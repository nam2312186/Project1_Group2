import os
import pandas as pd
from pymongo import MongoClient

# 1️⃣ Kết nối MongoDB Atlas
client = MongoClient("mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/")
db = client["spotify_project"]  # tên database

# 2️⃣ Đường dẫn đến thư mục chứa dữ liệu
base_dir = r"..\data1\data\data-top50"

# 3️⃣ Lặp qua từng thư mục quốc gia
for country in os.listdir(base_dir):
    country_path = os.path.join(base_dir, country)
    if os.path.isdir(country_path):
        print(f"\n🌍 Đang xử lý quốc gia: {country.upper()}")

        # Tìm file meta & audio trong thư mục đó
        meta_file = None
        audio_file = None
        for f in os.listdir(country_path):
            if "with-meta-clean" in f:
                meta_file = os.path.join(country_path, f)
            elif "with-audio" in f:
                audio_file = os.path.join(country_path, f)

        if not meta_file:
            print(f"⚠️ Không tìm thấy file meta cho {country}")
            continue

        # Đọc dữ liệu CSV
        df_meta = pd.read_csv(meta_file)
        if audio_file:
            df_audio = pd.read_csv(audio_file)
            # Gộp hai file theo track_id (hoặc spotify_id nếu có)
            key = "spotify_id" if "spotify_id" in df_meta.columns else "track_id"
            df_merged = pd.merge(df_meta, df_audio, on=key, how="left", suffixes=("", "_audio"))
        else:
            df_merged = df_meta

        # Thêm trường 'country' để biết nguồn dữ liệu
        df_merged["country"] = country.upper()

        # 4️⃣ Đưa dữ liệu vào MongoDB (mỗi nước 1 collection)
        collection_name = f"top50_{country.lower().replace('-', '_')}"
        collection = db[collection_name]
        collection.delete_many({})  # xóa dữ liệu cũ nếu có
        collection.insert_many(df_merged.to_dict("records"))
        print(f"✅ Đã upload {len(df_merged)} bản ghi vào collection '{collection_name}'")

print("\n🎉 Hoàn tất import dữ liệu tất cả quốc gia!")
