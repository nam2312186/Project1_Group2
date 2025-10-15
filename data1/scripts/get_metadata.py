import base64
import os
import json
import time
import pandas as pd
import glob
from requests import post, get
from dotenv import load_dotenv

# ================== CONFIG ==================
load_dotenv()
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

ACCESS_TOKEN = None
TOKEN_EXPIRE_AT = 0
CACHE_FILE = "track_cache.json"
PARENT_FOLDER = "data/data-top50"

# ================== CACHE ==================
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            print(" track_cache.json lỗi, reset cache")
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

track_cache = load_cache()

# ================== TOKEN ==================
def get_token():
    global ACCESS_TOKEN, TOKEN_EXPIRE_AT
    auth_string = client_id + ":" + client_secret
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": "Basic " + auth_base64,
               "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}

    resp = post(url, headers=headers, data=data)
    if resp.status_code != 200:
        print(" Lỗi token:", resp.status_code, resp.text)
        return None

    result = resp.json()
    ACCESS_TOKEN = result["access_token"]
    TOKEN_EXPIRE_AT = time.time() + (59 * 60)
    print(" Token mới (hết hạn sau 59 phút)")
    return ACCESS_TOKEN

def ensure_token():
    global ACCESS_TOKEN, TOKEN_EXPIRE_AT
    if not ACCESS_TOKEN or time.time() > TOKEN_EXPIRE_AT:
        return get_token()
    return ACCESS_TOKEN

# ================== SPOTIFY API ==================
def search_track(token, artist, song):
    """Tìm track_id + metadata từ song/artist"""
    artist = str(artist) if pd.notna(artist) else ""
    song = str(song) if pd.notna(song) else ""
    key = f"{artist.strip()} - {song.strip()}"

    # Check cache
    if key in track_cache:
        return track_cache[key]

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": f"track:{song} artist:{artist}", "type": "track", "limit": 1}

    resp = get(url, headers=headers, params=params)
    if resp.status_code == 401:  # token expired
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print(f" Search lỗi {song} - {artist}: {resp.status_code}")
        return None

    items = resp.json().get("tracks", {}).get("items", [])
    if not items:
        return None

    track_id = items[0]["id"]

    # Lấy metadata chi tiết
    metadata = get_track_metadata(token, track_id)
    if not metadata:
        return None

    # lưu vào cache
    track_cache[key] = metadata
    save_cache(track_cache)

    return metadata

def get_track_metadata(token, track_id):
    """Lấy metadata của một track (các field trong main.py)"""
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = get(url, headers=headers)
    if resp.status_code != 200:
        print(f" Metadata lỗi {track_id}: {resp.status_code}")
        return None

    data = resp.json()
    album_info = data.get("album") or {}

    return {
        "id": data.get("id"),
        "album_id": album_info.get("id"),
        "release_date_precision": album_info.get("release_date_precision"),
        "preview_url": data.get("preview_url"),
        "external_url": data.get("external_urls", {}).get("spotify"),
        "is_playable": data.get("is_playable"),
        "available_markets": data.get("available_markets"),
        "disc_number": data.get("disc_number"),
        "track_number": data.get("track_number"),
        "href": data.get("href"),
        "uri": data.get("uri"),
        "external_ids": data.get("external_ids"),
        "linked_from": data.get("linked_from"),
        "restrictions": data.get("restrictions"),
    }

# ================== MAIN ==================
def process_all_csv():
    subfolders = [os.path.join(PARENT_FOLDER, name) 
                  for name in os.listdir(PARENT_FOLDER) 
                  if os.path.isdir(os.path.join(PARENT_FOLDER, name))]

    print("📂 Tổng số folder:", len(subfolders))

    for folder in subfolders:
        csv_files = glob.glob(f"{folder}/*.csv")
        if not csv_files:
            continue
        csv_file = csv_files[0]
        print(f"\n Đang xử lý {csv_file}")

        df = pd.read_csv(csv_file)
        df["artist"] = df["artist"].fillna("").astype(str)
        df["song"] = df["song"].fillna("").astype(str)

        token = ensure_token()

        # Danh sách cột mới
        new_cols = {
            "track_id": [],
            "album_id": [],
            "release_date_precision": [],
            "preview_url": [],
            "external_url": [],
            "is_playable": [],
            "available_markets": [],
            "disc_number": [],
            "track_number": [],
            "href": [],
            "uri": [],
            "external_ids": [],
            "linked_from": [],
            "restrictions": []
        }

        for idx, row in df.iterrows():
            token = ensure_token()
            meta = search_track(token, row["artist"], row["song"])
            if meta:
                new_cols["track_id"].append(meta.get("id"))
                new_cols["album_id"].append(meta.get("album_id"))
                new_cols["release_date_precision"].append(meta.get("release_date_precision"))
                new_cols["preview_url"].append(meta.get("preview_url"))
                new_cols["external_url"].append(meta.get("external_url"))
                new_cols["is_playable"].append(meta.get("is_playable"))
                new_cols["available_markets"].append(",".join(meta.get("available_markets", [])))
                new_cols["disc_number"].append(meta.get("disc_number"))
                new_cols["track_number"].append(meta.get("track_number"))
                new_cols["href"].append(meta.get("href"))
                new_cols["uri"].append(meta.get("uri"))
                new_cols["external_ids"].append(str(meta.get("external_ids")))
                new_cols["linked_from"].append(str(meta.get("linked_from")))
                new_cols["restrictions"].append(str(meta.get("restrictions")))
            else:
                for k in new_cols.keys():
                    new_cols[k].append(None)

            print(f"{idx+1}. {row['song']} - {row['artist']} → {new_cols['track_id'][-1]}")

        # Gắn cột vào DataFrame
        for k, v in new_cols.items():
            df[k] = v

        out_file = csv_file.replace(".csv", "-with-meta.csv")
        df.to_csv(out_file, index=False)
        print(f" Đã lưu {out_file}")

if __name__ == "__main__":
    process_all_csv()
