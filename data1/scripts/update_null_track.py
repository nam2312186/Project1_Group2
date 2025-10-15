import os
import base64
import json
import pandas as pd
from requests import get, post
from dotenv import load_dotenv
from get_audio_feature import get_audio_features_batch
# ================== CONFIG ==================
load_dotenv()
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

INPUT_FILE = "data/data-top50/null_track_clean.csv"
OUTPUT_FILE = "data/data-top50/null_track_clean_with_meta.csv"

# ================== TOKEN ==================
def get_token():
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": "Basic " + auth_base64,
               "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)
    if result.status_code != 200:
        print("❌ Error getting token:", result.status_code, result.text)
        return None
    return result.json()["access_token"]

# ================== SEARCH & METADATA ==================
def search_track_by_name(token, song_name, limit=1):
    """Tìm track_id chỉ dựa vào tên bài hát"""
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": f"track:{song_name}", "type": "track", "limit": limit}

    resp = get(url, headers=headers, params=params)
    if resp.status_code != 200:
        print(f"❌ Lỗi search {song_name}: {resp.status_code}")
        return None

    items = resp.json().get("tracks", {}).get("items", [])
    if not items:
        return None
    return items[0]  # trả về object track đầu tiên

def get_track_metadata(token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Metadata lỗi {track_id}: {resp.status_code}")
        return None
    return resp.json()

# ================== CSV SAFELY ==================
def read_csv_safely(path):
    encodings = ["utf-8-sig", "utf-8", "ISO-8859-1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"✅ Đọc file thành công với encoding: {enc}")
            return df
        except Exception as e:
            print(f"❌ Lỗi với encoding {enc}: {e}")
    raise ValueError("Không đọc được CSV với các encoding đã thử")

# ================== TEST 1 SONG ==================
def test_one_song(song):
    token = get_token()
    if not token:
        return

    track = search_track_by_name(token, song)
    if track:
        print("✅ Tìm thấy track:")
        print("Track ID:", track["id"])
        print("Name:", track["name"])
        print("Artist:", ", ".join([a["name"] for a in track["artists"]]))
        print("Album:", track["album"]["name"])
        print("Release date:", track["album"]["release_date"])
        print("External URL:", track["external_urls"]["spotify"])
    else:
        print("❌ Không tìm thấy bài hát")

# ================== UPDATE NULL TRACKS ==================
def update_null_tracks():
    df = read_csv_safely(INPUT_FILE)
    print(f"📂 Đang xử lý {len(df)} bài hát null track_id")

    token = get_token()

    meta_cols = [
        "track_id", "album_id", "release_date_precision", "preview_url",
        "external_url", "is_playable", "available_markets", "disc_number",
        "track_number", "href", "uri", "external_ids", "linked_from", "restrictions"
    ]
    for col in meta_cols:
        if col not in df.columns:
            df[col] = None

    for idx, row in df.iterrows():
        song = row["song"]
        track = search_track_by_name(token, song)
        if track:
            track_id = track["id"]
            meta = get_track_metadata(token, track_id)
            if meta:
                df.at[idx, "track_id"] = track_id
                df.at[idx, "album_id"] = meta.get("album", {}).get("id")
                df.at[idx, "release_date_precision"] = meta.get("album", {}).get("release_date")
                df.at[idx, "preview_url"] = meta.get("preview_url")
                df.at[idx, "external_url"] = meta.get("external_urls", {}).get("spotify")
                df.at[idx, "is_playable"] = meta.get("is_playable")
                df.at[idx, "available_markets"] = ",".join(meta.get("available_markets", []))
                df.at[idx, "disc_number"] = meta.get("disc_number")
                df.at[idx, "track_number"] = meta.get("track_number")
                df.at[idx, "href"] = meta.get("href")
                df.at[idx, "uri"] = meta.get("uri")
                df.at[idx, "external_ids"] = str(meta.get("external_ids"))
                df.at[idx, "linked_from"] = str(meta.get("linked_from"))
                df.at[idx, "restrictions"] = str(meta.get("restrictions"))
                print(f"{idx+1}. ✅ {song} → {track_id}")
            else:
                print(f"{idx+1}. ⚠️ {song} tìm thấy id nhưng không lấy được metadata")
        else:
            print(f"{idx+1}. ❌ Không tìm thấy track cho {song}")

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Đã lưu kết quả cập nhật vào {OUTPUT_FILE}")

# ================== MAIN ==================
if __name__ == "__main__":


    # Cập nhật file null_track_clean.csv
    update_null_tracks()
