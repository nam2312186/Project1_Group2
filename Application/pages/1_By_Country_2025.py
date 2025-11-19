import importlib.util
import sys, os
import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import streamlit.components.v1 as components
from datetime import datetime, timedelta


# =============================
# 🧩 Import module By_Country (phòng khi cần)
# =============================
spec = importlib.util.spec_from_file_location(
    "by_country", os.path.join("pages/2_By_Country_2024.py")
)
module = importlib.util.module_from_spec(spec)
sys.modules["by_country"] = module
spec.loader.exec_module(module)
render_country_dashboard = module.render_country_dashboard

# -----------------------------
# 1️⃣ Cấu hình giao diện
# -----------------------------
st.set_page_config(page_title="By Country 2025", layout="wide")
st.title("🎶 Music Trends Dashboard – United States (Billboard Hot 100, 2025)")
st.caption("Dữ liệu được lấy từ collection **top100_usa_2025** trong MongoDB Atlas")

# -----------------------------
# 2️⃣ Kết nối MongoDB Atlas
# -----------------------------
uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["spotify_project"]
collection = db["top100_usa_2025"]

# -----------------------------
# 3️⃣ Load dữ liệu Billboard 2025
# -----------------------------
@st.cache_data
def load_billboard_data():
    data = list(collection.find({}, {"_id": 0}))
    return pd.DataFrame(data)

df = load_billboard_data()
if df.empty:
    st.warning("⚠️ Không tìm thấy dữ liệu trong collection `top100_usa_2025`.")
    st.stop()

# -----------------------------
# 4️⃣ Hiệu ứng cuộn mượt (JS)
# -----------------------------
components.html("""
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
""", height=0)

# -----------------------------
# 5️⃣ Bộ lọc thời gian chung
# -----------------------------
if "week" in df.columns:
    st.markdown("### 📆 Bộ lọc thời gian phân tích (Billboard 2025)")

    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    min_date = pd.to_datetime("2025-01-05")
    max_date = pd.to_datetime("2025-09-28")

    start_date, end_date = st.slider(
        "Chọn phạm vi tuần muốn phân tích:",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
        format="YYYY-MM-DD",
        step=timedelta(days=7)
    )

    st.caption(f"📅 Dữ liệu trong khoảng **{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}**")

    df_filtered = df[(df["week"] >= pd.to_datetime(start_date)) & (df["week"] <= pd.to_datetime(end_date))]
else:
    st.warning("⚠️ Dataset chưa có trường 'week'. Bộ lọc thời gian không khả dụng.")
    df_filtered = df.copy()

# -----------------------------
# 6️⃣ Mục lục
# -----------------------------
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

# =====================================================================
# 📊 1. TỔNG QUAN DỮ LIỆU
# =====================================================================
st.markdown('<a id="section-tong-quan"></a>', unsafe_allow_html=True)
st.markdown("## 📊 Tổng quan dữ liệu Billboard 2025")

col1, col2, col3 = st.columns(3)
col1.metric("Số bài hát", len(df_filtered))
col2.metric("Số nghệ sĩ", df_filtered['artist'].nunique() if 'artist' in df_filtered else 0)
col3.metric("Số thể loại", df_filtered['genre'].nunique() if 'genre' in df_filtered else 0)

st.markdown("---")

# =====================================================================
# 🎧 2. PHÂN TÍCH THỂ LOẠI
# =====================================================================
st.markdown('<a id="section-the-loai"></a>', unsafe_allow_html=True)
st.markdown("## 🎧 Phân tích xu hướng thể loại (Genre Trends)")

if 'genre' in df_filtered.columns:
    selected_feature = st.selectbox(
        "Chọn đặc trưng âm nhạc",
        [f for f in ["energy", "danceability", "valence", "tempo"] if f in df_filtered.columns]
    )
    if selected_feature:
        genre_stats = (
            df_filtered.groupby("genre")[selected_feature]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig_genre = px.bar(
            genre_stats.head(15),
            x="genre",
            y=selected_feature,
            color=selected_feature,
            title=f"Top 15 Thể loại theo {selected_feature}"
        )
        st.plotly_chart(fig_genre, use_container_width=True)
else:
    st.warning("⚠️ Dữ liệu chưa có cột 'genre'.")

st.markdown("---")

# =====================================================================
# 🌟 3. NGHỆ SĨ & BÀI HÁT NỔI BẬT
# =====================================================================
st.markdown('<a id="section-nghe-si"></a>', unsafe_allow_html=True)
st.markdown("## 🌟 Nghệ sĩ & Bài hát nổi bật")

if 'artist' in df_filtered.columns:
    option = st.radio("Chọn tiêu chí hiển thị", ["Top 10 Nghệ sĩ", "Top 10 Bài hát"])
    if option == "Top 10 Nghệ sĩ":
        top_artist = df_filtered['artist'].value_counts().head(10)
        fig_artist = px.bar(
            top_artist,
            x=top_artist.index,
            y=top_artist.values,
            title="Top 10 Nghệ sĩ có nhiều bài trên BXH nhất"
        )
        st.plotly_chart(fig_artist, use_container_width=True)
    else:
        if 'weeks_on_chart_total' in df_filtered.columns and 'title' in df_filtered.columns:
            top_songs = (
                df_filtered.groupby("title")["weeks_on_chart_total"]
                .max()
                .sort_values(ascending=False)
                .head(10)
            )
            fig_song = px.bar(
                top_songs,
                x=top_songs.index,
                y=top_songs.values,
                title="Top 10 Bài hát trụ BXH lâu nhất"
            )
            st.plotly_chart(fig_song, use_container_width=True)
else:
    st.warning("⚠️ Dữ liệu chưa có trường 'artist' hoặc 'title'.")

st.markdown("---")

# =====================================================================
# 🌤️ 4. THEO MÙA
# =====================================================================
st.markdown('<a id="section-theo-mua"></a>', unsafe_allow_html=True)
st.markdown("## 🌤️ Đặc trưng âm nhạc theo mùa (Seasonal Patterns)")

if 'season' in df_filtered.columns:
    season_features = (
        df_filtered.groupby("season")[["energy", "valence", "danceability"]]
        .mean()
        .reset_index()
    )
    fig_season = px.line(
        season_features,
        x="season",
        y=["energy", "valence", "danceability"],
        markers=True,
        title="Thay đổi đặc trưng âm nhạc theo mùa"
    )
    st.plotly_chart(fig_season, use_container_width=True)
else:
    st.info("⚠️ Dữ liệu không có cột 'season' để phân tích theo mùa.")

st.markdown("---")

# =====================================================================
# 📈 5. ĐỘ BỀN & THỨ HẠNG
# =====================================================================
st.markdown('<a id="section-do-ben"></a>', unsafe_allow_html=True)
st.markdown("## 📈 Phân tích độ bền & Thứ hạng (Longevity vs Peak Rank)")

if all(c in df_filtered.columns for c in ["peak_rank", "weeks_on_chart_total"]):
    fig_corr = px.scatter(
        df_filtered,
        x="peak_rank",
        y="weeks_on_chart_total",
        color="genre" if "genre" in df_filtered else None,
        hover_data=["title", "artist"],
        title="Mối quan hệ giữa Peak Rank và Số tuần trụ BXH"
    )
    st.plotly_chart(fig_corr, use_container_width=True)
else:
    st.warning("⚠️ Dữ liệu thiếu 'peak_rank' hoặc 'weeks_on_chart_total'.")

st.markdown("---")

# =====================================================================
# 🔥 6. BIẾN ĐỘNG ĐỘ HOT
# =====================================================================
st.markdown('<a id="section-do-hot"></a>', unsafe_allow_html=True)
st.markdown("## 🔥 Biến động độ hot của bài hát trong năm 2025")

if all(c in df_filtered.columns for c in ["week", "rank", "title"]):
    selected_song = st.selectbox("Chọn bài hát để xem độ hot", sorted(df_filtered['title'].unique()))
    song_data = df_filtered[df_filtered['title'] == selected_song].sort_values("week")

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
        st.plotly_chart(fig_rank, use_container_width=True)

        best_rank = int(song_data["rank"].min())
        longest_weeks = song_data["week"].nunique()
        st.info(f"🎤 {selected_song} đạt hạng cao nhất là **Top {best_rank}**, trụ BXH trong **{longest_weeks} tuần**.")
    else:
        st.warning("⚠️ Không có dữ liệu thứ hạng cho bài hát này.")
else:
    st.error("⚠️ Dữ liệu hiện chưa có trường 'week' hoặc 'rank'.")

# =====================================================================
# 📋 7. DỮ LIỆU GỐC – Bộ lọc riêng (không bị ảnh hưởng bởi time filter)
# =====================================================================
st.markdown("> ⚠️ **Lưu ý:** Bộ lọc thời gian ở trên không ảnh hưởng đến phần “📋 Dữ liệu Gốc” bên dưới.")
st.markdown("---")
st.subheader("📋 Dữ liệu Gốc – Billboard Hot 100 (2025)")

# (giữ nguyên phần lọc bảng bạn đã có)
show_cols = [
    "week", "rank", "title", "artist", "genre",
    "energy", "danceability", "valence", "tempo",
    "weeks_on_chart_total", "peak_rank", "season", "is_top10", "is_new"
]
df_display = df.copy()

col1, col2, col3, col4 = st.columns(4)

if "week" in df_display.columns:
    min_date, max_date = df_display["week"].min(), df_display["week"].max()
    start_date, end_date = col1.date_input(
        "📅 Tuần từ / đến",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )
    df_display = df_display[
        (df_display["week"] >= pd.to_datetime(start_date))
        & (df_display["week"] <= pd.to_datetime(end_date))
    ]

if "genre" in df_display.columns:
    genres = sorted(df_display["genre"].dropna().unique())
    selected_genres = col2.multiselect("🎧 Thể loại", genres)
    if selected_genres:
        df_display = df_display[df_display["genre"].isin(selected_genres)]

if "season" in df_display.columns:
    seasons = sorted(df_display["season"].dropna().unique())
    selected_season = col3.selectbox("🌤️ Mùa", ["Tất cả"] + seasons)
    if selected_season != "Tất cả":
        df_display = df_display[df_display["season"] == selected_season]

if "rank" in df_display.columns:
    max_rank = int(df_display["rank"].max())
    rank_limit = col4.slider("🏆 Thứ hạng tối đa (Top N)", 1, max_rank, 50)
    df_display = df_display[df_display["rank"] <= rank_limit]

col5, col6, col7, col8 = st.columns(4)

if "artist" in df_display.columns:
    artists = sorted(df_display["artist"].dropna().unique())
    selected_artists = col5.multiselect("🎤 Nghệ sĩ", artists)
    if selected_artists:
        df_display = df_display[df_display["artist"].isin(selected_artists)]

if "title" in df_display.columns:
    song_keyword = col6.text_input("🎵 Tìm bài hát (từ khóa)")
    if song_keyword:
        df_display = df_display[df_display["title"].str.contains(song_keyword, case=False, na=False)]

if "is_new" in df_display.columns:
    new_opt = col7.radio("🆕 Bài mới", ["Tất cả", "Chỉ bài mới", "Bài cũ"], horizontal=True)
    if new_opt == "Chỉ bài mới":
        df_display = df_display[df_display["is_new"] == 1]
    elif new_opt == "Bài cũ":
        df_display = df_display[df_display["is_new"] == 0]

if "is_collab" in df_display.columns:
    collab_opt = col8.radio("🤝 Hợp tác", ["Tất cả", "Chỉ collab", "Solo"], horizontal=True)
    if collab_opt == "Chỉ collab":
        df_display = df_display[df_display["is_collab"] == 1]
    elif collab_opt == "Solo":
        df_display = df_display[df_display["is_collab"] == 0]

col9, col10, col11, col12 = st.columns(4)
for col, feature in zip([col9, col10, col11, col12], ["energy", "danceability", "valence", "tempo"]):
    if feature in df_display.columns:
        min_f, max_f = float(df_display[feature].min()), float(df_display[feature].max())
        range_f = col.slider(f"🎚️ {feature.title()}", min_f, max_f, (min_f, max_f))
        df_display = df_display[
            (df_display[feature] >= range_f[0]) & (df_display[feature] <= range_f[1])
        ]

if df_display.empty:
    st.warning("⚠️ Không có bản ghi nào khớp với bộ lọc hiện tại.")
else:
    st.dataframe(
        df_display[show_cols].sort_values(["week", "rank"]),
        use_container_width=True,
        hide_index=True,
    )

colA, colB = st.columns([1, 4])
with colA:
    if st.button("🔄 Reset Bộ Lọc"):
        st.experimental_rerun()
with colB:
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Tải dữ liệu lọc (CSV)",
        data=csv,
        file_name="billboard_usa_2025_filtered.csv",
        mime="text/csv"
    )

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("📊 Dữ liệu Billboard Hot 100 (2025) – MongoDB Atlas `spotify_project.top100_usa_2025`")
