import pandas as pd
import os
import glob
#--------------------------------------------------------tạo file meta-clean--------------------------
# Các cột cần giữ lại cho with-meta
META_COLUMNS = [
    "date", "position", "song", "artist", "track_id",
    "popularity", "duration_ms", "is_explicit",
    "album_id", "release_date", "genres"
]

def preprocess_meta(file_path, out_path):
    """Tiền xử lý with-meta.csv"""
    df = pd.read_csv(file_path)

    keep_cols = [col for col in META_COLUMNS if col in df.columns]
    df_clean = df[keep_cols]

    if "release_date" in df_clean.columns:
        df_clean["release_date"] = pd.to_datetime(
            df_clean["release_date"], errors="coerce"
        )

    if "genres" in df_clean.columns:
        df_clean["genres"] = (
            df_clean["genres"]
            .fillna("unknown")
            .str.lower()
        )

    df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f" Meta cleaned: {out_path} (shape={df_clean.shape})")
    return df_clean


def preprocess_all(parent_folder):
    """Chạy tiền xử lý with-meta cho tất cả subfolder"""
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print(" Tổng số folder:", len(subfolders))
    for sub in subfolders:
        print(f"\n Đang xử lý folder: {sub}")

        # Tìm file with-meta trong folder
        meta_files = glob.glob(f"{sub}/*with-meta*.csv")
        if meta_files:
            meta_file = meta_files[0]
            out_meta = meta_file.replace(".csv", "-clean.csv")
            preprocess_meta(meta_file, out_meta)
        else:
            print(f" Không tìm thấy with-meta.csv trong {sub}")

#--------------------------------------------------------TIỀN XỬ LÝ---------------------------

    #--------------------------------------------------------XEM THIẾU DỮ LIỆU---------------------------
def view_missing_meta(parent_folder, n=10):
    """
    Duyệt tất cả subfolder trong parent_folder,
    tìm file *with-meta-clean.csv trong mỗi subfolder,
    và in ra thông tin missing data.
    """
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print(" Tổng số folder:", len(subfolders))
    for sub in subfolders:
        meta_files = glob.glob(os.path.join(sub, "*with-meta-clean.csv"))
        if meta_files:
            file_path = meta_files[0]
            df = pd.read_csv(file_path)

            print(f"\n File: {file_path}")
            print("Shape:", df.shape)
            print("Số giá trị thiếu theo cột:\n", df.isna().sum())
            print(f"\n{n} dòng đầu:\n", df.head(n))
            print("-"*60)
        else:
            print(f" Không tìm thấy csv trong {sub}")

    #----------------------------------------------------------XỬ LÝ-----------------------------
def handle_missing_meta(file_path):
    """
    Xử lý thiếu dữ liệu trong with-meta.csv và ghi đè trực tiếp:
    1. track_id null -> 'unknown_track'
    2. album_id null -> 'unknown_album'
    3. release_date:
       - Nếu chỉ có năm -> dùng '01-01-{year}' dựa trên min(date)
       - Nếu NaN -> cũng dùng như trên
       - (chưa cần chuẩn hóa datetime)
    4. genres null -> 'unknown'
    """
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 1. track_id
    df["track_id"] = df["track_id"].fillna("unknown_track")

    # 2. album_id
    if "album_id" in df.columns:
        df["album_id"] = df["album_id"].fillna("unknown_album")

    # 3. release_date
    if "release_date" in df.columns and "date" in df.columns:
        min_date = df["date"].min()  # yyyy-mm-dd
        min_year = str(min_date).split("-")[0]
        fallback_date = f"{min_year}-01-01"

        def fix_release_date(x):
            if pd.isna(x):
                return fallback_date
            x = str(x)
            if len(x) == 4 and x.isdigit():  # chỉ có năm
                return f"{x}-01-01"
            return x

        df["release_date"] = df["release_date"].apply(fix_release_date)

    # 4. genres
    if "genres" in df.columns:
        df["genres"] = df["genres"].fillna("unknown")

    # 5. Ghi đè chính file gốc
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f" Đã xử lý missing và ghi đè: {file_path} (shape={df.shape})")

    return df


def handle_missing_meta_in_all(parent_folder):
    """
    Duyệt qua tất cả subfolder trong parent_folder,
    tìm file *with-meta-clean.csv và xử lý thiếu dữ liệu,
    ghi đè trực tiếp vào chính file đó.
    """
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print("Tổng số folder:", len(subfolders))
    for sub in subfolders:
        meta_files = glob.glob(os.path.join(sub, "*with-meta-clean.csv"))
        if meta_files:
            meta_file = meta_files[0]
            handle_missing_meta(meta_file)
        else:
            print(f" Không tìm thấy with-meta-clean.csv trong {sub}")



#---------------------------------------------------------CHUẨN HÓA---------------------------
def standardize_meta(file_path):
    """
    Chuẩn hóa dữ liệu trong with-meta-clean.csv (theo yêu cầu mới):
    1. release_date và date -> datetime (YYYY-MM-DD)
    2. genres -> giữ nguyên format, lấy genre đầu tiên nếu nhiều
    3. is_explicit -> 0/1
    4. duration_ms -> giữ nguyên
    5. song, artist -> giữ nguyên
    """
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 1. Chuẩn hóa release_date và date
    for col in ["release_date", "date"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].apply(
                lambda x: f"{x}-01-01" if len(x) == 4 and x.isdigit() else x
            )
            df[col] = pd.to_datetime(df[col], errors="coerce").fillna(pd.to_datetime("1900-01-01"))

    # 2. Chuẩn hóa genres (giữ nguyên format, chỉ lấy genre đầu tiên)
    if "genres" in df.columns:
        df["main_genre"] = df["genres"].apply(
            lambda x: str(x).split(",")[0].strip() if pd.notna(x) else "unknown"
        )

    # 3. Chuẩn hóa is_explicit
    if "is_explicit" in df.columns:
        df["is_explicit"] = df["is_explicit"].astype(int)

    # 4. duration_ms giữ nguyên (không chia)

    # 5. song, artist giữ nguyên (không chuẩn hóa)

    # Xuất lại file (ghi đè)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f" Đã chuẩn hóa dữ liệu: {file_path} (shape={df.shape})")

    return df


def standardize_meta_in_all(parent_folder):
    """
    Duyệt qua tất cả subfolder trong parent_folder,
    chuẩn hóa file *with-meta-clean.csv trong từng folder.
    """
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print(" Tổng số folder:", len(subfolders))
    for sub in subfolders:
        meta_files = glob.glob(os.path.join(sub, "*with-meta-clean.csv"))
        if meta_files:
            meta_file = meta_files[0]
            standardize_meta(meta_file)
        else:
            print(f" Không tìm thấy csv trong {sub}")

if __name__ == "__main__":
    parent_folder = os.path.join("..", "data", "data-top50")  #  thay đường dẫn gốc của bạn
    # preprocess_all(parent_folder)

    view_missing_meta(parent_folder, 10)

    # handle_missing_meta_in_all(parent_folder)

    # standardize_meta_in_all(parent_folder)
