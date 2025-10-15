import os
import base64
import requests
import pandas as pd
import glob
from dotenv import load_dotenv

# ================== CONFIG ==================
PARENT_FOLDER = "data/data-top50"

# Load biến môi trường
load_dotenv()
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

# ================== GET TOKEN ==================
def get_token():
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}

    res = requests.post(url, headers=headers, data=data)
    if res.status_code != 200:
        raise Exception(f"❌ Error get_token: {res.status_code} {res.text}")
    return res.json()["access_token"]

# ================== API CALLS ==================
def get_tracks(token, ids):
    """Lấy thông tin nhiều tracks"""
    url = "https://api.spotify.com/v1/tracks"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"ids": ",".join(ids)}
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("tracks", [])

def get_artists(token, ids):
    """Lấy thông tin nhiều artists"""
    url = "https://api.spotify.com/v1/artists"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"ids": ",".join(ids)}
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("artists", [])

# ================== MAIN LOGIC ==================
def add_genres_to_meta(meta_file):
    print(f"\n📂 Đang xử lý file: {meta_file}")
    df = pd.read_csv(meta_file, encoding="utf-8-sig")

    if "track_id" not in df.columns:
        print("❌ File không có cột track_id")
        return

    all_ids = df["track_id"].dropna().unique().tolist()
    if not all_ids:
        print("❌ Không có track_id nào để xử lý")
        return

    token = get_token()

    # Map track_id -> artist_ids
    track_artist_map = {}
    genres_map = {}

    print("🔎 Đang lấy artist_id cho tracks...")
    for i in range(0, len(all_ids), 50):
        tracks = get_tracks(token, all_ids[i:i+50])
        for t in tracks:
            if not t:
                continue
            tid = t["id"]
            artists = [a["id"] for a in t.get("artists", [])]
            if artists:
                track_artist_map[tid] = artists
                for aid in artists:
                    genres_map[aid] = None

    print("🎵 Đang lấy genres cho artists...")
    artist_ids = list(genres_map.keys())
    for i in range(0, len(artist_ids), 50):
        artists = get_artists(token, artist_ids[i:i+50])
        for a in artists:
            genres_map[a["id"]] = a.get("genres", [])
        print(f"  Batch artist {i//50+1} ok ({len(artists)} artists)")

    # Map genres trở lại file with-meta
    def get_track_genres(track_id):
        artist_ids = track_artist_map.get(track_id, [])
        if not artist_ids:
            return None
        first_artist = artist_ids[0]
        genres = genres_map.get(first_artist, [])
        return ", ".join(genres) if genres else None

    df["genres"] = df["track_id"].apply(get_track_genres)

    # Xuất file (ghi đè)
    df.to_csv(meta_file, index=False, encoding="utf-8-sig")
    print(f"✅ Đã cập nhật genres cho {len(df)} dòng trong {meta_file}")

def main():
    meta_files = glob.glob(f"{PARENT_FOLDER}/**/*-with-meta.csv", recursive=True)
    print(f"📊 Tìm thấy {len(meta_files)} file with-meta")

    for meta_file in meta_files:
        add_genres_to_meta(meta_file)

if __name__ == "__main__":
    main()
