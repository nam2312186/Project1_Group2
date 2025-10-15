import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

BASE_FOLDER = "data/data-top50"
OUT_FOLDER = "reports/figure/output_heatmap/corr_matrix"

def process_folder(folder):
    audio_files = glob.glob(os.path.join(folder, "*-with-audio.csv"))
    meta_files = glob.glob(os.path.join(folder, "*-with-meta-clean.csv"))

    if not audio_files or not meta_files:
        print(f"❌ Bỏ qua {folder}, thiếu file audio/meta-clean")
        return

    audio_file = audio_files[0]
    meta_file = meta_files[0]

    print(f"\n📂 Đang xử lý: {folder}")

    try:
        df_audio = pd.read_csv(audio_file, encoding="utf-8-sig")
        df_meta = pd.read_csv(meta_file, encoding="utf-8-sig")

        df = pd.merge(df_audio, df_meta, on="track_id", how="inner")
        if df.empty:
            print("⚠️ Không có track_id trùng khớp")
            return

        # Chuyển cột bool sang int (0/1)
        for col in df.select_dtypes(include=["bool"]).columns:
            df[col] = df[col].astype(int)

        # Lấy tất cả cột số (bao gồm int, float, bool->int)
        numeric_df = df.select_dtypes(include=["number"])

        if numeric_df.empty:
            print("⚠️ Không có cột số")
            return

        corr = numeric_df.corr()

        plt.figure(figsize=(16, 12))
        sns.heatmap(
            corr,
            cmap="coolwarm",
            annot=True,        # hiển thị số
            fmt=".2f",         # làm tròn 2 chữ số
            annot_kws={"size": 7}
        )
        plt.title(f"Correlation Matrix - {os.path.basename(folder)} (All numeric cols)")
        plt.tight_layout()

        os.makedirs(OUT_FOLDER, exist_ok=True)
        out_file = os.path.join(OUT_FOLDER, f"{os.path.basename(folder)}_corr_all.png")
        plt.savefig(out_file, dpi=300)
        plt.close()

        print(f"✅ Đã lưu heatmap đầy đủ: {out_file}")

    except Exception as e:
        print(f"❌ Lỗi xử lý {folder}: {e}")

def main():
    folders = [f for f in glob.glob(f"{BASE_FOLDER}/*") if os.path.isdir(f)]
    print(f"🔎 Tìm thấy {len(folders)} folder")
    for folder in folders:
        process_folder(folder)

if __name__ == "__main__":
    main()
