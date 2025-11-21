import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import streamlit.components.v1 as components
import datetime

# -----------------------------
# 1️⃣ Cấu hình giao diện
# -----------------------------
st.set_page_config(page_title="Global Music Analytics", layout="wide")
st.title("🌍 Global Music Analytics – Spotify & Billboard Trends")
st.caption("Dữ liệu được phân tích từ MongoDB Atlas: Albums & Top 50 Global")

# -----------------------------
# 2️⃣ Kết nối MongoDB & Load Data
# -----------------------------
MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "spotify_project"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

client = init_connection()
db = client[DB_NAME]

@st.cache_data
def load_data():
    # Load Album Data
    album_df = pd.DataFrame(list(db["album_stats_global_2"].find()))
    # Load Single Data
    top50_df = pd.DataFrame(list(db["top50_world"].find()))

    # --- XỬ LÝ ALBUM DF ---
    if "Genre" not in album_df.columns and "genre" in album_df.columns:
        album_df.rename(columns={"genre": "Genre"}, inplace=True)
    
    # Xử lý ngày tháng cho Album
    if "Release Date" in album_df.columns:
        album_df["Release Date"] = pd.to_datetime(album_df["Release Date"], errors="coerce")
        album_df["Release Year"] = album_df["Release Date"].dt.year
    elif "releaseDate" in album_df.columns:
        album_df["Release Date"] = pd.to_datetime(album_df["releaseDate"], errors="coerce")
        album_df["Release Year"] = album_df["Release Date"].dt.year
    
    # Chuyển đổi số liệu
    cols_to_numeric = ["Total Streams (Millions)", "popularity", "energy", "danceability", 
                       "Monthly Listeners (Millions)", "Streams Last 30 Days (Millions)", "Skip Rate (%)", "valence", "acousticness"]
    for col in cols_to_numeric:
        if col in album_df.columns:
            album_df[col] = pd.to_numeric(album_df[col], errors="coerce")

    # --- XỬ LÝ TOP50 (SINGLE) DF ---
    if "date" in top50_df.columns:
        top50_df["date"] = pd.to_datetime(top50_df["date"], errors="coerce")
    
    # Xử lý cột số cho Top50
    top50_cols = ["popularity", "duration_ms", "energy", "valence", "danceability", "position", "acousticness", "loudness", "tempo"]
    for col in top50_cols:
        if col in top50_df.columns:
            top50_df[col] = pd.to_numeric(top50_df[col], errors="coerce")

    return album_df, top50_df

album_df_raw, top50_df_raw = load_data()

# -----------------------------
# 3️⃣ Hiệu ứng cuộn mượt (JS)
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
# 4️⃣ Bộ lọc thời gian & Logic Slider (Đã điều chỉnh)
# -----------------------------
st.markdown("### ⚙️ Cấu hình phân tích")

col_type, col_slider = st.columns([1, 3])

# 1. Chọn loại dữ liệu TRƯỚC để tính toán min/max date chính xác
with col_type:
    album_type_filter = st.selectbox(
        "🎵 Chọn loại dữ liệu:",
        ["Album", "Single"]
    )

# 2. Tính toán Min/Max Date dựa trên loại dữ liệu đã chọn
if album_type_filter == "Album":
    raw_dates = album_df_raw["Release Date"].dropna()
else:
    raw_dates = top50_df_raw["date"].dropna()

if not raw_dates.empty:
    min_date = raw_dates.min().to_pydatetime()
    max_date = raw_dates.max().to_pydatetime()
else:
    # Fallback nếu không có dữ liệu
    min_date = datetime.datetime(2020, 1, 1)
    max_date = datetime.datetime(2025, 12, 31)

# 3. Hiển thị Slider với giới hạn chính xác
with col_slider:
    start_date, end_date = st.slider(
        f"📆 Chọn khoảng thời gian ({album_type_filter}):",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="DD/MM/YYYY"
    )

# --- ÁP DỤNG BỘ LỌC ---
if album_type_filter == "Album":
    album_df = album_df_raw[
        (album_df_raw["Release Date"] >= pd.to_datetime(start_date)) & 
        (album_df_raw["Release Date"] <= pd.to_datetime(end_date))
    ].copy()
else:
    top50_df = top50_df_raw[
        (top50_df_raw["date"] >= pd.to_datetime(start_date)) & 
        (top50_df_raw["date"] <= pd.to_datetime(end_date))
    ].copy()

st.caption(f"Dữ liệu đang hiển thị từ **{start_date.strftime('%d/%m/%Y')}** đến **{end_date.strftime('%d/%m/%Y')}**")
st.markdown("---")

# -----------------------------
# 5️⃣ Phân tích chi tiết
# -----------------------------

if album_type_filter == "Album":
    # --- MỤC LỤC ALBUM ---
    st.markdown("""
    ### 🧭 **Mục lục (Albums)**
    - [📊 Tổng quan Thể loại & Tương quan](#section-genre)
    - [📅 Xu hướng theo Thời gian](#section-time)
    - [🌍 Phân tích Quốc gia](#section-country)
    - [🏷️ Hãng thu âm (Labels)](#section-label)
    - [💿 Top Albums & Hiệu suất](#section-top)
    """, unsafe_allow_html=True)
    st.markdown("---")

    # --- 1. GENRE & CORRELATION ---
    st.markdown('<a id="section-genre"></a>', unsafe_allow_html=True)
    st.subheader("📊 Phân tích Thể loại & Mối tương quan")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        genre_counts = album_df["Genre"].value_counts().head(10)
        fig = px.bar(
            x=genre_counts.index,
            y=genre_counts.values,
            labels={"x": "Thể loại", "y": "Số lượng album"},
            title="🎧 Top 10 thể loại phổ biến",
            color=genre_counts.index,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 🔥 NEW: Ma trận tương quan - Cái này có ý nghĩa để xem yếu tố nào ảnh hưởng Popularity
        st.markdown("**🔗 Yếu tố nào ảnh hưởng đến Popularity?**")
        corr_cols = ["popularity", "Total Streams (Millions)", "energy", "danceability", "Skip Rate (%)"]
        valid_corr = [c for c in corr_cols if c in album_df.columns]
        if len(valid_corr) > 1:
            corr = album_df[valid_corr].corr()
            fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", title="Ma trận tương quan")
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Chưa đủ dữ liệu số để vẽ ma trận tương quan.")

    # --- 2. TIME SERIES ---
    st.markdown('<a id="section-time"></a>', unsafe_allow_html=True)
    st.subheader("📅 Xu hướng theo Thời gian")
    
    col1, col2 = st.columns(2)
    with col1:
        fig_hist = px.histogram(
            album_df.dropna(subset=["Release Year"]),
            x="Release Year", nbins=20,
            title="Phân bố lượng Album theo năm phát hành",
            color_discrete_sequence=["#4C78A8"]
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        df_sorted = album_df.dropna(subset=["Release Date"]).sort_values("Release Date")
        # Dùng Scatter thay vì Line để đỡ bị rối nếu dữ liệu dày đặc
        fig_line = px.scatter(
            df_sorted,
            x="Release Date", y="popularity",
            title="Xu hướng độ phổ biến (Scatter Plot)",
            color="Genre",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- 3. COUNTRY ---
    st.markdown('<a id="section-country"></a>', unsafe_allow_html=True)
    st.subheader("🌍 Phân tích Quốc gia")
    
    country_metric = st.selectbox("Chọn chỉ số so sánh quốc gia:", 
                                  ["Số lượng album", "Popularity", "Total Streams (Millions)"], 
                                  key="country_select")
    
    if country_metric == "Số lượng album":
        country_counts = album_df["Country"].value_counts().head(10)
        fig_c = px.bar(x=country_counts.index, y=country_counts.values, 
                       title="Top 10 Quốc gia sản xuất nhiều Album nhất", color=country_counts.index)
        st.plotly_chart(fig_c, use_container_width=True)
    else:
        metric_map = {"Popularity": "popularity", "Total Streams (Millions)": "Total Streams (Millions)"}
        y_col = metric_map[country_metric]
        fig_c = px.box(album_df, x="Country", y=y_col, title=f"Phân bố {country_metric} theo Quốc gia")
        st.plotly_chart(fig_c, use_container_width=True)

    # --- 4. LABEL ---
    st.markdown('<a id="section-label"></a>', unsafe_allow_html=True)
    st.subheader("🏷️ Phân tích Hãng thu âm (Labels)")
    label_counts = album_df["label"].value_counts().head(10)
    fig_label = px.bar(x=label_counts.index, y=label_counts.values, 
                       title="Top 10 Hãng thu âm", labels={"x": "Label", "y": "Count"})
    st.plotly_chart(fig_label, use_container_width=True)

    # --- 5. TOP ALBUMS & SCATTER INSIGHT ---
    st.markdown('<a id="section-top"></a>', unsafe_allow_html=True)
    st.subheader("💿 Top Albums & Hiệu suất")
    
    col_top1, col_top2 = st.columns(2)
    
    with col_top1:
        # Top Streams Bar Chart
        if "Total Streams (Millions)" in album_df.columns:
            top_streams = album_df.nlargest(10, "Total Streams (Millions)").sort_values("Total Streams (Millions)")
            fig_top = px.bar(top_streams, y="Album", x="Total Streams (Millions)", orientation="h",
                             title="Top 10 Album có lượt stream cao nhất", text="Artist", color="Total Streams (Millions)")
            st.plotly_chart(fig_top, use_container_width=True)
            
    with col_top2:
        # 🔥 NEW: Scatter Plot (Popularity vs Streams) - Insight: Album nào Popular cao nhưng Stream thấp? (Hype ảo)
        if "Total Streams (Millions)" in album_df.columns and "popularity" in album_df.columns:
            fig_scat = px.scatter(
                album_df, 
                x="popularity", 
                y="Total Streams (Millions)",
                hover_data=["Album", "Artist"],
                color="Genre",
                title="Mối quan hệ: Độ phổ biến vs Tổng lượt Stream",
                trendline="ols" # Thêm đường xu hướng
            )
            st.plotly_chart(fig_scat, use_container_width=True)

# =====================================================================
# PHẦN SINGLE
# =====================================================================
elif album_type_filter == "Single":
    df = top50_df
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    # --- MỤC LỤC SINGLE ---
    st.markdown("""
    ### 🧭 **Mục lục (Singles)**
    - [📈 Tổng quan & Bài mới](#section-overview)
    - [🎤 Đối đầu Nghệ sĩ (Head-to-Head)](#section-artist)
    - [🧠 DNA Bài hát (Radar Chart)](#section-features)
    - [🏆 Biến động Xếp hạng](#section-ranking)
    """, unsafe_allow_html=True)
    st.markdown("---")

    # --- 1. OVERVIEW ---
    st.markdown('<a id="section-overview"></a>', unsafe_allow_html=True)
    st.subheader("📈 Tổng quan & Bài hát mới")
    
    col1, col2 = st.columns(2)
    with col1:
        new_songs = df.sort_values(["song", "date"]).drop_duplicates(["song"], keep="first")
        new_weekly = new_songs.groupby("week").size().reset_index(name="new_entries")
        fig1 = px.line(new_weekly, x="week", y="new_entries", title="Số bài hát mới lọt Top 50 theo tuần", markers=True)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        song_counts = df["song"].value_counts().head(10)
        fig2 = px.bar(x=song_counts.index, y=song_counts.values, title="Top 10 bài hát trụ hạng lâu nhất", labels={"x":"Bài hát", "y":"Số tuần"})
        st.plotly_chart(fig2, use_container_width=True)

    # --- 2. ARTIST HEAD-TO-HEAD (MỚI & HỮU DỤNG) ---
    st.markdown('<a id="section-artist"></a>', unsafe_allow_html=True)
    st.subheader("🎤 Đối đầu Nghệ sĩ (Head-to-Head)")
    st.caption("Chọn 2 nghệ sĩ để so sánh trực tiếp hiệu suất của họ trong Top 50.")

    artist_list = sorted(df["artist"].dropna().unique())
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        art1 = st.selectbox("Chọn Nghệ sĩ 1", artist_list, index=0)
    with col_sel2:
        art2 = st.selectbox("Chọn Nghệ sĩ 2", artist_list, index=1 if len(artist_list) > 1 else 0)

    if art1 and art2:
        df1 = df[df["artist"] == art1]
        df2 = df[df["artist"] == art2]
        
        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"Số bài ({art1})", df1["song"].nunique())
        m2.metric(f"Số bài ({art2})", df2["song"].nunique())
        m3.metric(f"Rank TB ({art1})", f"{df1['position'].mean():.1f}")
        m4.metric(f"Rank TB ({art2})", f"{df2['position'].mean():.1f}")
        
        # Comparison Chart
        daily_rank1 = df1.groupby("date")["position"].mean().reset_index()
        daily_rank1["Artist"] = art1
        daily_rank2 = df2.groupby("date")["position"].mean().reset_index()
        daily_rank2["Artist"] = art2
        
        comp_df = pd.concat([daily_rank1, daily_rank2])
        fig_comp = px.line(comp_df, x="date", y="position", color="Artist", title="So sánh thứ hạng trung bình theo thời gian")
        fig_comp.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_comp, use_container_width=True)


    # --- 3. FEATURES & RADAR CHART (MỚI) ---
    st.markdown('<a id="section-features"></a>', unsafe_allow_html=True)
    st.subheader("🧠 Đặc trưng Âm nhạc & DNA Bài hát")
    
    col_f1, col_f2 = st.columns([1, 1])
    
    with col_f1:
        # Radar Chart - Rất hữu dụng để xem "hình dáng" âm nhạc
        features = ["energy", "danceability", "valence", "acousticness", "speechiness"]
        valid_feats = [f for f in features if f in df.columns]
        
        if valid_feats:
            avg_feats = df[valid_feats].mean().tolist()
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=avg_feats,
                theta=valid_feats,
                fill='toself',
                name='Trung bình Top 50'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                title="🕸️ Radar Chart: DNA trung bình của bài hát Top 50",
                showlegend=False
            )
            st.plotly_chart(fig_radar, use_container_width=True)
    
    with col_f2:
         # Correlation Heatmap cho Single
        st.markdown("**Mối liên hệ giữa Đặc trưng & Thứ hạng**")
        corr_cols_s = ["position", "popularity", "duration_ms", "energy", "danceability", "valence", "tempo"]
        valid_corr_s = [c for c in corr_cols_s if c in df.columns]
        if len(valid_corr_s) > 1:
            corr_s = df[valid_corr_s].corr()
            fig_corr_s = px.imshow(corr_s, text_auto=".2f", color_continuous_scale="RdBu", title="Ma trận tương quan")
            st.plotly_chart(fig_corr_s, use_container_width=True)

    # --- 4. RANKING ---
    st.markdown('<a id="section-ranking"></a>', unsafe_allow_html=True)
    st.subheader("🏆 Biến động Xếp hạng")
    
    selected_song = st.selectbox("Chọn bài hát để xem hành trình leo hạng:", sorted(df["song"].unique()))
    song_df = df[df["song"] == selected_song].sort_values("date")
    
    fig_rank = px.line(song_df, x="date", y="position", title=f"Thứ hạng của '{selected_song}'", markers=True)
    fig_rank.update_yaxes(autorange="reversed") # Đảo ngược trục Y vì hạng 1 nằm trên cùng
    st.plotly_chart(fig_rank, use_container_width=True)

# =====================================================================
# 📋 DỮ LIỆU GỐC (RAW DATA TABLE)
# =====================================================================
st.markdown("---")
st.subheader("📋 Dữ liệu Gốc & Bộ lọc chi tiết")
st.caption("Bảng dữ liệu dưới đây hỗ trợ lọc chi tiết và tải về CSV.")

# Xác định DF đang hiển thị để đưa vào bảng
if album_type_filter == "Album":
    df_display = album_df.copy()
    search_col = "Album"
    filter_cols = ["Genre", "Country", "label"]
else:
    df_display = top50_df.copy()
    search_col = "song"
    filter_cols = ["artist", "main_genre"]

# 1. Bộ lọc cột
col1, col2, col3 = st.columns(3)

with col1:
    keyword = st.text_input(f"🔍 Tìm kiếm theo {search_col}:")
    if keyword:
        df_display = df_display[df_display[search_col].astype(str).str.contains(keyword, case=False, na=False)]

with col2:
    # Lọc theo cột định tính đầu tiên có trong danh sách
    for col in filter_cols:
        if col in df_display.columns:
            options = sorted(df_display[col].dropna().unique())
            selected = st.multiselect(f"Lọc theo {col}:", options)
            if selected:
                df_display = df_display[df_display[col].isin(selected)]
            break # Chỉ hiện 1 filter chính ở đây cho gọn

with col3:
    # Lọc theo Popularity nếu có
    if "popularity" in df_display.columns:
        min_pop, max_pop = int(df_display["popularity"].min()), int(df_display["popularity"].max())
        pop_range = st.slider("Độ phổ biến (Popularity)", min_pop, max_pop, (min_pop, max_pop))
        df_display = df_display[
            (df_display["popularity"] >= pop_range[0]) & 
            (df_display["popularity"] <= pop_range[1])
        ]

# Hiển thị bảng
st.dataframe(df_display, use_container_width=True, height=400)

# Nút Download
csv = df_display.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Tải dữ liệu hiện tại (CSV)",
    data=csv,
    file_name=f"global_music_data_{album_type_filter.lower()}.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.markdown("Designed for **Global Music Analytics Dashboard** | 2025")






# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from pymongo import MongoClient
# import datetime

# # -----------------------------
# # 1️⃣ Cấu hình giao diện
# # -----------------------------
# st.set_page_config(
#     page_title="Global Music Analytics", 
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # CSS tùy chỉnh để làm đẹp Metric Card
# st.markdown("""
# <style>
#     div[data-testid="stMetric"] {
#         background-color: #f0f2f6;
#         padding: 10px;
#         border-radius: 10px;
#         border: 1px solid #e6e9ef;
#     }
#     div[data-testid="stMetricLabel"] {
#         color: #555;
#         font-weight: bold;
#     }
# </style>
# """, unsafe_allow_html=True)

# # -----------------------------
# # 2️⃣ Kết nối MongoDB & Load Data
# # -----------------------------
# MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# DB_NAME = "spotify_project"

# @st.cache_resource
# def init_connection():
#     return MongoClient(MONGO_URI)

# try:
#     client = init_connection()
#     db = client[DB_NAME]
# except Exception as e:
#     st.error(f"Lỗi kết nối MongoDB: {e}")
#     st.stop()

# @st.cache_data
# def load_data():
#     # Load Album Data
#     album_df = pd.DataFrame(list(db["album_stats_global_2"].find()))
#     # Load Single Data
#     top50_df = pd.DataFrame(list(db["top50_world"].find()))

#     # --- XỬ LÝ ALBUM DF ---
#     if "Genre" not in album_df.columns and "genre" in album_df.columns:
#         album_df.rename(columns={"genre": "Genre"}, inplace=True)
    
#     if "Release Date" in album_df.columns:
#         album_df["Release Date"] = pd.to_datetime(album_df["Release Date"], errors="coerce")
#         album_df["Release Year"] = album_df["Release Date"].dt.year
#     elif "releaseDate" in album_df.columns:
#         album_df["Release Date"] = pd.to_datetime(album_df["releaseDate"], errors="coerce")
#         album_df["Release Year"] = album_df["Release Date"].dt.year
    
#     cols_to_numeric = ["Total Streams (Millions)", "popularity", "energy", "danceability", 
#                        "Monthly Listeners (Millions)", "Streams Last 30 Days (Millions)", 
#                        "Skip Rate (%)", "valence", "acousticness"]
#     for col in cols_to_numeric:
#         if col in album_df.columns:
#             album_df[col] = pd.to_numeric(album_df[col], errors="coerce")

#     # --- XỬ LÝ TOP50 (SINGLE) DF ---
#     if "date" in top50_df.columns:
#         top50_df["date"] = pd.to_datetime(top50_df["date"], errors="coerce")
    
#     top50_cols = ["popularity", "duration_ms", "energy", "valence", "danceability", 
#                   "position", "acousticness", "loudness", "tempo"]
#     for col in top50_cols:
#         if col in top50_df.columns:
#             top50_df[col] = pd.to_numeric(top50_df[col], errors="coerce")

#     return album_df, top50_df

# album_df_raw, top50_df_raw = load_data()

# # -----------------------------
# # 3️⃣ SIDEBAR: BỘ LỌC TRUNG TÂM
# # -----------------------------
# with st.sidebar:
#     st.title("🎧 Control Panel")
#     st.markdown("---")
    
#     # Chọn loại dữ liệu
#     album_type_filter = st.radio(
#         "📊 Chọn nguồn dữ liệu:",
#         ["Album Analytics", "Top 50 Singles"],
#         index=0
#     )
    
#     st.markdown("---")
#     st.subheader("📆 Thời gian")
    
#     # Logic Slider
#     if album_type_filter == "Album Analytics":
#         raw_dates = album_df_raw["Release Date"].dropna()
#     else:
#         raw_dates = top50_df_raw["date"].dropna()

#     if not raw_dates.empty:
#         min_date, max_date = raw_dates.min().to_pydatetime(), raw_dates.max().to_pydatetime()
#     else:
#         min_date, max_date = datetime.datetime(2020, 1, 1), datetime.datetime(2025, 12, 31)

#     start_date, end_date = st.slider(
#         "Chọn khoảng thời gian:",
#         min_value=min_date, max_value=max_date,
#         value=(min_date, max_date),
#         format="DD/MM/YYYY"
#     )
    
#     st.caption(f"Filter: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
#     st.markdown("---")
#     st.info("Designed by Global Music Analytics Team")

# # --- ÁP DỤNG BỘ LỌC ---
# if album_type_filter == "Album Analytics":
#     main_df = album_df_raw[
#         (album_df_raw["Release Date"] >= pd.to_datetime(start_date)) & 
#         (album_df_raw["Release Date"] <= pd.to_datetime(end_date))
#     ].copy()
#     data_mode = "album"
# else:
#     main_df = top50_df_raw[
#         (top50_df_raw["date"] >= pd.to_datetime(start_date)) & 
#         (top50_df_raw["date"] <= pd.to_datetime(end_date))
#     ].copy()
#     data_mode = "single"

# # -----------------------------
# # 4️⃣ HEADER & KPI METRICS (QUAN TRỌNG)
# # -----------------------------
# st.title("🌍 Global Music Analytics Dashboard")
# st.markdown(f"Phân tích dữ liệu **{album_type_filter}** từ MongoDB Atlas.")

# # Hiển thị KPI Cards
# kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# if data_mode == "album":
#     total_streams = main_df["Total Streams (Millions)"].sum() if "Total Streams (Millions)" in main_df.columns else 0
#     top_artist = main_df["Artist"].mode()[0] if "Artist" in main_df.columns else "N/A"
#     avg_pop = main_df["popularity"].mean() if "popularity" in main_df.columns else 0
#     count_item = len(main_df)
    
#     kpi1.metric("💿 Tổng số Albums", f"{count_item:,}")
#     kpi2.metric("🎧 Tổng lượt Stream", f"{total_streams:,.0f} M")
#     kpi3.metric("🔥 Độ phổ biến TB", f"{avg_pop:.1f}/100")
#     kpi4.metric("👑 Nghệ sĩ năng suất nhất", top_artist)

# else: # Single
#     unique_songs = main_df["song"].nunique()
#     unique_artists = main_df["artist"].nunique()
#     avg_rank = main_df["position"].mean()
#     top_song = main_df["song"].mode()[0] if not main_df.empty else "N/A"
    
#     kpi1.metric("🎵 Số bài hát", unique_songs)
#     kpi2.metric("🎤 Số nghệ sĩ", unique_artists)
#     kpi3.metric("📉 Thứ hạng TB", f"{avg_rank:.1f}")
#     kpi4.metric("🌟 Bài hát trụ hạng lâu", top_song)

# st.markdown("---")

# # -----------------------------
# # 5️⃣ MAIN CONTENT TABS
# # -----------------------------

# tab1, tab2, tab3, tab4 = st.tabs([
#     "📈 Tổng quan Thị trường", 
#     "🏆 Xếp hạng & Nghệ sĩ", 
#     "🧠 Phân tích Chuyên sâu", 
#     "📋 Dữ liệu Chi tiết"
# ])

# # ==================================================
# # TAB 1: TỔNG QUAN THỊ TRƯỜNG (TRENDS & GENRE)
# # ==================================================
# with tab1:
#     st.subheader("📅 Xu hướng & Phân bố Thể loại")
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         if data_mode == "album":
#             df_sorted = main_df.dropna(subset=["Release Date"]).sort_values("Release Date")
#             fig_trend = px.scatter(df_sorted, x="Release Date", y="popularity", color="Genre",
#                                 title="Xu hướng Popularity theo thời gian", trendline="lowess")
#             st.plotly_chart(fig_trend, use_container_width=True)
#         else:
#             daily_counts = main_df.groupby("date")["song"].nunique().reset_index()
#             fig_trend = px.line(daily_counts, x="date", y="song", title="Số lượng bài hát trong Top 50 theo ngày")
#             st.plotly_chart(fig_trend, use_container_width=True)
            
#     with col2:
#         if data_mode == "album":
#             genre_col = "Genre"
#         else:
#             genre_col = "main_genre" if "main_genre" in main_df.columns else None
            
#         if genre_col and genre_col in main_df.columns:
#             cnt = main_df[genre_col].value_counts().head(10)
#             fig_pie = px.pie(names=cnt.index, values=cnt.values, title="Top 10 Thể loại phổ biến", hole=0.4)
#             st.plotly_chart(fig_pie, use_container_width=True)
#         else:
#             st.info("Không có dữ liệu thể loại.")

#     # Biểu đồ phân bố
#     st.markdown("#### Phân bố chỉ số năng lượng (Energy) & Cảm xúc (Valence)")
#     c1, c2 = st.columns(2)
#     with c1:
#         if "energy" in main_df.columns:
#             st.plotly_chart(px.histogram(main_df, x="energy", title="Phân bố Energy", nbins=30), use_container_width=True)
#     with c2:
#         if "valence" in main_df.columns:
#             st.plotly_chart(px.histogram(main_df, x="valence", title="Phân bố Valence (Độ tích cực)", nbins=30, color_discrete_sequence=['#FF7F0E']), use_container_width=True)


# # ==================================================
# # TAB 2: XẾP HẠNG & NGHỆ SĨ (TOP CHARTS)
# # ==================================================
# with tab2:
#     if data_mode == "album":
#         st.subheader("💿 Top Albums & Labels")
#         col_a, col_b = st.columns(2)
        
#         with col_a:
#             if "Total Streams (Millions)" in main_df.columns:
#                 top_st = main_df.nlargest(10, "Total Streams (Millions)").sort_values("Total Streams (Millions)")
#                 fig_bar = px.bar(top_st, y="Album", x="Total Streams (Millions)", orientation='h', 
#                                  title="Top 10 Album được Stream nhiều nhất", text="Artist")
#                 st.plotly_chart(fig_bar, use_container_width=True)
        
#         with col_b:
#             lbl_cnt = main_df["label"].value_counts().head(10)
#             fig_lbl = px.bar(x=lbl_cnt.index, y=lbl_cnt.values, title="Top 10 Hãng thu âm (Labels)", labels={'x':'Label', 'y':'Count'})
#             st.plotly_chart(fig_lbl, use_container_width=True)
            
#         st.markdown("#### 🌍 Bản đồ âm nhạc")
#         cnt_country = main_df["Country"].value_counts().head(15)
#         st.plotly_chart(px.bar(x=cnt_country.index, y=cnt_country.values, title="Quốc gia sản xuất Album nhiều nhất"), use_container_width=True)

#     else: # Single
#         st.subheader("🏆 Xếp hạng Bài hát & Nghệ sĩ")
        
#         # Top bài hát trụ hạng
#         song_stay = main_df["song"].value_counts().head(10)
#         st.plotly_chart(px.bar(x=song_stay.index, y=song_stay.values, title="Top 10 Bài hát xuất hiện nhiều nhất trong Top 50"), use_container_width=True)
        
#         # Hành trình leo hạng
#         st.markdown("#### 📈 Hành trình leo hạng")
#         selected_song = st.selectbox("Chọn bài hát để xem chi tiết:", sorted(main_df["song"].unique()))
#         if selected_song:
#             s_df = main_df[main_df["song"] == selected_song].sort_values("date")
#             fig_rank = px.line(s_df, x="date", y="position", title=f"Thứ hạng của '{selected_song}'", markers=True)
#             fig_rank.update_yaxes(autorange="reversed")
#             st.plotly_chart(fig_rank, use_container_width=True)


# # ==================================================
# # TAB 3: PHÂN TÍCH CHUYÊN SÂU (DEEP DIVE)
# # ==================================================
# with tab3:
#     st.subheader("🧠 Phân tích Đặc trưng & Tương quan")
    
#     col_deep1, col_deep2 = st.columns([1, 1])
    
#     with col_deep1:
#         st.markdown("**🕸️ DNA Âm nhạc (Radar Chart)**")
#         features = ["energy", "danceability", "valence", "acousticness", "speechiness", "liveness"]
#         valid_feats = [f for f in features if f in main_df.columns]
        
#         if valid_feats:
#             avg_vals = main_df[valid_feats].mean().tolist()
#             fig_radar = go.Figure(data=go.Scatterpolar(
#                 r=avg_vals, theta=valid_feats, fill='toself', name='Average'
#             ))
#             fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), title="Đặc tính trung bình")
#             st.plotly_chart(fig_radar, use_container_width=True)
            
#     with col_deep2:
#         st.markdown("**🔗 Ma trận Tương quan (Correlation)**")
#         if data_mode == "album":
#             corr_cols = ["popularity", "Total Streams (Millions)", "energy", "danceability", "Skip Rate (%)"]
#         else:
#             corr_cols = ["position", "popularity", "duration_ms", "energy", "danceability", "valence", "tempo"]
            
#         valid_corr = [c for c in corr_cols if c in main_df.columns]
#         if len(valid_corr) > 1:
#             corr = main_df[valid_corr].corr()
#             fig_hm = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", aspect="auto")
#             st.plotly_chart(fig_hm, use_container_width=True)

#     # Head to Head (Chỉ cho Single hoặc có thể chế cho Album nếu muốn)
#     if data_mode == "single":
#         st.markdown("---")
#         st.subheader("🥊 Đối đầu Nghệ sĩ (Head-to-Head)")
#         artists = sorted(main_df["artist"].dropna().unique())
#         ca, cb = st.columns(2)
#         art1 = ca.selectbox("Nghệ sĩ A", artists, index=0)
#         art2 = cb.selectbox("Nghệ sĩ B", artists, index=1 if len(artists)>1 else 0)
        
#         if art1 and art2:
#             d1 = main_df[main_df["artist"] == art1].groupby("date")["position"].mean().reset_index()
#             d1["Artist"] = art1
#             d2 = main_df[main_df["artist"] == art2].groupby("date")["position"].mean().reset_index()
#             d2["Artist"] = art2
#             comp = pd.concat([d1, d2])
            
#             fig_comp = px.line(comp, x="date", y="position", color="Artist", title="So sánh hạng trung bình hằng ngày")
#             fig_comp.update_yaxes(autorange="reversed")
#             st.plotly_chart(fig_comp, use_container_width=True)

# # ==================================================
# # TAB 4: DỮ LIỆU CHI TIẾT (DATA TABLE)
# # ==================================================
# with tab4:
#     st.subheader("📋 Bảng dữ liệu chi tiết")
    
#     # Search & Filter Tool
#     c_search, c_down = st.columns([3, 1])
#     with c_search:
#         search_term = st.text_input("🔍 Tìm kiếm (Tên bài hát / Album / Nghệ sĩ):")
    
#     display_df = main_df.copy()
    
#     if search_term:
#         # Tìm trên các cột dạng chuỗi
#         mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
#         display_df = display_df[mask]
    
#     st.dataframe(display_df, use_container_width=True, height=500)
    
#     with c_down:
#         csv = display_df.to_csv(index=False).encode('utf-8')
#         st.download_button(
#             label="📥 Tải xuống CSV",
#             data=csv,
#             file_name=f"music_data_{data_mode}.csv",
#             mime="text/csv",
#             use_container_width=True
#         )