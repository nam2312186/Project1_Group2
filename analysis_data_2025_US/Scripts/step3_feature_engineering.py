import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_step3(save_output=True):
    print(">>> STEP 3: FEATURE ENGINEERING (Billboard Hot 100 US) <<<")

    # ===== PATH CONFIG =====
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "Output", "step2", "billboard_cleaned.csv")
    out_dir = os.path.join(base_dir, "Output", "step3")
    if save_output:
        os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, "billboard_features.csv")

    # ===== 1. Load dữ liệu =====
    df = pd.read_csv(input_file, encoding="utf-8-sig")
    print(f"Đọc dữ liệu từ: {input_file}")

    # chuyển cột week sang datetime
    df["week"] = pd.to_datetime(df["week"], errors="coerce")

    # ===== 2. Track-level features =====
    weeks_total = (
        df.drop_duplicates(["spotify_id", "week"])        # mỗi tuần/track chỉ tính 1 lần
        .groupby("spotify_id")["week"]
        .nunique()
        .reset_index(name="weeks_on_chart_total")
    )
    df = df.merge(weeks_total, on="spotify_id", how="left")
    
    df = df.sort_values(["spotify_id", "week"])
    df["weeks_on_chart_cum"] = (
        df.groupby("spotify_id")["week"]
        .rank(method="dense", ascending=True)
        .astype(int)
    )

    df["peak_rank"] = df.groupby("spotify_id")["rank"].transform("min")
    df["avg_rank"] = df.groupby("spotify_id")["rank"].transform("mean").round(2)
    df["is_top10"] = (df["rank"] <= 10).astype(int)
    df["is_new"] = (df["weeks_on_chart_cum"] == 1).astype(int)

    # Sắp xếp lại theo tuần và rank
    df = df.sort_values(["week", "rank"]).reset_index(drop=True)

    # ===== 3. Artist-based features =====
    df["is_collab"] = df["artist"].str.contains("feat\.|&|,", case=False, regex=True).astype(int)

    # ===== 4. Time-based features (US seasons) =====
    def get_season(month):
        if month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        elif month in [9, 10, 11]:
            return "Fall"
        else:
            return "Winter"
    df["season"] = df["week"].dt.month.apply(get_season)


    # ===== 5. Xuất dữ liệu enriched =====
    if save_output:
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f" Xuất thành công → {output_file}")

    # ===== 6. Summary =====
    info_text = []
    info_text.append(f"Số dòng: {df.shape[0]}")
    info_text.append(f"Số cột: {df.shape[1]}")
    info_text.append("\nTên cột: " + ", ".join(df.columns))
    info_text.append("\nKiểu dữ liệu:\n" + str(df.dtypes))
    info_text.append("\nGiá trị Null:\n" + str(df.isnull().sum()))
    info_text.append(f"\nSố dòng trùng lặp: {df.duplicated().sum()}")
    info_text.append("\nThống kê mô tả:\n" + str(df.describe(include="all")))

    if save_output:
        with open(os.path.join(out_dir, "summary_features.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(info_text))
        print(f" Xuất summary_features.txt vào {out_dir}")

    # ===== 7. Ma trận tương quan =====
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        df.corr(numeric_only=True),
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1, vmax=1, center=0
    )
    plt.title("Ma trận tương quan sau khi thêm đặc trưng (Step 3)")
    plt.tight_layout()
    plt.xticks(rotation=45, ha="right")
    if save_output:
        plt.savefig(os.path.join(out_dir, "correlation_matrix_step3.png"))
        print(f" Xuất correlation_matrix_step3.png vào {out_dir}")
    plt.close()

    return df
