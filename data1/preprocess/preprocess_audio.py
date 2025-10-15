import pandas as pd
import os
import glob

#--------------------------------------------------------Xử lý thiếu dữ liệu---------------------------
def view_missing_audio(file_path, n=5):
    """
    Xem thông tin cơ bản và missing values của 1 file with-audio.csv
    """
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    print(f"\n📂 File: {file_path}")
    print("Shape:", df.shape)
    print("Số giá trị thiếu theo cột:\n", df.isna().sum())
    print(f"\n{n} dòng đầu:\n", df.head(n))
    print("-"*60)
    return df

def view_missing_audio_in_all(parent_folder, n=5):
    """
    Duyệt tất cả subfolder trong parent_folder,
    hiển thị missing values của file *with-audio.csv
    """
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print("📂 Tổng số folder:", len(subfolders))
    for sub in subfolders:
        audio_files = glob.glob(os.path.join(sub, "*with-audio.csv"))
        if audio_files:
            view_missing_audio(audio_files[0], n=n)
        else:
            print(f"⚠️ Không tìm thấy with-audio.csv trong {sub}")

def preprocess_audio(file_path):
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 1. Gộp các hàng có track_id trùng nhau
    if "track_id" in df.columns:
        agg_funcs = {}
        for col in df.columns:
            if col == "track_id":
                continue
            elif df[col].dtype in ["float64", "int64"]:
                agg_funcs[col] = "mean"  # numeric -> mean
            else:
                agg_funcs[col] = "first" # categorical -> first non-null

        df = df.groupby("track_id", as_index=False).agg(agg_funcs)

    # 2. Fill missing cho numeric
    num_cols = df.select_dtypes(include=["float64", "int64"]).columns
    for col in num_cols:
        mean_val = df[col].mean()
        df[col] = df[col].fillna(mean_val)

    # 3. Fill missing cho categorical
    if "mode" in df.columns:
        df["mode"] = df["mode"].fillna("unknown")
    if "key" in df.columns:
        df["key"] = df["key"].fillna("unknown")
    if "href" in df.columns:
        df["href"] = df["href"].fillna("unknown_href")

    # 4. Chuẩn hóa tempo
    if "tempo" in df.columns:
        median_tempo = df["tempo"].median()
        df.loc[(df["tempo"] < 30) | (df["tempo"] > 250), "tempo"] = median_tempo

    # 5. Chuẩn hóa loudness
    if "loudness" in df.columns:
        median_loud = df["loudness"].median()
        df.loc[(df["loudness"] < -60) | (df["loudness"] > 0), "loudness"] = median_loud

    # 6. Ghi đè lại file gốc
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ Audio cleaned & merged: {file_path} (shape={df.shape})")

    return df


def handle_audio(parent_folder):
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print("📂 Tổng số folder:", len(subfolders))
    for sub in subfolders:
        audio_files = glob.glob(os.path.join(sub, "*with-audio.csv"))
        if audio_files:
            preprocess_audio(audio_files[0])
        else:
            print(f"⚠️ Không tìm thấy with-audio.csv trong {sub}")

#---------------------------------------------------Chuẩn hóa dữ liệu---------------------------
def standardize_audio(file_path):
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 1. Clip các feature [0,1]
    num_01_cols = [
        "danceability","energy","valence",
        "acousticness","instrumentalness","liveness","speechiness"
    ]
    for col in num_01_cols:
        if col in df.columns:
            df[col] = df[col].clip(0,1)  # giữ nguyên nếu trong [0,1]

    # 2. Tempo
    if "tempo" in df.columns:
        df["tempo"] = df["tempo"].clip(30,250)  # giữ trong khoảng hợp lý
        df["tempo_norm"] = (df["tempo"] - 30) / (250 - 30)

    # 3. Loudness
    if "loudness" in df.columns:
        df["loudness_norm"] = (df["loudness"] + 60) / 60
        df["loudness_norm"] = df["loudness_norm"].clip(0,1)

    # 4. Mode: fill NaN theo majority (0 hoặc 1)
    if "mode" in df.columns:
        if df["mode"].notna().sum() > 0:
            majority_val = df["mode"].dropna().mode()[0]  # giá trị phổ biến nhất
            df["mode"] = df["mode"].fillna(majority_val).astype(int)

    # 5. Key: giữ nguyên + thêm key_name
    key_map = {
        -1:"unknown",0:"C",1:"C#",2:"D",3:"D#",4:"E",5:"F",6:"F#",
        7:"G",8:"G#",9:"A",10:"A#",11:"B"
    }
    if "key" in df.columns:
        df["key_name"] = df["key"].map(key_map).fillna("unknown")

    # 6. Giữ nguyên các cột khác

    # Xuất lại file (ghi đè)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ Audio standardized: {file_path} (shape={df.shape})")

    return df


def standardize_audio_in_all(parent_folder):
    """
    Duyệt qua tất cả subfolder trong parent_folder,
    chuẩn hóa file *with-audio.csv trong từng folder.
    """
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print("📂 Tổng số folder:", len(subfolders))
    for sub in subfolders:
        audio_files = glob.glob(os.path.join(sub, "*with-audio.csv"))
        if audio_files:
            standardize_audio(audio_files[0])
        else:
            print(f"⚠️ Không tìm thấy with-audio.csv trong {sub}")


def fix_unknown_key(file_path):
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    if "key_name" not in df.columns:
        print(f"⚠️ Không có cột key_name trong file {file_path}")
        return df

    # Nếu vẫn còn cột key dạng số thì ưu tiên xử lý từ đó
    if "key" in df.columns:
        valid_keys = df.loc[df["key"] >= 0, "key"]
        if not valid_keys.empty:
            majority_key = int(valid_keys.mode()[0])
            df.loc[(df["key"] == -1) | (df["key"].isna()), "key"] = majority_key

        key_map = {
            0:"C",1:"C#",2:"D",3:"D#",4:"E",5:"F",6:"F#",
            7:"G",8:"G#",9:"A",10:"A#",11:"B"
        }
        df["key_name"] = df["key"].map(key_map).fillna("C")

    else:
        # Nếu chỉ có key_name thì thay "unknown" bằng giá trị phổ biến nhất
        if (df["key_name"] == "unknown").any():
            majority_keyname = df.loc[df["key_name"] != "unknown", "key_name"].mode()[0]
            df["key_name"] = df["key_name"].replace("unknown", majority_keyname)

    # Ghi đè lại file
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ Fixed unknown key_name in {file_path} (shape={df.shape})")

    return df


def fix_unknown_key_in_all(parent_folder):
    """
    Duyệt qua tất cả subfolder trong parent_folder,
    xử lý unknown trong file *-with-audio.csv.
    """
    subfolders = [
        os.path.join(parent_folder, name)
        for name in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, name))
    ]

    print("📂 Tổng số folder:", len(subfolders))
    for sub in subfolders:
        audio_files = glob.glob(os.path.join(sub, "*with-audio.csv"))
        if audio_files:
            fix_unknown_key(audio_files[0])
        else:
            print(f"⚠️ Không tìm thấy with-audio.csv trong {sub}")

if __name__ == "__main__":
    parent_folder = os.path.join("..", "data", "data-top50")  # 🔧 thay đường dẫn gốc của bạn
   
    view_missing_audio_in_all(parent_folder, 10)

    # handle_audio(parent_folder)
    # standardize_audio_in_all(parent_folder)
    # fix_unknown_key_in_all(parent_folder)