from pymongo import MongoClient
import pandas as pd
import os

# 1️⃣ Kết nối MongoDB Atlas
uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["spotify_project"]  # tên database
collection = db["billboard_features_2025"]  # tên collection

# 2️⃣ Đường dẫn tới file CSV
csv_path = r"D:\Daihoc\Nam3\ĐAHKTDL\Code\Project_Spotify\analysis_data_2025_US\Output\step3\billboard_features.csv"

# 3️⃣ Đọc file CSV
if not os.path.exists(csv_path):
    raise FileNotFoundError("Không tìm thấy file CSV ở đường dẫn: " + csv_path)

df = pd.read_csv(csv_path)
print(f"📄 Đã đọc {len(df)} dòng dữ liệu từ CSV.")

# 4️⃣ Ghi dữ liệu lên MongoDB
data = df.to_dict(orient="records")
if data:
    collection.insert_many(data)
    print(f"✅ Đã import {len(data)} dòng dữ liệu vào MongoDB Atlas!")
else:
    print("⚠️ File CSV trống, không có dữ liệu để import.")
