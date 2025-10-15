import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Đường dẫn thư mục dữ liệu và output
DATA_DIR = os.path.join('data', 'data-top50')
OUTPUT_DIR = os.path.join('reports/figure/analysis/output_heatmap', 'cluster_mood_detail')

# Các đặc trưng sử dụng cho phân cụm
FEATURES = [
    'energy', 'acousticness', 'danceability', 'tempo',
    'valence', 'mode', 'instrumentalness'
]

MOOD_LABELS = [
    'Chill/Relax',        # low energy, high acousticness
    'Dance/Party',       # high danceability, mid-high tempo
    'Sad/Emotional',     # low valence, minor mode
    'Instrumental'       # high instrumentalness
]

def get_country_csvs(data_dir):
    countries = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    csv_files = {}
    for country in countries:
        country_dir = os.path.join(data_dir, country)
        for file in os.listdir(country_dir):
            if file.endswith('-with-audio.csv'):
                csv_files[country] = os.path.join(country_dir, file)
                break
    return csv_files

def assign_mood_labels(cluster_centers):
    labels = []
    for center in cluster_centers:
        if center[0] < 0 and center[1] > 0.5:
            labels.append('Chill/Relax')
        elif center[2] > 0.5 and center[3] > 0:
            labels.append('Dance/Party')
        elif center[4] < 0 and center[5] < 0:
            labels.append('Sad/Emotional')
        elif center[6] > 0.5:
            labels.append('Instrumental')
        else:
            labels.append('Other')
    return labels

def cluster_and_analyze(df, country, output_dir):
    df = df.dropna(subset=FEATURES)
    X = df[FEATURES].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    mood_labels = assign_mood_labels(kmeans.cluster_centers_)
    cluster_moods = [mood_labels[c] for c in clusters]
    df['cluster'] = clusters
    df['mood'] = cluster_moods
    # Thống kê trung bình các đặc trưng cho từng cluster
    summary = df.groupby(['cluster', 'mood'])[FEATURES].mean()
    summary['count'] = df.groupby(['cluster', 'mood']).size()
    summary = summary.reset_index()
    os.makedirs(output_dir, exist_ok=True)
    summary.to_csv(os.path.join(output_dir, f'{country}_cluster_detail.csv'), index=False)

    # --- Visualization ---
    import matplotlib.pyplot as plt
    import seaborn as sns
    # Bar chart: số lượng bài hát theo mood
    plt.figure(figsize=(7,4))
    sns.barplot(data=summary, x='mood', y='count', palette='Set2')
    plt.title(f'Số lượng bài hát theo mood ({country})')
    plt.ylabel('Số lượng')
    plt.xlabel('Mood')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{country}_bar_mood_count.png'))
    plt.close()

    # Radar chart: đặc trưng trung bình từng cluster
    def plot_radar(df, features, mood_col, country, output_dir):
        import numpy as np
        import matplotlib.pyplot as plt
        moods = df[mood_col].values
        values = df[features].values
        N = len(features)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]
        plt.figure(figsize=(7,7))
        for i, mood in enumerate(moods):
            vals = values[i].tolist()
            vals += vals[:1]
            plt.polar(angles, vals, label=mood, linewidth=2)
        plt.xticks(angles[:-1], features, color='grey', size=12)
        plt.title(f'Đặc trưng trung bình từng mood ({country})', size=14)
        plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{country}_radar_mood_features.png'))
        plt.close()

    plot_radar(summary, FEATURES, 'mood', country, output_dir)

def main():
    csv_files = get_country_csvs(DATA_DIR)
    for country, csv_path in csv_files.items():
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f'Không thể đọc {csv_path}: {e}')
            continue
        if all(f in df.columns for f in FEATURES):
            cluster_and_analyze(df, country, OUTPUT_DIR)
        else:
            print(f'{country}: Thiếu một số cột đặc trưng cần thiết')

if __name__ == '__main__':
    main()
