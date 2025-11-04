import pandas as pd
from pymongo import MongoClient

# 1️⃣ Kết nối MongoDB Atlas
client = MongoClient("mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/")
db = client["spotify_project"]

# 2️⃣ Đọc hai file CSV
cleaned_file = "..\data2\Cleaned_Spotify_2024_GLobal_Streaming_Data-with-id.csv"
info_file = "..\data2\Albums_Info_from_ReccoBeats_2.csv"

df_clean = pd.read_csv(cleaned_file)
df_info = pd.read_csv(info_file)

# 3️⃣ Chuẩn hóa tên album để khớp join
df_clean["Album"] = df_clean["Album"].astype(str).str.strip().str.lower()
df_info["name"] = df_info["name"].astype(str).str.strip().str.lower()

# 4️⃣ Join hai bảng: Cleaned (Album) ↔ Info (name)
merged = df_clean.merge(df_info, left_on="Album", right_on="name", how="left", suffixes=("", "_info"))

print(f"🔗 Đã ghép được {len(merged)} dòng dữ liệu sau khi join!")

# 5️⃣ Upload lên MongoDB (1 collection duy nhất)
collection = db["album_stats_global"]
collection.delete_many({})  # Xóa dữ liệu cũ (nếu có)
collection.insert_many(merged.to_dict(orient="records"))

print(f"✅ Đã import {len(merged)} document vào collection 'album_stats_global'")
