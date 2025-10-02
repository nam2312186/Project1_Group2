import billboard
import pandas as pd
import numpy as np
import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import os

# ====== Spotify config ======
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="ddfbc5255c2549b2869adbfe81eeb7fb",
    client_secret="bb680c2eae494432902151ac3e9a03a3",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-email user-read-private",
    open_browser=True
))

# ====== ReccoBeats config ======
API_URL = "https://api.reccobeats.com/v1/audio-features"
BATCH_SIZE = 30

# ====== Nơi lưu trữ dữ liệu ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "Output", "step0")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_sundays(year: int):
    """Sinh list ngày Chủ Nhật trong 1 năm (Billboard chart tuần)."""
    d = datetime.date(year, 1, 5)  # Chủ Nhật đầu tiên của 2025
    while d.year == year:
        yield d.strftime("%Y-%m-%d")
        d += datetime.timedelta(days=7)


def run_step0(year=2025):
    """Pipeline Step 0: Thu thập Billboard + enrich từ Spotify/ReccoBeats."""

    # ====== STEP 1: Lấy Billboard Hot 100 ======
    weeks = list(get_sundays(year))
    rows = []
    for week in weeks:
        try:
            chart = billboard.ChartData('hot-100', date=week)
            for entry in chart:
                rows.append({
                    "week": week,
                    "rank": entry.rank,
                    "title": entry.title,
                    "artist": entry.artist
                })
            print(f" Lấy xong tuần {week}")
        except Exception as e:
            print(f" Lỗi tuần {week}: {e}")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "billboard_raw.csv"),
              index=False, encoding="utf-8-sig")
    print(" Xuất thành công STEP 1 → billboard_raw.csv")

    # ====== STEP 2: Tìm Spotify track ID ======
    ids = []
    for idx, row in df.iterrows():
        q = f"{row['title']} {row['artist']}"
        try:
            result = sp.search(q=q, type="track", limit=1)
            items = result["tracks"]["items"]
            spotify_id = items[0]["id"] if items else None
            print(f" {q} → {spotify_id}")
        except Exception as e:
            print(f" Lỗi search {q}: {e}")
            spotify_id = None
        ids.append(spotify_id)
        time.sleep(0.2)

    df["spotify_id"] = ids
    df.to_csv(os.path.join(OUTPUT_DIR, "billboard_with_id.csv"),
              index=False, encoding="utf-8-sig")
    print(" Xuất thành công STEP 2 → billboard_with_id.csv")

    # ====== STEP 3: Lấy audio features từ ReccoBeats ======
    features_map = {}
    valid_ids = df["spotify_id"].dropna().unique().tolist()

    for i in range(0, len(valid_ids), BATCH_SIZE):
        batch = valid_ids[i:i+BATCH_SIZE]
        params = {"ids": ",".join(batch)}
        headers = {"Accept": "application/json"}
        r = requests.get(API_URL, params=params, headers=headers)

        if r.status_code == 200:
            data = r.json().get("content", [])
            for item in data:
                href = item.get("href", "")
                if "track/" in href:
                    spotify_id = href.split("track/")[-1]
                    features_map[spotify_id] = item
            print(f" Lấy features cho batch {i//BATCH_SIZE+1}")
        else:
            print(f" Batch {i//BATCH_SIZE+1} lỗi: {r.status_code}")
        time.sleep(0.2)

    feature_cols = [
        "danceability", "energy", "tempo", "valence",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "loudness", "key", "mode"
    ]
    for col in feature_cols:
        df[col] = df["spotify_id"].map(
            lambda x: features_map.get(x, {}).get(col))

    df.to_csv(os.path.join(OUTPUT_DIR, "billboard_with_features.csv"),
              index=False, encoding="utf-8-sig")
    print(" Xuất thành công STEP 3 → billboard_with_features.csv")

    # ====== STEP 4: Lấy genres từ Spotify ======
    genres_map = {}
    for spotify_id in valid_ids:
        try:
            track = sp.track(spotify_id)
            artists = track["artists"]
            if artists:
                main_artist_id = artists[0]["id"]
                artist_info = sp.artist(main_artist_id)
                genres = artist_info.get("genres", [])
                genres_map[spotify_id] = genres[0] if genres else np.nan
            else:
                genres_map[spotify_id] = np.nan
            print(f"🎶 {track['name']} → {genres_map[spotify_id]}")
        except Exception as e:
            print(f"Lỗi lấy genres cho {spotify_id}: {e}")
            genres_map[spotify_id] = np.nan
        time.sleep(0.2)

    df["genre"] = df["spotify_id"].map(lambda x: genres_map.get(x, np.nan))

    df.to_csv(os.path.join(OUTPUT_DIR, "billboard_final.csv"),
              index=False, encoding="utf-8-sig")
    print(" Xuất thành công STEP 4 → billboard_final.csv")

    print(" HOÀN TẤT STEP 0: DATA COLLECTION & ENRICHMENT")

    return df
