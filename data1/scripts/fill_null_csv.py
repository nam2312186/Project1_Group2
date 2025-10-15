import pandas as pd
import glob
import os

PARENT_FOLDER = "data/data-top50"
OUT_PATH = os.path.join(PARENT_FOLDER, "null_track_clean_with_meta.csv")

all_null_rows = []

# Duyệt qua tất cả các file with-meta.csv
csv_files = glob.glob(f"{PARENT_FOLDER}/**/*-with-meta.csv", recursive=True)
print("📂 Tổng số file cần xử lý:", len(csv_files))

for csv_file in csv_files:
    df = pd.read_csv(csv_file, encoding="ISO-8859-1")
    # Lọc track_id null
    null_rows = df[df["track_id"].isna()]
    if len(null_rows) > 0:
        print(f"➡️ {csv_file}: {len(null_rows)} hàng null")
        # Loại trùng theo (song, artist)
        null_rows = null_rows.drop_duplicates(subset=["song", "artist"])
        # Bỏ cột position, date nếu có
        cols_to_drop = [c for c in ["position", "date"] if c in null_rows.columns]
        null_rows = null_rows.drop(columns=cols_to_drop)
        all_null_rows.append(null_rows)

# Ghép tất cả các hàng null từ nhiều file
if all_null_rows:
    final_df = pd.concat(all_null_rows, ignore_index=True)
    # Loại trùng lần cuối cùng (phòng trường hợp cùng bài hát ở nhiều quốc gia)
    final_df = final_df.drop_duplicates(subset=["song", "artist"])
    # Xuất ra CSV
    final_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"✅ Đã xuất {len(final_df)} hàng vào file: {OUT_PATH}")
else:
    print("Không tìm thấy track_id null trong các file.")
