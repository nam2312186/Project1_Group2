# import os
# import json
# import time
# import pandas as pd
# import glob
# import requests

# CACHE_FILE = "audio_cache.json"
# PARENT_FOLDER = "data/data-top50"
# BASE_URL = "https://api.reccobeats.com/v1"

# # ========== CACHE ==========
# def load_cache():
#     if os.path.exists(CACHE_FILE):
#         try:
#             with open(CACHE_FILE, "r", encoding="utf-8") as f:
#                 return json.load(f)
#         except json.JSONDecodeError:
#             print("⚠️ Cache lỗi, reset cache")
#             return {}
#     return {}

# def save_cache(cache):
#     with open(CACHE_FILE, "w", encoding="utf-8") as f:
#         json.dump(cache, f, indent=2, ensure_ascii=False)

# track_cache = load_cache()

# # ========== RECCOBEATS API (batch 20 + retry) ==========
# def get_audio_features_batch(track_ids, retries=3):
#     """Lấy audio features cho tối đa 20 track_id, có retry nếu bị 429"""
#     uncached = [tid for tid in track_ids if tid and tid not in track_cache]
#     if not uncached:
#         return {tid: track_cache.get(tid) for tid in track_ids if tid}

#     ids_str = ",".join(uncached)
#     url = f"{BASE_URL}/audio-features?ids={ids_str}"

#     for attempt in range(retries):
#         resp = requests.get(url)
#         if resp.status_code == 200:
#             data = resp.json()
#             features_list = data.get("content", [])
#             for feat in features_list:
#                 tid = feat.get("href", "").split("/")[-1]
#                 if tid:
#                     clean_feat = {k: v for k, v in feat.items() if k != "id"}
#                     track_cache[tid] = clean_feat
#             save_cache(track_cache)
#             break
#         elif resp.status_code == 429:
#             wait_time = 5 * (attempt + 1)
#             print(f"⏳ Rate limited (429), đợi {wait_time}s rồi thử lại...")
#             time.sleep(wait_time)
#         elif resp.status_code in [500, 502, 503]:
#             wait_time = 5 * (attempt + 1)
#             print(f"⚠️ Server error {resp.status_code}, đợi {wait_time}s rồi thử lại...")
#             time.sleep(wait_time)
#         else:
#             print(f"❌ Error {resp.status_code} for batch {uncached[:3]}...")
#             break


#     return {tid: track_cache.get(tid) for tid in track_ids if tid}

# # ========== MAIN ==========
# def process_all_csv():
#     csv_files = glob.glob(f"{PARENT_FOLDER}/**/*-with-meta.csv", recursive=True)
#     print("📂 Tổng số file cần xử lý:", len(csv_files))

#     for csv_file in csv_files:
#         print(f"\n➡️ Đang xử lý {csv_file}")
#         df = pd.read_csv(csv_file)

#         features_cols = [
#             "href", "acousticness", "danceability", "energy",
#             "instrumentalness", "key", "liveness", "loudness",
#             "mode", "speechiness", "tempo", "valence"
#         ]

#         results_data = {col: [] for col in ["track_id"] + features_cols}

#         track_ids = df["track_id"].dropna().astype(str).tolist()
#         for i in range(0, len(track_ids), 20):
#             batch_ids = track_ids[i:i+20]
#             results = get_audio_features_batch(batch_ids)

#             for tid in batch_ids:
#                 feat = results.get(tid)
#                 if feat:
#                     results_data["track_id"].append(tid)
#                     for col in features_cols:
#                         results_data[col].append(feat.get(col))
#                 # Nếu không có feat → bỏ qua (không ghi dòng None)

#             print(f"✅ Batch {i//20+1} xử lý xong ({len(batch_ids)} tracks)")

#         # Tạo DataFrame mới chỉ có track_id + audio features
#         new_df = pd.DataFrame(results_data)
#         out_file = csv_file.replace("-with-meta.csv", "-with-audio.csv")
#         new_df.to_csv(out_file, index=False)
#         print(f"💾 Đã lưu {out_file} ({len(new_df)} dòng)")

# if __name__ == "__main__":
#     process_all_csv()















import os
import json
import time
import pandas as pd
import glob
import requests

CACHE_FILE = "audio_cache.json"
PARENT_FOLDER = "data/data-top50"
BASE_URL = "https://api.reccobeats.com/v1"

# ================= CACHE =================
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Cache lỗi, reset cache")
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

track_cache = load_cache()

# ================= API CALL =================
def get_audio_features_batch(track_ids, retries=3):
    """
    Lấy audio features cho tối đa 20 track_id từ ReccoBeats API.
    Có retry khi gặp lỗi 429 (rate limit) hoặc 500/502/503 (server error).
    """
    uncached = [tid for tid in track_ids if tid and tid not in track_cache]
    if not uncached:
        return {tid: track_cache.get(tid) for tid in track_ids if tid}

    ids_str = ",".join(uncached)
    url = f"{BASE_URL}/audio-features?ids={ids_str}"

    for attempt in range(retries):
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            features_list = data.get("content", [])
            for feat in features_list:
                tid = feat.get("href", "").split("/")[-1]
                if tid:
                    # bỏ id nội bộ, giữ lại các field khác
                    clean_feat = {k: v for k, v in feat.items() if k != "id"}
                    track_cache[tid] = clean_feat
            save_cache(track_cache)
            break
        elif resp.status_code == 429:
            wait_time = 5 * (attempt + 1)
            print(f"⏳ Rate limited (429), đợi {wait_time}s rồi thử lại...")
            time.sleep(wait_time)
        elif resp.status_code in [500, 502, 503]:
            wait_time = 5 * (attempt + 1)
            print(f"⚠️ Server error {resp.status_code}, đợi {wait_time}s rồi thử lại...")
            time.sleep(wait_time)
        else:
            print(f"❌ Error {resp.status_code} for batch {uncached[:3]}...")
            break
    else:
    # chỉ chạy nếu vòng for kết thúc mà không break (tức là thất bại sau 3 lần)
        print(f"🚨 Batch {uncached[:3]}... thất bại sau {retries} lần thử, ghi None")

    return {tid: track_cache.get(tid) for tid in track_ids if tid}

# ================= MAIN =================
def process_all_csv():
    csv_files = glob.glob(f"{PARENT_FOLDER}/**/*-with-meta.csv", recursive=True)
    print("📂 Tổng số file cần xử lý:", len(csv_files))

    for csv_file in csv_files:
        print(f"\n➡️ Đang xử lý {csv_file}")
        df = pd.read_csv(csv_file)

        features_cols = [
            "href", "acousticness", "danceability", "energy",
            "instrumentalness", "key", "liveness", "loudness",
            "mode", "speechiness", "tempo", "valence"
        ]

        results_data = {col: [] for col in ["track_id"] + features_cols}

        # bỏ null/rỗng track_id
        track_ids = df["track_id"].dropna().astype(str).tolist()
        track_ids = [tid for tid in track_ids if tid.strip() != ""]

        for i in range(0, len(track_ids), 20):
            batch_ids = track_ids[i:i+20]
            results = get_audio_features_batch(batch_ids)

            for tid in batch_ids:
                feat = results.get(tid)
                results_data["track_id"].append(tid)
                if feat:
                    for col in features_cols:
                        results_data[col].append(feat.get(col))
                else:
                    # giữ dòng nhưng điền None cho audio features
                    for col in features_cols:
                        results_data[col].append(None)

            print(f"✅ Batch {i//20+1} xử lý xong ({len(batch_ids)} tracks)")

        # Tạo DataFrame mới chỉ có track_id + audio features
        new_df = pd.DataFrame(results_data)
        out_file = csv_file.replace("-with-meta.csv", "-with-audio.csv")
        new_df.to_csv(out_file, index=False)
        print(f"💾 Đã lưu {out_file} ({len(new_df)} dòng)")

if __name__ == "__main__":
    process_all_csv()

