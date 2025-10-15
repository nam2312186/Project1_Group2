import pandas as pd
import glob
import os

PARENT_FOLDER = "data/data-top50"

# Input: file đã cập nhật metadata/audio
NULL_META_FILE = os.path.join(PARENT_FOLDER, "null_track_clean_with_meta.csv")
NULL_AUDIO_FILE = os.path.join(PARENT_FOLDER, "null_audio.csv")

def update_with_meta():
    if not os.path.exists(NULL_META_FILE):
        print("❌ Không tìm thấy null_track_clean_with_meta.csv")
        return

    null_df = pd.read_csv(NULL_META_FILE, encoding="utf-8-sig")

    # Cột để cập nhật (trừ song để dùng làm key join)
    meta_cols = [c for c in null_df.columns if c != "song"]

    csv_files = glob.glob(f"{PARENT_FOLDER}/**/*-with-meta.csv", recursive=True)
    print("📂 Tổng số file with-meta cần xử lý:", len(csv_files))

    for csv_file in csv_files:
        df = pd.read_csv(csv_file, encoding="ISO-8859-1")
        if "song" not in df.columns:
            continue

        # Merge theo cột song
        updated = df.merge(null_df, on="song", how="left", suffixes=("", "_new"))

        # Update cột nếu null và có giá trị mới
        for col in meta_cols:
            if col in df.columns:
                updated[col] = updated[col].combine_first(updated[f"{col}_new"])

        # Xóa các cột *_new
        updated = updated[[c for c in updated.columns if not c.endswith("_new")]]

        updated.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"✅ Đã cập nhật {csv_file}")

def update_with_audio():
    if not os.path.exists(NULL_AUDIO_FILE):
        print("❌ Không tìm thấy null_audio.csv")
        return

    null_df = pd.read_csv(NULL_AUDIO_FILE, encoding="utf-8-sig")

    audio_cols = [c for c in null_df.columns if c != "track_id"]

    csv_files = glob.glob(f"{PARENT_FOLDER}/**/*-with-audio.csv", recursive=True)
    print("📂 Tổng số file with-audio cần xử lý:", len(csv_files))

    for csv_file in csv_files:
        df = pd.read_csv(csv_file, encoding="ISO-8859-1")
        if "track_id" not in df.columns:
            continue

        # Merge theo track_id
        updated = df.merge(null_df, on="track_id", how="left", suffixes=("", "_new"))

        for col in audio_cols:
            if col in df.columns:
                updated[col] = updated[col].combine_first(updated[f"{col}_new"])

        updated = updated[[c for c in updated.columns if not c.endswith("_new")]]

        updated.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"✅ Đã cập nhật {csv_file}")

if __name__ == "__main__":
    update_with_meta()
    update_with_audio()
