import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_step2(save_output=True):
    print(">>> STEP 2: CLEAN DỮ LIỆU <<<")

    # ====== PATH CONFIG ======
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "Output", "step0", "billboard_final.csv")
    out_dir = os.path.join(base_dir, "Output", "step2")
    if save_output:
        os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, "billboard_cleaned.csv")

    # ====== 1. Load dữ liệu ======
    df = pd.read_csv(input_file, encoding="utf-8-sig")
    print(f"Đọc dữ liệu từ: {input_file}")

    # ====== 2. Chuyển kiểu dữ liệu ======
    if "week" in df.columns:
        df["week"] = pd.to_datetime(df["week"], errors="coerce")
    if "rank" in df.columns:
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")

    # ====== 3. Xử lý missing ======
    num_cols = [
        "danceability","energy","tempo","valence",
        "speechiness","acousticness","instrumentalness",
        "liveness","loudness","key","mode"
    ]
    for col in num_cols:
        if col in df.columns:
            mean_val = df[col].mean()
            df[col].fillna(mean_val, inplace=True)
            print(f"   Điền missing {col} bằng mean = {mean_val:.4f}")

    if "genre" in df.columns:
        df["genre"].fillna("Unknown", inplace=True)
        print("   Điền missing genre = 'Unknown'")

    # ====== 4. Xuất dữ liệu sạch ======
    if save_output:
        df.to_csv(output_file, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
        print(f"🎉 Xuất thành công → {output_file}")

    # ====== 5. Summary ======
    info_text = []
    info_text.append(f"Số dòng: {df.shape[0]}")
    info_text.append(f"Số cột: {df.shape[1]}")
    info_text.append("\nTên cột: " + ", ".join(df.columns))
    info_text.append("\nKiểu dữ liệu:\n" + str(df.dtypes))
    info_text.append("\nGiá trị Null (sau clean):\n" + str(df.isnull().sum()))
    info_text.append(f"\nSố dòng trùng lặp (sau clean): {df.duplicated().sum()}")
    info_text.append("\nThống kê mô tả:\n" + str(df.describe(include='all')))

    if save_output:
        with open(os.path.join(out_dir, "summary_clean.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(info_text))
        print(f"📄 Xuất summary_clean.txt vào {out_dir}")

    # ====== 6. Biểu đồ missing values ======
    plt.figure(figsize=(14, 8))
    sns.heatmap(df.isnull(), cbar=False, cmap="viridis")
    plt.title("Biểu đồ giá trị thiếu (sau khi clean)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    if save_output:
        plt.savefig(os.path.join(out_dir, "missing_values_after_clean.png"))
    plt.close()

    # ====== 7. Ma trận tương quan ======
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        df.corr(numeric_only=True),
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1, vmax=1, center=0
    )
    plt.title("Ma trận tương quan sau khi làm sạch")
    plt.tight_layout()
    plt.xticks(rotation=45, ha="right")
    if save_output:
        plt.savefig(os.path.join(out_dir, "correlation_matrix.png"))
    plt.close()


    return df
