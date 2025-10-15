import pandas as pd
from get_audio_feature import get_audio_features_batch

INPUT_FILE = "data/data-top50/null_track_clean_with_meta.csv"
OUTPUT_FILE = "data/data-top50/null_audio.csv"

def process_null_file():
    df = pd.read_csv(INPUT_FILE)

    features_cols = [
        "href", "acousticness", "danceability", "energy",
        "instrumentalness", "key", "liveness", "loudness",
        "mode", "speechiness", "tempo", "valence"
    ]

    results_data = {col: [] for col in ["track_id"] + features_cols}

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
                # Nếu không lấy được thì giữ None
                for col in features_cols:
                    results_data[col].append(None)

        print(f"✅ Batch {i//20+1} xử lý xong ({len(batch_ids)} tracks)")

    new_df = pd.DataFrame(results_data)
    new_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"💾 Đã lưu {OUTPUT_FILE} ({len(new_df)} dòng)")

if __name__ == "__main__":
    process_null_file()
