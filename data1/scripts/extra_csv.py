import pandas as pd
import os

# Đọc file CSV
country = "usa"
typ = ["meta", "audio", "meta-clean"]
i = 2# df = pd.read_csv("data/data-top50/{country}/spotify-streaming-top-50-{country}-with-audio.csv")
file_path = os.path.join("data", "data-top50", country, f"spotify-streaming-top-50-{country}-with-{typ[i]}.csv")

try:
    df = pd.read_csv(file_path)
    print(f"✅ Đã đọc file thành công từ: {file_path}")
    
    # ...existing code...
    
except FileNotFoundError:
    print(f"❌ Không tìm thấy file trong thư mục {country}: {file_path}")
    print("Cấu trúc thư mục hiện tại:")
    print("data/")
    print("└── data-top50/")
    print(f"    └── {country}/")
    print(f"        └── spotify-streaming-top-50-{country}-with-audio.csv")
    exit(1)
except Exception as e:
    print(f"❌ Lỗi khi đọc file: {str(e)}")
    exit(1)
# Giả sử bạn muốn kiểm tra cột "medal"
col = "track_id"

# 1. Thống kê số giá trị null (NaN) trong cột
null_count = df[col].isnull().sum()

# 2. Thống kê số giá trị rỗng (chuỗi "")
empty_count = (df[col] == "").sum()

# 3. Tổng số dòng
total_rows = len(df)

# 4. Tỷ lệ phần trăm giá trị null/rỗng
null_pct = null_count / total_rows * 100
empty_pct = empty_count / total_rows * 100

print(f"Tổng số dòng: {total_rows}")
print(f"Số giá trị null: {null_count} ({null_pct:.2f}%)")
print(f"Số giá trị rỗng: {empty_count} ({empty_pct:.2f}%)")

# 5. Thống kê phân bố giá trị (bỏ qua NaN)
print("\nPhân bố giá trị khác nhau trong cột:")
print(df[col].value_counts(dropna=False))

# 6. Hiển thị các cột
cols = df.columns.tolist()
print("\nCác cột trong DataFrame:")
print(cols)

  
# null_rows = df[df[col].isnull()]
# print(null_rows[["song", "artist", col]])