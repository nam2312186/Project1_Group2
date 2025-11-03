import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# -----------------------------
# 1️⃣ Kết nối MongoDB Atlas
# -----------------------------
uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["spotify_project"]
collection = db["billboard_features_2025"]

# -----------------------------
# 2️⃣ Tải dữ liệu vào DataFrame
# -----------------------------
@st.cache_data
def load_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    return df

df = load_data()

st.set_page_config(page_title="🎵 Billboard Hot 100 – Dashboard", layout="wide")
st.title("🎵 Billboard Hot 100 – Music Trends Dashboard (2025)")

st.markdown("---")

# -----------------------------
# 3️⃣ Section 1: Tổng quan dữ liệu
# -----------------------------
st.header("📊 Tổng quan dữ liệu Billboard 2025")

col1, col2, col3 = st.columns(3)
col1.metric("Số bài hát", len(df))
col2.metric("Số nghệ sĩ", df['artist'].nunique())
col3.metric("Số thể loại", df['genre'].nunique())

st.markdown("---")

# -----------------------------
# 4️⃣ Section 2: Phân tích xu hướng thể loại
# -----------------------------
st.header("🎧 Phân tích xu hướng thể loại (Genre Trends)")

selected_feature = st.selectbox("Chọn đặc trưng âm nhạc", ["energy", "danceability", "valence", "tempo"])
genre_stats = df.groupby("genre")[selected_feature].mean().sort_values(ascending=False).reset_index()

fig_genre = px.bar(genre_stats.head(15), x="genre", y=selected_feature,
                   color=selected_feature, title=f"Top 15 Thể loại theo {selected_feature}")
st.plotly_chart(fig_genre, use_container_width=True)

st.markdown("---")

# -----------------------------
# 5️⃣ Section 3: Nghệ sĩ và bài hát nổi bật
# -----------------------------
st.header("🌟 Nghệ sĩ & Bài hát nổi bật")

option = st.radio("Chọn tiêu chí hiển thị", ["Top 10 Nghệ sĩ", "Top 10 Bài hát"])
if option == "Top 10 Nghệ sĩ":
    top_artist = df['artist'].value_counts().head(10)
    fig_artist = px.bar(top_artist, x=top_artist.index, y=top_artist.values,
                        title="Top 10 Nghệ sĩ có nhiều bài trên BXH nhất")
    st.plotly_chart(fig_artist, use_container_width=True)
else:
    top_songs = df.groupby("title")["weeks_on_chart_total"].max().sort_values(ascending=False).head(10)
    fig_song = px.bar(top_songs, x=top_songs.index, y=top_songs.values,
                      title="Top 10 Bài hát trụ BXH lâu nhất")
    st.plotly_chart(fig_song, use_container_width=True)

st.markdown("---")

# -----------------------------
# 6️⃣ Section 4: Đặc trưng âm nhạc theo mùa
# -----------------------------
st.header("🌤️ Đặc trưng âm nhạc theo mùa (Seasonal Patterns)")

season_features = df.groupby("season")[["energy", "valence", "danceability"]].mean().reset_index()
fig_season = px.line(season_features, x="season", y=["energy", "valence", "danceability"],
                     markers=True, title="Thay đổi đặc trưng âm nhạc theo mùa")
st.plotly_chart(fig_season, use_container_width=True)

st.markdown("---")

# -----------------------------
# 7️⃣ Section 5: Phân tích độ bền & thứ hạng
# -----------------------------
st.header("📈 Phân tích độ bền & Thứ hạng (Longevity vs Peak Rank)")

fig_corr = px.scatter(df, x="peak_rank", y="weeks_on_chart_total",
                      color="genre", hover_data=["title", "artist"],
                      title="Mối quan hệ giữa Peak Rank và Số tuần trụ BXH")
st.plotly_chart(fig_corr, use_container_width=True)


# -----------------------------
# 8️⃣ Section 6: Biến động độ hot theo thời gian
# -----------------------------
st.header("🔥 Biến động độ hot của bài hát trong năm 2025")

# Kiểm tra nếu dữ liệu có cột 'week' và 'rank'
if "week" in df.columns and "rank" in df.columns:
    df["week"] = pd.to_datetime(df["week"], errors="coerce")

    # Cho người dùng chọn bài hát để xem xu hướng
    selected_song = st.selectbox("Chọn bài hát để xem độ hot", sorted(df['title'].unique()))
    song_data = df[df['title'] == selected_song].sort_values("week")

    if not song_data.empty:
        fig_rank = px.line(
            song_data,
            x="week",
            y="rank",
            markers=True,
            title=f"Biến động thứ hạng (độ hot) của bài hát: {selected_song}",
            labels={"rank": "Thứ hạng (1 là cao nhất)", "week": "Tuần"},
        )

        # Đảo chiều trục Y vì rank 1 là cao nhất
        fig_rank.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_rank, use_container_width=True)

        # Thêm nhận xét tự động
        best_rank = int(song_data["rank"].min())
        longest_weeks = song_data["week"].nunique()
        st.info(f"🎤 {selected_song} đạt hạng cao nhất là **Top {best_rank}**, trụ BXH trong **{longest_weeks} tuần**.")
    else:
        st.warning("Không có dữ liệu thứ hạng cho bài hát này.")
else:
    st.error("⚠️ Dữ liệu hiện chưa có trường 'week' hoặc 'rank'. Hãy kiểm tra lại dataset.")


st.success("✅ Dashboard sẵn sàng! Bạn có thể cuộn để xem từng phần.")
