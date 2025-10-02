import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def run_step1(save_output=True):
    print(">>> STEP 1: PHÂN TÍCH DỮ LIỆU GỐC <<<")

    # ====== PATH CONFIG ======
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "Output", "step0", "billboard_final.csv")
    out_dir = os.path.join(base_dir, "Output", "step1")
    if save_output:
        os.makedirs(out_dir, exist_ok=True)

    # ====== 1. Load dữ liệu ======
    print(f"Đọc dữ liệu từ: {input_file}")
    df = pd.read_csv(input_file, encoding="utf-8-sig")

    # ====== 2. Thông tin cơ bản ======
    info_text = []
    info_text.append(f"Số dòng: {df.shape[0]}")
    info_text.append(f"Số cột: {df.shape[1]}")
    info_text.append("\nTên cột: " + ", ".join(df.columns))
    info_text.append("\nKiểu dữ liệu:\n" + str(df.dtypes))
    info_text.append("\nGiá trị Null:\n" + str(df.isnull().sum()))
    info_text.append(f"\nSố dòng trùng lặp: {df.duplicated().sum()}")
    info_text.append("\nThống kê mô tả:\n" + str(df.describe(include="all")))

    # Xuất ra file summary.txt
    if save_output:
        with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(info_text))
        print(f"✅ Xuất summary.txt vào {out_dir}")

    # ====== 3. Biểu đồ missing values ======
    plt.figure(figsize=(14, 8))
    sns.heatmap(df.isnull(), cbar=False, cmap="viridis")
    plt.title("Biểu đồ giá trị thiếu (Missing values)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    if save_output:
        plt.savefig(os.path.join(out_dir, "missing_values.png"))
        print(f"✅ Xuất missing_values.png vào {out_dir}")
    plt.close()

    # ====== 4. Phân bố các feature quan trọng ======
    num_cols = [
        "danceability", "energy", "tempo", "valence",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "loudness"
    ]
    for col in num_cols:
        if col in df.columns:
            plt.figure(figsize=(7, 4))
            sns.histplot(df[col].dropna(), bins=30, kde=True)
            plt.title(f"Phân bố {col}")
            if save_output:
                plt.savefig(os.path.join(out_dir, f"{col}_distribution.png"))
            plt.close()
    print(f"✅ Xuất phân bố các feature quan trọng vào {out_dir}")

    # ====== 6. Phân bố thể loại (genre) ======
    if "genre" in df.columns:
        plt.figure(figsize=(10, 6))
        genre_counts = (
            df.loc[df["genre"] != "Unknown", "genre"]
            .value_counts()
            .head(15)   # top 15 thể loại phổ biến
        )
        sns.barplot(x=genre_counts.values, y=genre_counts.index, palette="viridis")
        plt.title("Top thể loại âm nhạc phổ biến nhất (không tính Unknown)")
        plt.xlabel("Số lần xuất hiện")
        plt.ylabel("Thể loại")
        plt.tight_layout()
        if save_output:
            plt.savefig(os.path.join(out_dir, "genre_distribution.png"))
            print(f" Xuất genre_distribution.png vào {out_dir}")
        plt.close()


    # ====== 5. Ma trận tương quan ======
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        df.corr(numeric_only=True),
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1, vmax=1, center=0  # đảm bảo thang -1 → 1
    )
    plt.title("Ma trận tương quan giữa các thuộc tính âm nhạc")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    if save_output:
        plt.savefig(os.path.join(out_dir, "correlation_matrix.png"))
        print(f"✅ Xuất correlation_matrix.png vào {out_dir}")
    plt.close()


    return df
