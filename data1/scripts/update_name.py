import pandas as pd
import os

# Danh sách quốc gia
countries = [
    'argentina', 'france', 'italy', 'japan', 'mexico',
    'south-korea', 'spain', 'uk', 'usa', 'world'
]

# Hàm xử lý cho một quốc gia
def process_country(country):
    base_dir = 'data/data-top50'
    fixed_filename = os.path.abspath(os.path.join(base_dir, country,f'spotify_streaming_top_50_fixed_{country}.csv'))
    clean_filename = os.path.abspath(os.path.join(base_dir, country, f'spotify-streaming-top-50-{country}-with-meta-clean.csv'))

    
    # Kiểm tra file clean tồn tại
    if not os.path.exists(clean_filename):
        print(f"[{country.upper()}] Bỏ qua: Không tìm thấy {clean_filename}")
        return
    
    # Đọc file fixed nếu tồn tại
    if not os.path.exists(fixed_filename):
        print(f"[{country.upper()}] Bỏ qua: Không tìm thấy {fixed_filename} (giữ nguyên file gốc)")
        return
    
    fixed_df = pd.read_csv(fixed_filename, encoding="utf-8-sig")
    mapping = {}
    for _, row in fixed_df.iterrows():
        track_id = row['track_id']
        if track_id not in mapping:  # Tránh duplicate
            mapping[track_id] = (row['song'], row['artist'])
    
    print(f"[{country.upper()}] Tìm thấy {len(mapping)} track_id trong file fixed.")
    
    if len(mapping) == 0:
        print(f"[{country.upper()}] Không có mapping, giữ nguyên file gốc.")
        return
    
    # Đọc file clean
    clean_df = pd.read_csv(clean_filename, encoding="utf-8-sig")
    
    # Thay thế song và artist
    fixed_count = 0
    for idx, row in clean_df.iterrows():
        track_id = row['track_id']
        if track_id in mapping:
            clean_df.at[idx, 'song'] = mapping[track_id][0]
            clean_df.at[idx, 'artist'] = mapping[track_id][1]
            fixed_count += 1
    
    # Lưu file updated
    clean_df.to_csv(clean_filename, index=False, encoding='utf-8-sig')
    print(f"[{country.upper()}] Đã thay thế {fixed_count} rows. Lưu vào {clean_filename}")

# Chạy cho tất cả quốc gia
print("Bắt đầu xử lý tất cả file...")
for country in countries:
    process_country(country)
print("Hoàn tất!")