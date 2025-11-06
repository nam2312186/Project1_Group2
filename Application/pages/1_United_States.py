import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import streamlit.components.v1 as components

# -----------------------------
# 1️⃣ Cấu hình giao diện
# -----------------------------
st.set_page_config(page_title="🇺🇸 United States Dashboard", layout="wide")
st.title("Music Trends Dashboard – United States")
st.caption("Chọn nguồn dữ liệu để xem dashboard tương ứng")

# -----------------------------
# 2️⃣ Kết nối MongoDB Atlas
# -----------------------------
uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["spotify_project"]

# -----------------------------
# 3️⃣ Tabs chọn nguồn dữ liệu
# -----------------------------
tab1, tab2 = st.tabs(["📊 Billboard Hot 100 (2025)", "🎧 Spotify Top 50 (2024)"])

# ====================================================================
# TAB 1️⃣ — Billboard Hot 100 (2025)
# ====================================================================
with tab1:
    collection = db["billboard_features_2025"]

    @st.cache_data
    def load_billboard_data():
        data = list(collection.find({}, {"_id": 0}))
        return pd.DataFrame(data)

    df = load_billboard_data()

    # ===== Hiệu ứng cuộn mượt (JS)
    components.html(
        """
        <script>
        const links = document.querySelectorAll('a[href^="#"]');
        for (let link of links) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    window.scrollTo({
                        top: target.offsetTop - 80,
                        behavior: 'smooth'
                    });
                }
            });
        }
        </script>
        """,
        height=0,
    )
    
    # ===== MỤC LỤC =====
    st.markdown("""
    ### 🧭 **Mục lục**
    - [📊 Tổng quan dữ liệu](#section-tong-quan)
    - [🎧 Phân tích xu hướng thể loại](#section-the-loai)
    - [🌟 Nghệ sĩ & Bài hát nổi bật](#section-nghe-si)
    - [🌤️ Đặc trưng âm nhạc theo mùa](#section-theo-mua)
    - [📈 Phân tích độ bền & thứ hạng](#section-do-ben)
    - [🔥 Biến động độ hot theo thời gian](#section-do-hot)
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ===== SECTION 1 =====
    st.markdown('<a id="section-tong-quan"></a>', unsafe_allow_html=True)
    st.markdown("## 📊 Tổng quan dữ liệu Billboard 2025")

    col1, col2, col3 = st.columns(3)
    col1.metric("Số bài hát", len(df))
    col2.metric("Số nghệ sĩ", df['artist'].nunique())
    col3.metric("Số thể loại", df['genre'].nunique())

    st.markdown("---")

    # ===== SECTION 2 =====
    st.markdown('<a id="section-the-loai"></a>', unsafe_allow_html=True)
    st.markdown("## 🎧 Phân tích xu hướng thể loại (Genre Trends)")

    selected_feature = st.selectbox("Chọn đặc trưng âm nhạc", ["energy", "danceability", "valence", "tempo"])
    genre_stats = df.groupby("genre")[selected_feature].mean().sort_values(ascending=False).reset_index()

    fig_genre = px.bar(
        genre_stats.head(15),
        x="genre",
        y=selected_feature,
        color=selected_feature,
        title=f"Top 15 Thể loại theo {selected_feature}"
    )
    st.plotly_chart(fig_genre, width="stretch")

    st.markdown("---")

    # ===== SECTION 3 =====
    st.markdown('<a id="section-nghe-si"></a>', unsafe_allow_html=True)
    st.markdown("## 🌟 Nghệ sĩ & Bài hát nổi bật")

    option = st.radio("Chọn tiêu chí hiển thị", ["Top 10 Nghệ sĩ", "Top 10 Bài hát"])
    if option == "Top 10 Nghệ sĩ":
        top_artist = df['artist'].value_counts().head(10)
        fig_artist = px.bar(
            top_artist,
            x=top_artist.index,
            y=top_artist.values,
            title="Top 10 Nghệ sĩ có nhiều bài trên BXH nhất"
        )
        st.plotly_chart(fig_artist, width="stretch")
    else:
        top_songs = df.groupby("title")["weeks_on_chart_total"].max().sort_values(ascending=False).head(10)
        fig_song = px.bar(
            top_songs,
            x=top_songs.index,
            y=top_songs.values,
            title="Top 10 Bài hát trụ BXH lâu nhất"
        )
        st.plotly_chart(fig_song, width="stretch")

    st.markdown("---")

    # ===== SECTION 4 =====
    st.markdown('<a id="section-theo-mua"></a>', unsafe_allow_html=True)
    st.markdown("## 🌤️ Đặc trưng âm nhạc theo mùa (Seasonal Patterns)")

    season_features = df.groupby("season")[["energy", "valence", "danceability"]].mean().reset_index()
    fig_season = px.line(
        season_features,
        x="season",
        y=["energy", "valence", "danceability"],
        markers=True,
        title="Thay đổi đặc trưng âm nhạc theo mùa"
    )
    st.plotly_chart(fig_season, width="stretch")

    st.markdown("---")

    # ===== SECTION 5 =====
    st.markdown('<a id="section-do-ben"></a>', unsafe_allow_html=True)
    st.markdown("## 📈 Phân tích độ bền & Thứ hạng (Longevity vs Peak Rank)")

    fig_corr = px.scatter(
        df,
        x="peak_rank",
        y="weeks_on_chart_total",
        color="genre",
        hover_data=["title", "artist"],
        title="Mối quan hệ giữa Peak Rank và Số tuần trụ BXH"
    )
    st.plotly_chart(fig_corr, width="stretch")

    st.markdown("---")

    # ===== SECTION 6 =====
    st.markdown('<a id="section-do-hot"></a>', unsafe_allow_html=True)
    st.markdown("## 🔥 Biến động độ hot của bài hát trong năm 2025")

    if "week" in df.columns and "rank" in df.columns:
        df["week"] = pd.to_datetime(df["week"], errors="coerce")

        selected_song = st.selectbox("Chọn bài hát để xem độ hot", sorted(df['title'].unique()))
        song_data = df[df['title'] == selected_song].sort_values("week")

        if not song_data.empty:
            fig_rank = px.line(
                song_data,
                x="week",
                y="rank",
                markers=True,
                title=f"Biến động thứ hạng của bài hát: {selected_song}",
                labels={"rank": "Thứ hạng (1 là cao nhất)", "week": "Tuần"},
            )
            fig_rank.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_rank, width="stretch")

            best_rank = int(song_data["rank"].min())
            longest_weeks = song_data["week"].nunique()
            st.info(f"🎤 {selected_song} đạt hạng cao nhất là **Top {best_rank}**, trụ BXH trong **{longest_weeks} tuần**.")
        else:
            st.warning("Không có dữ liệu thứ hạng cho bài hát này.")
    else:
        st.error("⚠️ Dữ liệu hiện chưa có trường 'week' hoặc 'rank'.")


# ====================================================================
# TAB 2️⃣ — Spotify Top 50 (2024)
# ====================================================================
with tab2:
    collection_spotify = db["spotify_top50_2024"]

    @st.cache_data
    def load_spotify_data():
        data = list(collection_spotify.find({}, {"_id": 0}))
        return pd.DataFrame(data)

    df_spotify = load_spotify_data()

    st.header("🎧 Spotify Top 50 (2024)")
    st.write("Hiển thị dữ liệu Spotify 2024 cho Hoa Kỳ (đang cập nhật...)")

    if not df_spotify.empty:
        st.dataframe(df_spotify.head(20))
    else:
        st.warning("Chưa có dữ liệu Spotify Top 50 (2024) trong MongoDB.")
