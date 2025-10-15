import pandas as pd
import glob
import os

PARENT_FOLDER = "data/data-top50"
NULL_AUDIO_FILE = os.path.join(PARENT_FOLDER, "null_audio.csv")

def update_audio_files():
    # Load null_audio
    null_df = pd.read_csv(NULL_AUDIO_FILE, encoding="utf-8-sig")

    # Lặp qua từng folder con
    folders = [f for f in glob.glob(f"{PARENT_FOLDER}/*") if os.path.isdir(f)]
    for folder in folders:
        meta_files = glob.glob(f"{folder}/*-with-meta.csv")
        audio_files = glob.glob(f"{folder}/*-with-audio.csv")

        if not meta_files or not audio_files:
            continue

        meta_file = meta_files[0]
        audio_file = audio_files[0]

        df_meta = pd.read_csv(meta_file, encoding="utf-8-sig")
        df_audio = pd.read_csv(audio_file, encoding="utf-8-sig")

        # Lấy danh sách track_id trùng nhau
        common_ids = set(df_meta["track_id"]).intersection(set(null_df["track_id"]))
        if not common_ids:
            print(f"❌ {folder}: Không có track_id trùng nhau")
            continue

        # Lọc các hàng null_audio có track_id trùng
        rows_to_add = null_df[null_df["track_id"].isin(common_ids)]

        # Merge vào with-audio (ưu tiên giữ dữ liệu cũ, chỉ fill nếu thiếu)
        updated = df_audio.merge(rows_to_add, on="track_id", how="outer", suffixes=("", "_new"))

        # Nếu có cột trùng → fill dữ liệu còn thiếu
        for col in rows_to_add.columns:
            if col != "track_id" and col in updated.columns:
                updated[col] = updated[col].combine_first(updated[f"{col}_new"])

        # Xóa cột thừa *_new
        updated = updated[[c for c in updated.columns if not c.endswith("_new")]]

        # Xuất file
        updated.to_csv(audio_file, index=False, encoding="utf-8-sig")
        print(f"✅ Đã cập nhật {audio_file} (thêm {len(rows_to_add)} hàng từ null_audio)")

if __name__ == "__main__":
    update_audio_files()
