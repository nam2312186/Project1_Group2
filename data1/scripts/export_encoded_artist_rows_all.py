import pandas as pd
import os

def export_encoded_song_or_artist_rows(csv_path, song_col='song', artist_col='artist', trackid_col='track_id', output_path='encoded_song_or_artist_rows.csv'):
    df = pd.read_csv(csv_path)
    
    # Lọc các dòng mà song HOẶC artist bị mã hóa (không phải ASCII)
    def is_encoded(text):
        return not str(text).isascii()  # True nếu không phải ASCII (bị mã hóa)
    
    mask_song = df[song_col].astype(str).apply(is_encoded)
    mask_artist = df[artist_col].astype(str).apply(is_encoded)
    encoded_df = df[mask_song | mask_artist]  # OR: song HOẶC artist bị mã hóa
    
    # Loại bỏ trùng lặp theo track_id, giữ lại dòng đầu tiên cho mỗi track_id
    encoded_df = encoded_df.drop_duplicates(subset=[trackid_col])
    
    encoded_df.to_csv(output_path, index=False, encoding='utf-8-sig')  # Thêm encoding để tránh issue khi lưu
    print(f'Đã xuất {encoded_df.shape[0]} dòng bị mã hóa (song HOẶC artist, không trùng track_id) ra file: {output_path}')

if __name__ == '__main__':
    # Danh sách các nước
    countries = [
        'argentina', 'france', 'italy', 'japan', 'mexico',
        'south-korea', 'spain', 'uk', 'usa', 'world'
    ]
    base_dir = 'data/data-top50'
    
    for country in countries:
        input_path = os.path.abspath(os.path.join(base_dir, country, f'spotify-streaming-top-50-{country}-with-meta-clean.csv'))
        output_path = f'encoded_song_or_artist_rows_{country}.csv'
        print(f"Checking: {input_path}")
        if os.path.isfile(input_path):
            export_encoded_song_or_artist_rows(
                input_path, 
                song_col='song', 
                artist_col='artist', 
                trackid_col='track_id', 
                output_path=os.path.abspath(os.path.join(base_dir, country, output_path))
            )
        else:
            print(f'File not found: {input_path}')