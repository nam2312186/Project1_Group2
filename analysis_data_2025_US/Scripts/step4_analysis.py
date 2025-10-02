import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_step4(save_output=True):
    print(">>> STEP 4: ANALYSIS & INSIGHTS (Billboard Hot 100 US) <<<")

    # ===== PATH CONFIG =====
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "Output", "step3", "billboard_features.csv")
    out_dir = os.path.join(base_dir, "Output", "step4")
    if save_output:
        os.makedirs(out_dir, exist_ok=True)

    # ===== 1. Load dữ liệu =====
    df = pd.read_csv(input_file, encoding="utf-8-sig")
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    print(f"Đọc dữ liệu từ: {input_file}")

    # ===== 2. Xu hướng bài hát theo thời gian =====
    # (a) New entries theo tuần
    new_entries = df.groupby("week")["is_new"].sum()
    plt.figure(figsize=(12,6))
    new_entries.plot(kind="line", marker="o")
    plt.title("Số lượng bài hát mới (new entry) theo tuần")
    plt.ylabel("Số new entry")
    plt.tight_layout()
    if save_output:
        plt.savefig(os.path.join(out_dir, "new_entry_trend.png"))
    plt.close()

    # (b) Phân phối longevity
    plt.figure(figsize=(8,5))
    sns.histplot(df.drop_duplicates("spotify_id")["weeks_on_chart_total"], bins=20)
    plt.title("Phân phối số tuần tồn tại của các bài hát (Longevity)")
    plt.xlabel("Số tuần trên BXH")
    plt.ylabel("Số bài hát")
    if save_output:
        plt.savefig(os.path.join(out_dir, "hit_longevity.png"))
    plt.close()

    # (c) Timeline một số hit đình đám (peak = 1)
    top_tracks = df[df["peak_rank"] == 1]["spotify_id"].unique()[:5]
    sample = df[df["spotify_id"].isin(top_tracks)]
    plt.figure(figsize=(12,6))
    sns.lineplot(data=sample, x="week", y="rank", hue="title", marker="o")
    plt.gca().invert_yaxis()
    plt.title("Timeline rank của một số track đình đám")
    if save_output:
        plt.savefig(os.path.join(out_dir, "track_timeline.png"))
    plt.close()

    # ===== 3. Thể loại trong Top 10 =====
    top10_genres = (
        df[(df["is_top10"] == 1) & (df["genre"] != "Unknown")]  # bỏ Unknown
        ["genre"]
        .value_counts()
        .head(10)
    )

    plt.figure(figsize=(8,5))
    sns.barplot(x=top10_genres.values, y=top10_genres.index, palette="magma")

    plt.title("Thể loại phổ biến trong Top 10", fontsize=14, fontweight="bold")
    plt.xlabel("Số lần xuất hiện trong Top 10", fontsize=12)
    plt.ylabel("Thể loại", fontsize=12)
    plt.tight_layout()

    # hiển thị số lượng trên cột
    for i, v in enumerate(top10_genres.values):
        plt.text(v + 0.2, i, str(v), va="center", fontsize=10)

    if save_output:
        plt.savefig(os.path.join(out_dir, "top10_genres.png"))
    plt.close()


    # ===== 4. Top nghệ sĩ trong bài hát Top 10 =====
    top_artists = (
        df[df["is_top10"] == 1]
        .groupby("artist")["title"]
        .nunique()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10,6))
    sns.barplot(
        x=top_artists.values,
        y=top_artists.index,
        palette="viridis"
    )

    plt.title("Top 10 nghệ sĩ có nhiều bài vào Top 10 Billboard Hot 100 (2025)", fontsize=14, fontweight="bold")
    plt.xlabel("Số lượng bài hát vào Top 10", fontsize=12)
    plt.ylabel("Nghệ sĩ", fontsize=12)

    # Hiển thị số ngay trên bar
    for i, v in enumerate(top_artists.values):
        plt.text(v + 0.1, i, str(v), color="black", va="center", fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "top_artists_top10.png"))
    plt.close()

    # ===== 5. Audio features theo mùa =====
    features = ["danceability","energy","valence"]
    season_features = df.groupby("season")[features].mean()
    season_features.plot(kind="bar", figsize=(10,6))
    plt.title("So sánh đặc trưng audio theo mùa")
    plt.ylabel("Giá trị trung bình")
    plt.xticks(rotation=0)
    if save_output:
        plt.savefig(os.path.join(out_dir, "season_features.png"))
    plt.close()

    # ===== 6. Longevity vs Peak rank =====
    plt.figure(figsize=(8,5))
    sns.regplot(data=df.drop_duplicates("spotify_id"), x="peak_rank", y="weeks_on_chart_total")
    plt.title("Tuổi thọ bài hát vs Peak Rank")
    plt.xlabel("Peak Rank (1 = cao nhất)")
    plt.ylabel("Số tuần trên BXH")
    if save_output:
        plt.savefig(os.path.join(out_dir, "longevity_vs_peak.png"))
    plt.close()

    

    # ===== 7. Xuất summary =====
    info_text = []
    info_text.append("=== STEP 4 SUMMARY ===")
    info_text.append(f"Số dòng: {df.shape[0]}")
    info_text.append(f"Số cột: {df.shape[1]}")
    info_text.append("\nTên cột: " + ", ".join(df.columns))
    info_text.append("\nGiá trị Null:\n" + str(df.isnull().sum()))
    info_text.append("\nMô tả thống kê:\n" + str(df.describe(include='all')))

    if save_output:
        with open(os.path.join(out_dir, "summary_step4.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(info_text))
        print(f" Xuất summary_step4.txt vào {out_dir}")

    print(" STEP 4 hoàn tất")

    return df
