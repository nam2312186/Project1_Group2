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
st.set_page_config(page_title="Global Music Analytics", layout="wide", page_icon="🌍")
st.title("🌍 Global Music Analytics – Spotify Trends")
st.markdown("*Phân tích dữ liệu chuyên sâu từ MongoDB Atlas*")

# -----------------------------
# 2️⃣ Kết nối MongoDB & Load Data
# -----------------------------
MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "spotify_project"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client[DB_NAME]
except Exception as e:
    st.error(f"❌ Lỗi kết nối MongoDB: {e}")
    st.stop()

@st.cache_data
def load_data():
    # --- 1. LOAD ALBUM DATA ---
    try:
        album_data = list(db["album_stats_global_2"].find())
        album_df = pd.DataFrame(album_data)
        
        if not album_df.empty:
            # Xử lý ngày tháng: releaseDate -> Release Date
            if "releaseDate" in album_df.columns:
                album_df["Release Date"] = pd.to_datetime(album_df["releaseDate"], errors="coerce")
                album_df["Release Year"] = album_df["Release Date"].dt.year
            elif "Release Date" in album_df.columns:
                album_df["Release Date"] = pd.to_datetime(album_df["Release Date"], errors="coerce")
                album_df["Release Year"] = album_df["Release Date"].dt.year

            # Đổi tên cột genre cho thống nhất nếu cần
            if "Genre" not in album_df.columns and "genre" in album_df.columns:
                album_df.rename(columns={"genre": "Genre"}, inplace=True)

            # Xử lý số liệu
            cols_to_num = [
                "Total Streams (Millions)", "Monthly Listeners (Millions)", 
                "Streams Last 30 Days (Millions)", "Skip Rate (%)", 
                "popularity", "totalTracks", "Avg Stream Duration (Min)",
                "energy", "danceability", "valence", "acousticness" 
            ]
            for col in cols_to_num:
                if col in album_df.columns:
                    album_df[col] = pd.to_numeric(album_df[col], errors="coerce").fillna(0)
    except Exception as e:
        st.error(f"Lỗi load Album: {e}")
        album_df = pd.DataFrame()

    # --- 2. LOAD SINGLE DATA ---
    try:
        single_data = list(db["top50_world"].find())
        top50_df = pd.DataFrame(single_data)
        
        if not top50_df.empty:
            # Xử lý ngày tháng (date)
            if "date" in top50_df.columns:
                top50_df["date"] = pd.to_datetime(top50_df["date"], errors="coerce")
            
            # Xử lý Audio Features & Stats
            audio_feats = [
                "acousticness", "danceability", "energy", "instrumentalness", 
                "liveness", "loudness", "speechiness", "tempo", "valence", 
                "popularity", "position", "duration_ms"
            ]
            for col in audio_feats:
                if col in top50_df.columns:
                    top50_df[col] = pd.to_numeric(top50_df[col], errors="coerce")
            
            # Chuyển duration ra phút
            if "duration_ms" in top50_df.columns:
                top50_df["duration_min"] = top50_df["duration_ms"] / 60000
    except Exception as e:
        st.error(f"Lỗi load Single: {e}")
        top50_df = pd.DataFrame()

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
# 4️⃣ Bộ lọc thời gian & Slider
# -----------------------------
st.markdown("### ⚙️ Cấu hình phân tích")

col_type, col_slider = st.columns([1, 3])

# 1. Chọn loại dữ liệu
with col_type:
    data_type = st.selectbox(
        "🎵 Chọn loại dữ liệu:",
        ["Album", "Single"]
    )

# 2. Tính toán Min/Max Date để setup cho Slider
if data_type == "Album":
    raw_dates = album_df_raw["Release Date"].dropna()
    df_original = album_df_raw
    date_col_name = "Release Date"
else:
    raw_dates = top50_df_raw["date"].dropna()
    df_original = top50_df_raw
    date_col_name = "date"

# Xác định giới hạn slider
if not raw_dates.empty:
    min_date = raw_dates.min().to_pydatetime()
    max_date = raw_dates.max().to_pydatetime()
else:
    min_date = datetime.datetime(2020, 1, 1)
    max_date = datetime.datetime(2025, 12, 31)

# 3. Hiển thị Slider Kéo Thả
with col_slider:
    start_date, end_date = st.slider(
        f"📆 Chọn khoảng thời gian ({data_type}):",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="DD/MM/YYYY"
    )

# --- ÁP DỤNG BỘ LỌC CHÍNH XÁC ---
s_date = pd.to_datetime(start_date)
e_date = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

mask = (df_original[date_col_name] >= s_date) & (df_original[date_col_name] <= e_date)
df = df_original.loc[mask].copy()

st.caption(f"Đang hiển thị **{len(df)}** bản ghi từ **{start_date.strftime('%d/%m/%Y')}** đến **{end_date.strftime('%d/%m/%Y')}**")
st.markdown("---")

# -----------------------------
# 5️⃣ MAIN DASHBOARD
# -----------------------------

if data_type == "Album":
    tab_titles = ["📊 Tổng Quan", "🎤 Phân Tích Nghệ Sĩ", "🌍 Quốc Gia & Thị Trường", "🕒 Chuỗi Thời Gian", "🧩 Insights Khác"]
    tabs = st.tabs(tab_titles)
    t_overview, t_artist, t_country, t_time, t_insight = tabs
else: # Single
    tab_titles = ["📊 Tổng Quan", "🎚️ Audio Features", "🎤 Phân Tích Nghệ Sĩ", "🕒 Chuỗi Thời Gian", "🧩 Insights Khác"]
    tabs = st.tabs(tab_titles)
    t_overview, t_features, t_artist, t_time, t_insight = tabs

# ==============================================================================
# TAB 1: TỔNG QUAN (OVERVIEW)
# ==============================================================================
with t_overview:
    st.subheader(f"📊 Tổng quan thị trường ({data_type})")
    
    col1, col2, col3, col4 = st.columns(4)
    
    if data_type == "Album":
        # ... (Phần tính toán metrics tổng ở trên giữ nguyên) ...
        # total_streams = ...
        # col1.metric(...)
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        
        # --- SỬA LẠI PHẦN BIỂU ĐỒ TOP 10 ---
        with c1:
            # BƯỚC 1: GOM NHÓM VÀ TÍNH TỔNG (AGGREGATE)
            # Gom theo Tên Album và Nghệ sĩ -> Tính tổng Stream
            if "Total Streams (Millions)" in df.columns and "Album" in df.columns:
                album_rank = df.groupby(["Album", "Artist"]).agg({
                    "Total Streams (Millions)": "sum"
                }).reset_index()
                
                # BƯỚC 2: LẤY TOP 10
                top_10_grouped = album_rank.nlargest(10, "Total Streams (Millions)").sort_values("Total Streams (Millions)", ascending=True)
                
                # BƯỚC 3: VẼ BIỂU ĐỒ
                fig_top = px.bar(
                    top_10_grouped, 
                    x="Total Streams (Millions)", 
                    y="Album", 
                    orientation='h', 
                    title="🏆 Top 10 Album có lượt Stream cao nhất (Tổng hợp)", 
                    text="Total Streams (Millions)", # Hiển thị số liệu tổng
                    color="Total Streams (Millions)",
                    color_continuous_scale="Viridis", # Hoặc màu bạn thích
                    labels={"Total Streams (Millions)": "Tổng Stream (Triệu)", "Album": ""}
                )
                
                # Tinh chỉnh hiển thị: Số liệu nằm bên ngoài cột cho dễ nhìn
                fig_top.update_traces(texttemplate='%{text:.3s}', textposition='outside') 
                fig_top.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.warning("Thiếu dữ liệu để xếp hạng.")
            
            
        with c2:
            if "Platform Type" in df.columns:
                fig_pie = px.pie(df, names="Platform Type", title="💿 Tỷ lệ nền tảng (Free vs Premium)", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

    else: # Single
        # --- LOGIC TÍNH TOÁN KPI MỚI (ĐÃ LỌC UNKNOWN) ---
        if not df.empty:
            # 1. Tìm Nghệ sĩ thống trị
            top_artist = df["artist"].mode()[0] if "artist" in df.columns else "N/A"
            art_count = df[df["artist"] == top_artist].shape[0]
            
            # 2. Tìm Thể loại chủ đạo (LỌC BỎ UNKNOWN)
            if "main_genre" in df.columns:
                # Tạo bản sao lọc bỏ unknown để tính toán
                df_genre_clean = df[df["main_genre"].astype(str).str.lower() != "unknown"]
                if not df_genre_clean.empty:
                    top_genre = df_genre_clean["main_genre"].mode()[0]
                else:
                    top_genre = "N/A (All Unknown)"
            else:
                top_genre = "N/A"
            
            # 3. Bài hát Top 1
            top_song = df["song"].mode()[0] if "song" in df.columns else "N/A"
        else:
            top_artist, top_genre, top_song = "N/A", "N/A", "N/A"
            art_count = 0

        # Hiển thị Metrics
        col1.metric("📚 Tổng bản ghi", f"{len(df):,}")
        col2.metric("👑 Nghệ sĩ thống trị", top_artist, delta=f"{art_count} lần lọt top")
        col3.metric("🎹 Thể loại chủ đạo", top_genre, help="Đã loại bỏ 'unknown'")
        col4.metric("🔥 Bài hát Top 1", top_song)
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            # Top bài hát trụ hạng lâu nhất
            if not df.empty:
                longevity = df.groupby(["song", "artist"]).size().reset_index(name="days_on_chart")
                top_long = longevity.nlargest(10, "days_on_chart")
                fig_long = px.bar(top_long, x="days_on_chart", y="song", orientation='h', 
                                  title="⏳ Top bài hát trụ hạng lâu nhất (Số ngày)", 
                                  text="artist", 
                                  color="days_on_chart",
                                  color_continuous_scale="Viridis")
                fig_long.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_long, use_container_width=True)
        
        with c2:
             # Phân bố Main Genre (LỌC BỎ UNKNOWN CHO BIỂU ĐỒ)
            if "main_genre" in df.columns:
                # Lọc dữ liệu chỉ cho biểu đồ này
                df_chart_genre = df[df["main_genre"].astype(str).str.lower() != "unknown"]
                
                if not df_chart_genre.empty:
                    genre_counts = df_chart_genre["main_genre"].value_counts().head(10)
                    fig_g = px.bar(x=genre_counts.index, y=genre_counts.values, 
                                   title="🎵 Top Thể loại nhạc đang thịnh hành (Đã lọc unknown)",
                                   labels={'x': 'Thể loại', 'y': 'Số lượng'},
                                   color=genre_counts.values,
                                   color_continuous_scale="Turbo")
                    st.plotly_chart(fig_g, use_container_width=True)
                else:
                    st.warning("Không có dữ liệu thể loại hợp lệ (tất cả đều là unknown).")
                
        # --- Ranking Section ---
        st.markdown("---")
        st.subheader("🏆 Biến động Xếp hạng")
        if not df.empty:
            selected_song = st.selectbox("Chọn bài hát để xem hành trình leo hạng:", sorted(df["song"].unique()))
            song_df = df[df["song"] == selected_song].sort_values("date")
            
            fig_rank = px.line(song_df, x="date", y="position", title=f"Thứ hạng của '{selected_song}'", markers=True)
            fig_rank.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_rank, use_container_width=True)

# ==============================================================================
# TAB: AUDIO FEATURES (UPDATED: GENRE FINGERPRINTS & DURATION)
# ==============================================================================
if data_type == "Single":
    with t_features:
        st.subheader("🎚️ Phân tích Đặc tính Âm thanh (Audio DNA)")
        
        features_list = ["danceability", "energy", "valence", "acousticness", "speechiness", "liveness"]
        
        # --- PHẦN 1: RADAR CHART (SO SÁNH) & CORRELATION ---
        c1, c2 = st.columns([1, 1])
        
        with c1:
            if not df.empty:
                avg_selected = df[features_list].mean().tolist()
                avg_global = df_original[features_list].mean().tolist()
                
                fig_radar = go.Figure()
                # Lớp nền
                fig_radar.add_trace(go.Scatterpolar(
                    r=avg_global, theta=features_list, fill='toself',
                    name='TB Toàn bộ', line_color='gray', opacity=0.3,
                    hoverinfo='text', text=[f"Global: {x:.2f}" for x in avg_global]
                ))
                # Lớp chính
                fig_radar.add_trace(go.Scatterpolar(
                    r=avg_selected, theta=features_list, fill='toself',
                    name='Giai đoạn chọn', line_color='#1DB954', opacity=0.8,
                    hoverinfo='text', text=[f"Select: {x:.2f}" for x in avg_selected]
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    title="🕸️ Radar Chart: So sánh đặc tính",
                    legend=dict(y=-0.1, orientation="h"),
                    margin=dict(t=40, b=20)
                )
                st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_{start_date}")
            else:
                st.warning("⚠️ Không có dữ liệu.")
        
        with c2:
            if not df.empty:
                corr_cols = features_list + ["popularity", "tempo"]
                corr = df[corr_cols].corr()
                fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", 
                                     title="🔗 Ma trận tương quan")
                st.plotly_chart(fig_corr, use_container_width=True, key=f"corr_{start_date}")

        st.markdown("---")

        # --- PHẦN 2: GENRE FINGERPRINTS (LỌC BỎ UNKNOWN) ---
        st.subheader("🧬 Hồ sơ Âm nhạc theo Thể loại (Genre Fingerprints)")
        st.caption("So sánh sự khác biệt về đặc tính âm thanh giữa các dòng nhạc đang thịnh hành.")
        
        if not df.empty and "main_genre" in df.columns:
            col_g1, col_g2 = st.columns([1, 3])
            with col_g1:
                feat_compare = st.selectbox(
                    "So sánh chỉ số nào?", 
                    ["danceability", "energy", "valence", "acousticness", "speechiness"],
                    index=1
                )
            
            with col_g2:
                # Tạo DF sạch không có unknown để vẽ biểu đồ
                df_genre_clean_viz = df[df["main_genre"].astype(str).str.lower() != "unknown"]
                
                if not df_genre_clean_viz.empty:
                    # Lọc top 10 thể loại phổ biến (sau khi đã bỏ unknown)
                    top_genres_list = df_genre_clean_viz["main_genre"].value_counts().head(10).index.tolist()
                    df_genre_filtered = df_genre_clean_viz[df_genre_clean_viz["main_genre"].isin(top_genres_list)]
                    
                    fig_box = px.box(
                        df_genre_filtered, 
                        x="main_genre", 
                        y=feat_compare, 
                        color="main_genre",
                        title=f"Phân phối {feat_compare.capitalize()} giữa Top 10 Thể loại (Đã lọc unknown)",
                        points="outliers"
                    )
                    fig_box.update_layout(showlegend=False, xaxis_title="Thể loại", yaxis_title=feat_compare.capitalize())
                    st.plotly_chart(fig_box, use_container_width=True, key=f"genre_box_{start_date}")
                else:
                    st.warning("Không đủ dữ liệu thể loại hợp lệ để vẽ biểu đồ.")
                
            st.info(f"💡 **Insight:** Biểu đồ này cho biết 'chất' riêng của từng dòng nhạc.")
        else:
            st.warning("Chưa đủ dữ liệu thể loại để phân tích.")

        st.markdown("---")

        # --- PHẦN 3: DURATION TRENDS ---
        st.subheader("⏱️ Hiệu ứng TikTok: Xu hướng Thời lượng bài hát")
        st.caption("Phân tích độ dài bài hát để xem xu hướng Short-form content.")
        
        if not df.empty and "duration_ms" in df.columns:
            # Tạo cột phút
            df["duration_min_val"] = df["duration_ms"] / 60000
            
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                fig_dur = px.histogram(
                    df, 
                    x="duration_min_val", 
                    nbins=20,
                    title="Phân bố độ dài bài hát (Phút)",
                    color_discrete_sequence=["#FF6F61"],
                    labels={"duration_min_val": "Thời lượng (Phút)"}
                )
                avg_dur = df["duration_min_val"].mean()
                fig_dur.add_vline(x=avg_dur, line_dash="dash", line_color="white", annotation_text=f"TB: {avg_dur:.2f}p")
                st.plotly_chart(fig_dur, use_container_width=True, key=f"dur_hist_{start_date}")
                
            with col_d2:
                # --- GIẢI PHÁP MỚI: BIỂU ĐỒ CỘT PHÂN NHÓM (Bar Chart by Bins) ---
                
                # 1. Tạo các nhóm thời lượng (Bins)
                # Định nghĩa các mốc: <2.5p, 2.5-3.0p, 3.0-3.5p, 3.5-4.0p, >4.0p
                bins = [0, 2.5, 3.0, 3.5, 4.0, 100]
                labels = ['Rất ngắn (<2.5p)', 'Ngắn (2.5-3p)', 'Chuẩn (3-3.5p)', 'Hơi dài (3.5-4p)', 'Dài (>4p)']
                
                # Tạo cột phân nhóm mới
                df_dur_viz = df.copy()
                df_dur_viz['duration_group'] = pd.cut(df_dur_viz['duration_min_val'], bins=bins, labels=labels)
                
                # 2. Tính toán độ phổ biến trung bình cho từng nhóm
                # Gom nhóm theo 'duration_group' và tính trung bình cột 'popularity'
                df_grouped = df_dur_viz.groupby('duration_group', observed=False)['popularity'].mean().reset_index()
                
                # Làm tròn số cho đẹp
                df_grouped['popularity'] = df_grouped['popularity'].round(1)

                # 3. Vẽ biểu đồ
                fig_dur_pop = px.bar(
                    df_grouped,
                    x="duration_group",
                    y="popularity",
                    text="popularity", # Hiển thị số trên cột
                    title="Tương quan: Độ dài vs Độ phổ biến TB",
                    labels={"duration_group": "Nhóm thời lượng", "popularity": "Độ phổ biến TB"},
                    color="popularity",
                    color_continuous_scale="Viridis"
                )
                
                fig_dur_pop.update_traces(textposition='outside') # Đưa số lên đầu cột cho dễ nhìn
                fig_dur_pop.update_layout(yaxis_range=[df_grouped['popularity'].min() - 5, 100]) # Zoom vào phần chênh lệch
                
                st.plotly_chart(fig_dur_pop, use_container_width=True, key=f"dur_bar_{start_date}")
            
            short_songs = df[df["duration_min_val"] < 3].shape[0]
            percent_short = (short_songs / len(df)) * 100
            st.metric("Tỷ lệ bài hát dưới 3 phút", f"{percent_short:.1f}%", delta="Trend nhạc ngắn")

# ==============================================================================
# TAB: ARTIST ANALYSIS
# ==============================================================================
artist_tab = t_artist 
# ==============================================================================
# TAB: ARTIST ANALYSIS (NÂNG CẤP)
# ==============================================================================
# ==============================================================================
# TAB: ARTIST ANALYSIS (ĐÃ SỬA LỖI GỘP TÊN & BẢNG TRỐNG)
# ==============================================================================
# ==============================================================================
# TAB: ARTIST ANALYSIS (HYBRID: HỖ TRỢ CẢ SINGLE & ALBUM)
# ==============================================================================
with t_artist:
    sub_t1, sub_t2 = st.tabs(["👤 Hồ sơ", "⚔️ So sánh"])
    
    # --- 1. CẤU HÌNH ĐỘNG (DYNAMIC CONFIG) ---
    # Tự động phát hiện loại dữ liệu để gán tên cột tương ứng
    if "song" in df.columns: 
        # CHẾ ĐỘ SINGLE
        mode = "Single"
        col_art = "artist"
        col_item = "song"
        col_date = "date"
        col_metric = "popularity"
        lbl_metric = "Popularity"
    elif "Album" in df.columns: 
        # CHẾ ĐỘ ALBUM
        mode = "Album"
        col_art = "Artist" # Lưu ý viết hoa chữ A trong ảnh Album
        col_item = "Album"
        col_date = "releaseDate"
        col_metric = "Total Streams (Millions)"
        lbl_metric = "Tổng Stream (Triệu)"
    else:
        st.error("Dữ liệu không khớp chuẩn Single hoặc Album.")
        st.stop()

    # --- HÀM HỖ TRỢ ---
    def get_individual_artists(df_in, c_art):
        if c_art not in df_in.columns: return []
        raw = df_in[c_art].dropna().astype(str).unique()
        res = set()
        for x in raw:
            # Tách tên (feat, &, x)
            clean = x.replace(" & ", ",").replace(" feat. ", ",").replace(" ft. ", ",").replace(" x ", ",")
            res.update([p.strip() for p in clean.split(",")])
        return sorted(list(res))

    def filter_artist_hybrid(df_in, c_art, target):
        if c_art not in df_in.columns: return pd.DataFrame()
        def check(val):
            if not isinstance(val, str): return False
            clean = val.replace(" & ", ",").replace(" feat. ", ",").replace(" ft. ", ",").replace(" x ", ",")
            return target in [p.strip() for p in clean.split(",")]
        return df_in[df_in[c_art].apply(check)]

    # ==========================================================================
    # SUB-TAB 1: HỒ SƠ CHUYÊN SÂU
    # ==========================================================================
    with sub_t1:
        st.subheader("👤 Hồ sơ năng lực Nghệ sĩ")
        
        if not df.empty:
            # 1. Chọn Nghệ sĩ
            artists_list = get_individual_artists(df, col_art)
            selected_artist = st.selectbox("🔍 Chọn nghệ sĩ:", artists_list)
            
            # 2. Lọc dữ liệu
            art_df = filter_artist_hybrid(df, col_art, selected_artist)
            
            # 3. KPI (Hiển thị khác nhau tùy chế độ)
            k1, k2, k3, k4 = st.columns(4)
            
            # K1: Số lượng (Chung)
            uniq_count = art_df[col_item].nunique()
            k1.metric(f"Số lượng {col_item}", uniq_count)
            
            # K2, K3, K4: Riêng biệt
            if mode == "Single":
                # --- KPI CHO SINGLE ---
                avg_pop = art_df['popularity'].mean()
                k2.metric("Popularity TB", f"{avg_pop:.1f}")
                
                best_rank = art_df['position'].min() if 'position' in art_df.columns else "-"
                k3.metric("Thứ hạng tốt nhất", best_rank)
                
                if 'main_genre' in art_df.columns:
                    # Lọc unknown
                    valid_g = art_df[art_df['main_genre'].astype(str).str.lower() != 'unknown']['main_genre']
                    top_g = valid_g.mode()[0] if not valid_g.empty else "N/A"
                    k4.metric("Dòng nhạc", top_g)
                else:
                    k4.metric("Dòng nhạc", "N/A")
                    
            else: # Album
                # --- KPI CHO ALBUM ---
                total_str = art_df['Total Streams (Millions)'].sum()
                k2.metric("Tổng Stream", f"{total_str:,.0f} M")
                
                avg_pop = art_df['popularity'].mean() if 'popularity' in art_df.columns else 0
                k3.metric("Popularity TB", f"{avg_pop:.1f}")
                
                if 'label' in art_df.columns:
                    k4.metric("Hãng đĩa (Label)", art_df['label'].mode()[0] if not art_df['label'].empty else "-")
                else:
                    k4.metric("Genre", art_df['Genre'].mode()[0] if 'Genre' in art_df.columns else "-")

            st.markdown("---")

            # 4. BIỂU ĐỒ
# 4. BIỂU ĐỒ (LOGIC MỚI: TÁCH RIÊNG SINGLE VÀ ALBUM)
            c_chart1, c_chart2 = st.columns([1, 1])

# === TRƯỜNG HỢP A: CHẾ ĐỘ ALBUM (PHÂN TÍCH ĐỊA LÝ/QUỐC GIA) ===
            if mode == "Album":
                # Kiểm tra xem trong dữ liệu có cột Quốc gia không
                if "Country" in art_df.columns:
                    
                    # --- BƯỚC 1: XỬ LÝ DỮ LIỆU THEO QUỐC GIA ---
                    # Gom nhóm theo Quốc gia để tính tổng Stream và trung bình các chỉ số khác
                    country_stats = art_df.groupby("Country").agg({
                        "Total Streams (Millions)": "sum",
                        "popularity": "mean",
                        "Skip Rate (%)": "mean",
                        "Monthly Listeners (Millions)": "sum" # Hoặc max tùy logic dữ liệu của bạn
                    }).reset_index()
                    
                    # Lấy tên Album đang xét (Giả sử chỉ có 1 album chính)
                    current_album_name = art_df["Album"].mode()[0] if "Album" in art_df.columns else "Album"

                    # --- BƯỚC 2: VẼ BIỂU ĐỒ ---
                    c_chart1, c_chart2 = st.columns([1.5, 1]) # Chia cột bên trái rộng hơn cho Bản đồ
                    
                    # CỘT TRÁI: BẢN ĐỒ NHIỆT ĐỘ PHỦ SÓNG (CHOROPLETH MAP)
                    with c_chart1:
                        st.markdown(f"##### 🗺️ Độ phủ sóng toàn cầu: {current_album_name}")
                        
                        fig_map = px.choropleth(
                            country_stats,
                            locations="Country",
                            locationmode="country names", # Dùng tên quốc gia chuẩn tiếng Anh
                            color="Total Streams (Millions)",
                            hover_name="Country",
                            hover_data=["popularity", "Skip Rate (%)"],
                            color_continuous_scale="Plasma", # Màu rực rỡ cho đẹp
                            title=""
                        )
                        fig_map.update_layout(
                            geo=dict(showframe=False, showcoastlines=False, projection_type='equirectangular'),
                            margin=dict(t=0, b=0, l=0, r=0),
                            height=400
                        )
                        st.plotly_chart(fig_map, use_container_width=True)

                    # CỘT PHẢI: TOP THỊ TRƯỜNG TIÊU THỤ (BAR CHART)
                    with c_chart2:
                        st.markdown("##### 🏆 Top 10 Quốc gia nghe nhiều nhất")
                        
                        # Lấy Top 10 nước
                        top_countries = country_stats.nlargest(10, "Total Streams (Millions)").sort_values("Total Streams (Millions)", ascending=True)
                        
                        fig_bar_c = px.bar(
                            top_countries,
                            x="Total Streams (Millions)",
                            y="Country",
                            orientation='h',
                            text_auto='.1f',
                            color="popularity", # Màu sắc thể hiện độ phổ biến tại nước đó
                            color_continuous_scale="Viridis",
                            labels={"Total Streams (Millions)": "Tổng Stream (Triệu)", "Country": ""}
                        )
                        fig_bar_c.update_layout(showlegend=False, height=400, margin=dict(t=0, b=0))
                        st.plotly_chart(fig_bar_c, use_container_width=True)

                    st.markdown("---")
                    
                    # --- BIỂU ĐỒ PHỤ: CHẤT LƯỢNG THÍNH GIẢ (SCATTER PLOT) ---
                    st.markdown("##### 💎 Phân tích Chất lượng Thị trường (Stream vs Skip Rate)")
                    st.caption("Biểu đồ giúp xác định đâu là 'Thị trường Vàng' (Stream cao, Skip thấp) và thị trường khó tính.")
                    
                    fig_quality = px.scatter(
                        country_stats,
                        x="Total Streams (Millions)",
                        y="Skip Rate (%)",
                        size="Monthly Listeners (Millions)", # Bong bóng to = Nhiều người nghe
                        color="Country",
                        hover_name="Country",
                        text="Country",
                        title="",
                        labels={"Total Streams (Millions)": "Tổng Stream (Càng cao càng tốt)", "Skip Rate (%)": "Tỷ lệ Bỏ qua (Càng thấp càng tốt)"}
                    )
                    # Thêm đường trung bình để chia 4 góc phần tư
                    avg_stream = country_stats["Total Streams (Millions)"].mean()
                    avg_skip = country_stats["Skip Rate (%)"].mean()
                    
                    fig_quality.add_hline(y=avg_skip, line_dash="dash", line_color="gray", annotation_text="TB Skip Rate")
                    fig_quality.add_vline(x=avg_stream, line_dash="dash", line_color="gray", annotation_text="TB Stream")
                    
                    st.plotly_chart(fig_quality, use_container_width=True)

                else:
                    st.warning("⚠️ Dữ liệu không có cột 'Country' để phân tích địa lý.")

            # === TRƯỜNG HỢP B: CHẾ ĐỘ SINGLE (GIỮ NGUYÊN CODE CŨ CỦA BẠN) ===
            else: 
                # Cột Trái: Radar Chart (Audio Features)
                with c_chart1:
                    feats = ["danceability", "energy", "valence", "acousticness", "speechiness"]
                    avail = [f for f in feats if f in art_df.columns]
                    if avail:
                        v_art = art_df[avail].mean().tolist()
                        v_glo = df[avail].mean().tolist()
                        fig_r = go.Figure()
                        fig_r.add_trace(go.Scatterpolar(r=v_glo, theta=avail, fill='toself', name='Thị trường', opacity=0.3))
                        fig_r.add_trace(go.Scatterpolar(r=v_art, theta=avail, fill='toself', name=selected_artist, line_color='#1DB954'))
                        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), title=f"🧬 Audio DNA ({selected_artist})")
                        st.plotly_chart(fig_r, use_container_width=True)
                    else:
                        st.info("Không đủ dữ liệu Audio Features để vẽ Radar Chart.")

                # Cột Phải: Xu hướng leo hạng (Line Chart)
                with c_chart2:
                    if "date" in art_df.columns:
                        top_s = art_df.groupby("song")["popularity"].max().nlargest(5).index.tolist()
                        df_tr = art_df[art_df["song"].isin(top_s)].sort_values("date")
                        fig_l = px.line(df_tr, x="date", y="popularity", color="song", 
                                        title="📈 Xu hướng Top 5 bài hát", labels={"date":""})
                        fig_l.update_traces(mode='lines+markers')
                        st.plotly_chart(fig_l, use_container_width=True)
                    else:
                        st.info("Không có dữ liệu ngày tháng.")
            # 5. BẢNG CHI TIẾT (HYBRID)
            st.markdown(f"### 🎶 Danh sách {col_item} của {selected_artist}")
            
            if not art_df.empty:
                try:
                    # Cấu hình gom nhóm tùy loại
                    agg_rules = {}
                    
                    # Metric chính
                    if col_metric in art_df.columns: agg_rules[col_metric] = 'max' if mode == "Single" else 'sum' # Single lấy max pop, Album lấy sum (hoặc gốc)
                    if col_date in art_df.columns: agg_rules[col_date] = 'min'
                    if 'position' in art_df.columns: agg_rules['position'] = 'min'
                    
                    # Genre & Label
                    if mode == "Single" and 'main_genre' in art_df.columns:
                        def get_valid_g(s):
                            v = s[s.astype(str).str.lower() != 'unknown']
                            return v.iloc[0] if not v.empty else "unknown"
                        agg_rules['main_genre'] = get_valid_g
                    elif mode == "Album":
                        if 'Genre' in art_df.columns: agg_rules['Genre'] = 'first'
                        if 'label' in art_df.columns: agg_rules['label'] = 'first'
                        if 'totalTracks' in art_df.columns: agg_rules['totalTracks'] = 'max'
                    
                    # Group by
                    df_table = art_df.groupby(col_item).agg(agg_rules).reset_index()
                    
                    # Sort
                    if col_metric in df_table.columns:
                        df_table = df_table.sort_values(col_metric, ascending=False).head(15)
                    
                    # Rename columns cho đẹp
                    rename_map = {
                        col_item: "Tên Tác phẩm",
                        col_metric: lbl_metric,
                        col_date: "Ngày phát hành",
                        "position": "Best Rank",
                        "main_genre": "Thể loại",
                        "Genre": "Thể loại",
                        "label": "Hãng đĩa",
                        "totalTracks": "Số bài"
                    }
                    df_table = df_table.rename(columns=rename_map)
                    st.dataframe(df_table, use_container_width=True, hide_index=True)
                    
                except Exception as e:
                    st.error(f"Lỗi bảng: {e}")
                    st.dataframe(art_df.head(10))

 # ==========================================================================
    # SUB-TAB 2: SO SÁNH ĐỐI ĐẦU (BATTLE MODE - NÂNG CẤP)
    # ==========================================================================
    with sub_t2:
        st.subheader("⚔️So Sánh")
        
        if not df.empty:
            # Lấy danh sách nghệ sĩ
            all_ind = get_individual_artists(df, col_art)
            
            # Layout chọn nghệ sĩ
            row_select_1, row_select_2 = st.columns(2)
            with row_select_1:
                a1 = st.selectbox("🥊 Góc xanh (Challenger 1)", all_ind, index=0)
            with row_select_2:
                a2 = st.selectbox("🥊 Góc đỏ (Challenger 2)", all_ind, index=1 if len(all_ind)>1 else 0)
            
            if a1 != a2:
                # Lọc dữ liệu cho 2 nghệ sĩ
                d1 = filter_artist_hybrid(df, col_art, a1)
                d2 = filter_artist_hybrid(df, col_art, a2)
                
                # --- PHẦN 1: KPI ĐỐI ĐẦU (BIG NUMBERS) ---
                st.markdown(f"<h3 style='text-align: center;'> <span style='color:#1DB954'>{a1}</span> vs <span style='color:#E91E63'>{a2}</span> </h3>", unsafe_allow_html=True)
                st.markdown("---")

                # Tính toán các chỉ số
                # 1. Stream
                s1 = d1["Total Streams (Millions)"].sum() if "Total Streams (Millions)" in d1.columns else 0
                s2 = d2["Total Streams (Millions)"].sum() if "Total Streams (Millions)" in d2.columns else 0
                
                # 2. Monthly Listeners (Lấy max hoặc sum tùy logic, ở đây lấy Sum đại diện độ phủ)
                l1 = d1["Monthly Listeners (Millions)"].sum() if "Monthly Listeners (Millions)" in d1.columns else 0
                l2 = d2["Monthly Listeners (Millions)"].sum() if "Monthly Listeners (Millions)" in d2.columns else 0
                
                # 3. Popularity (Trung bình)
                p1 = d1["popularity"].mean() if "popularity" in d1.columns else 0
                p2 = d2["popularity"].mean() if "popularity" in d2.columns else 0
                
                # 4. Skip Rate (Trung bình - Càng thấp càng tốt)
                sk1 = d1["Skip Rate (%)"].mean() if "Skip Rate (%)" in d1.columns else 0
                sk2 = d2["Skip Rate (%)"].mean() if "Skip Rate (%)" in d2.columns else 0

                # 5. Duration
                dur1 = d1["Avg Stream Duration (Min)"].mean() if "Avg Stream Duration (Min)" in d1.columns else 0
                dur2 = d2["Avg Stream Duration (Min)"].mean() if "Avg Stream Duration (Min)" in d2.columns else 0

                # ... (Phần tính toán s1, s2, l1, l2... ở trên giữ nguyên) ...

                # --- CẤU HÌNH GIAO DIỆN SO SÁNH MỚI (KHÔNG MŨI TÊN) ---
                # Hàm hỗ trợ tạo giao diện số liệu đối kháng
                def battle_metric(label, v1, v2, unit="", lower_is_better=False):
                    color1 = "#1DB954" # Xanh (Spotify Green) cho A1
                    color2 = "#E91E63" # Hồng/Đỏ cho A2
                    
                    # Xác định ai thắng để bôi đậm (Optional)
                    is_v1_better = (v1 < v2) if lower_is_better else (v1 > v2)
                    weight1 = "bold" if is_v1_better else "normal"
                    weight2 = "bold" if not is_v1_better else "normal"
                    
                    # HTML Template
                    html = f"""
                    <div style="text-align: center; padding: 10px; background-color: #262730; border-radius: 10px; margin-bottom: 10px;">
                        <p style="font-size: 14px; margin-bottom: 5px; opacity: 0.8;">{label}</p>
                        <div style="display: flex; justify-content: center; align-items: baseline; gap: 10px;">
                            <span style="color: {color1}; font-size: 20px; font-weight: {weight1}">{v1}{unit}</span>
                            <span style="color: #888; font-size: 14px;">vs</span>
                            <span style="color: {color2}; font-size: 20px; font-weight: {weight2}">{v2}{unit}</span>
                        </div>
                    </div>
                    """
                    return html

                # Hiển thị 4 cột chỉ số (Sử dụng HTML thay cho st.metric)
                c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                
                with c_kpi1:
                    # Format số: 1,000 (thêm dấu phẩy)
                    v1_fmt = f"{s1:,.0f}"
                    v2_fmt = f"{s2:,.0f}"
                    st.markdown(battle_metric("TỔNG STREAM (Triệu)", v1_fmt, v2_fmt), unsafe_allow_html=True)
                
                with c_kpi2:
                    v1_fmt = f"{l1:,.0f}"
                    v2_fmt = f"{l2:,.0f}"
                    st.markdown(battle_metric("NGƯỜI NGHE (Triệu)", v1_fmt, v2_fmt), unsafe_allow_html=True)
                
                with c_kpi3:
                    # Skip Rate: Thấp hơn là tốt hơn -> bật cờ lower_is_better=True
                    v1_fmt = f"{sk1:.1f}"
                    v2_fmt = f"{sk2:.1f}"
                    st.markdown(battle_metric("TỶ LỆ SKIP (%)", v1_fmt, v2_fmt, "%", lower_is_better=True), unsafe_allow_html=True)
                
                with c_kpi4:
                    v1_fmt = f"{dur1:.2f}"
                    v2_fmt = f"{dur2:.2f}"
                    st.markdown(battle_metric("THỜI LƯỢNG (Phút)", v1_fmt, v2_fmt, "p"), unsafe_allow_html=True)

                st.markdown("---")
                
                # ... (Phần biểu đồ Radar và Chart bên dưới giữ nguyên) ...

                # --- PHẦN 2: BIỂU ĐỒ RADAR (SO SÁNH TOÀN DIỆN) ---
                col_radar, col_bar = st.columns([1, 1])

                with col_radar:
                    st.markdown("##### 🕸️ Biểu đồ Sức mạnh (Power Radar)")
                    # Chuẩn hóa dữ liệu về thang 0-1 để vẽ Radar (tránh việc Stream hàng nghìn đè bẹp Popularity hàng chục)
                    def normalize(v1, v2):
                        m = max(v1, v2)
                        if m == 0: return 0, 0
                        return v1/m, v2/m

                    n_s1, n_s2 = normalize(s1, s2) # Stream
                    n_l1, n_l2 = normalize(l1, l2) # Listeners
                    n_p1, n_p2 = normalize(p1, p2) # Pop
                    n_dur1, n_dur2 = normalize(dur1, dur2) # Duration
                    
                    # Retention (Giữ chân): 100 - Skip Rate. Cao là tốt.
                    ret1 = max(0, 100 - sk1)
                    ret2 = max(0, 100 - sk2)
                    n_ret1, n_ret2 = normalize(ret1, ret2)

                    categories = ['Sức hút (Stream)', 'Độ phủ (Listeners)', 'Danh tiếng (Pop)', 'Sự lôi cuốn (Duration)', 'Giữ chân (Retention)']
                    
                    fig_battle = go.Figure()
                    
                    fig_battle.add_trace(go.Scatterpolar(
                        r=[n_s1, n_l1, n_p1, n_dur1, n_ret1],
                        theta=categories,
                        fill='toself',
                        name=a1,
                        line_color='#1DB954'
                    ))
                    fig_battle.add_trace(go.Scatterpolar(
                        r=[n_s2, n_l2, n_p2, n_dur2, n_ret2],
                        theta=categories,
                        fill='toself',
                        name=a2,
                        line_color='#E91E63'
                    ))

                    fig_battle.update_layout(
                        polar=dict(radialaxis=dict(visible=False, range=[0, 1.1])), # Ẩn trục số cho đẹp
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.1),
                        margin=dict(t=20, b=20)
                    )
                    st.plotly_chart(fig_battle, use_container_width=True)

                # --- PHẦN 3: CHI TIẾT QUỐC GIA (Bar Chart) ---
                with col_bar:
                    st.markdown(f"##### 🌍 Top Quốc gia: {a1} vs {a2}")
                    if "Country" in df.columns:
                        # Đếm số lượng quốc gia có mặt
                        c_count1 = d1["Country"].nunique()
                        c_count2 = d2["Country"].nunique()
                        st.info(f"🌐 Độ phủ thị trường: **{a1}** ({c_count1} QG) - **{a2}** ({c_count2} QG)")
                        
                        # So sánh Stream tại Top 5 thị trường chung
                        # (Logic: Tìm các nước cả 2 cùng có mặt và so sánh)
                        common_countries = list(set(d1["Country"]) & set(d2["Country"]))
                        if common_countries:
                            df_common = df[df["Country"].isin(common_countries) & df[col_art].isin([a1, a2])]
                            # Lấy Top 5 nước có tổng stream lớn nhất
                            top_c_list = df_common.groupby("Country")["Total Streams (Millions)"].sum().nlargest(5).index
                            df_viz = df_common[df_common["Country"].isin(top_c_list)]
                            
                            fig_comp_bar = px.bar(
                                df_viz,
                                x="Country",
                                y="Total Streams (Millions)",
                                color=col_art,
                                barmode="group",
                                title="So găng tại Top 5 thị trường chung",
                                color_discrete_map={a1: '#1DB954', a2: '#E91E63'}
                            )
                            st.plotly_chart(fig_comp_bar, use_container_width=True)
                        else:
                            st.warning("Hai nghệ sĩ này không có thị trường chung để so sánh.")
                    else:
                        st.info("Không có dữ liệu quốc gia.")

            else:
                st.info("👈 Vui lòng chọn 2 nghệ sĩ khác nhau để bắt đầu so sánh.")
# ==============================================================================
# TAB: COUNTRY ANALYSIS (CHỈ DÀNH CHO ALBUM)
# ==============================================================================
# ==============================================================================
# TAB: COUNTRY ANALYSIS (NÂNG CẤP: MARKET MATRIX & PLATFORM MIX)
# ==============================================================================
if data_type == "Album":
    with t_country:
        st.subheader("🌍 Phân tích Thị trường Quốc tế")

        if "Country" in df.columns and not df.empty:
            
            # --- BƯỚC 1: CHUẨN BỊ DỮ LIỆU GOM NHÓM (AGGREGATE) ---
            # Gom nhóm theo Quốc gia để có số liệu tổng quan
            country_agg = df.groupby("Country").agg({
                "Total Streams (Millions)": "sum",
                "Monthly Listeners (Millions)": "sum",
                "Skip Rate (%)": "mean",
                "Avg Stream Duration (Min)": "mean",
                "Album": "count"
            }).reset_index()

            # --- PHẦN 1: BẢN ĐỒ NHIỆT (FULL WIDTH) ---
            st.markdown("##### 🗺️ Bản đồ nhiệt: Phân bổ lượng Stream toàn cầu")
            
            fig_map = px.choropleth(
                country_agg,
                locations="Country",
                locationmode="country names",
                color="Total Streams (Millions)", 
                hover_name="Country",
                hover_data=["Monthly Listeners (Millions)", "Skip Rate (%)"],
                color_continuous_scale="Plasma",
                projection="natural earth" # Dạng bản đồ cong tự nhiên đẹp hơn
            )
            fig_map.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                geo=dict(showframe=False, showcoastlines=False),
                height=450
            )
            st.plotly_chart(fig_map, use_container_width=True)

            st.markdown("---")

            # --- PHẦN 2: PHÂN TÍCH CHUYÊN SÂU (2 CỘT) ---
            c_m1, c_m2 = st.columns([1.5, 1])

            # CỘT TRÁI: MA TRẬN THỊ TRƯỜNG (SCATTER PLOT)
            with c_m1:
                st.markdown("##### 💎 Ma trận Giá trị: Stream vs Người nghe")
                st.caption("Giúp xác định thị trường tiềm năng (Nhiều người nghe nhưng ít Stream) và thị trường Loyal (Ít người nghe nhưng cày Stream).")
                
                fig_matrix = px.scatter(
                    country_agg,
                    x="Monthly Listeners (Millions)",
                    y="Total Streams (Millions)",
                    size="Total Streams (Millions)", # Bong bóng to = Doanh thu cao
                    color="Skip Rate (%)",           # Màu sắc = Chất lượng (Xanh = Tốt/Skip thấp, Vàng/Đỏ = Skip cao)
                    color_continuous_scale="RdYlGn_r", # Đảo ngược màu: Đỏ là Skip cao, Xanh là Skip thấp
                    hover_name="Country",
                    text="Country",
                    title="",
                    labels={
                        "Monthly Listeners (Millions)": "Lượng người nghe (Triệu)", 
                        "Total Streams (Millions)": "Tổng lượt Stream (Triệu)",
                        "Skip Rate (%)": "Tỷ lệ Skip"
                    }
                )
                # Kẻ đường trung bình chia 4 góc phần tư
                avg_list = country_agg["Monthly Listeners (Millions)"].mean()
                avg_str = country_agg["Total Streams (Millions)"].mean()
                
                fig_matrix.add_vline(x=avg_list, line_dash="dash", line_color="gray", annotation_text="TB Người nghe")
                fig_matrix.add_hline(y=avg_str, line_dash="dash", line_color="gray", annotation_text="TB Stream")
                fig_matrix.update_traces(textposition='top center')
                
                st.plotly_chart(fig_matrix, use_container_width=True)

            # CỘT PHẢI: TỶ LỆ PLATFORM (FREE VS PREMIUM)
            with c_m2:
                st.markdown("##### 💳 Tỷ lệ Tài khoản (Free vs Premium)")
                st.caption("Thị trường nào chịu chi tiền (Premium)?")
                
                if "Platform Type" in df.columns:
                    # Gom nhóm đếm số lượng Free/Premium theo từng nước
                    platform_counts = df.groupby(["Country", "Platform Type"]).size().reset_index(name="Count")
                    
                    # Lọc lấy Top 10 nước có dữ liệu lớn nhất để biểu đồ không bị rối
                    top_countries = country_agg.nlargest(10, "Total Streams (Millions)")["Country"].tolist()
                    platform_filtered = platform_counts[platform_counts["Country"].isin(top_countries)]

                    fig_stack = px.bar(
                        platform_filtered,
                        x="Count",
                        y="Country",
                        color="Platform Type",
                        orientation='h',
                        title="Phân bổ nền tảng tại Top 10 QG",
                        barmode="stack", # Xếp chồng
                        color_discrete_map={"Premium": "#1DB954", "Free": "#535353"}, # Màu Spotify chuẩn
                        labels={"Count": "Số lượng bản ghi", "Country": ""}
                    )
                    st.plotly_chart(fig_stack, use_container_width=True)
                else:
                    st.warning("Không có dữ liệu 'Platform Type'.")

            st.markdown("---")

            # --- PHẦN 3: BOX PLOT (GIỮ LẠI CÁI CŨ NHƯNG CẢI TIẾN) ---
            st.markdown("##### 📉 Phân phối Tỷ lệ Bỏ qua (Skip Rate) & Thời lượng nghe")
            
            c_b1, c_b2 = st.columns(2)
            
            with c_b1:
                # Top 10 nước để boxplot đỡ rối
                top_10_c = country_agg.nlargest(10, "Total Streams (Millions)")["Country"].tolist()
                df_top10 = df[df["Country"].isin(top_10_c)]
                
                fig_skip = px.box(
                    df_top10, 
                    x="Country", 
                    y="Skip Rate (%)", 
                    color="Country", 
                    title="Biến động Skip Rate tại Top 10 QG",
                    points="outliers" # Chỉ hiện điểm ngoại lai
                )
                fig_skip.update_layout(showlegend=False, xaxis_title="")
                st.plotly_chart(fig_skip, use_container_width=True)
            
            with c_b2:
                # Biểu đồ mới: Avg Duration by Country
                fig_dur = px.bar(
                    country_agg.nlargest(10, "Total Streams (Millions)"),
                    x="Avg Stream Duration (Min)",
                    y="Country",
                    orientation='h',
                    title="Thời lượng nghe trung bình (Phút)",
                    text_auto='.2f',
                    color="Avg Stream Duration (Min)",
                    color_continuous_scale="Teal"
                )
                fig_dur.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, xaxis_title="Phút")
                st.plotly_chart(fig_dur, use_container_width=True)

        else:
            st.info("Không có dữ liệu quốc gia phù hợp với bộ lọc.")

# ==============================================================================
# TAB: TIME SERIES
# ==============================================================================
time_tab = t_time
# ==============================================================================
# TAB: TIME SERIES (NÂNG CẤP TOÀN DIỆN)
# ==============================================================================
# ==============================================================================
# TAB: TIME SERIES (ĐÃ SỬA LỖI KEYERROR: SONG)
# ==============================================================================
with t_time:
    st.subheader("⏳ Phân tích Chuỗi thời gian & Xu hướng")

    # Tạo 2 tab con
    # Đổi tên Tab 2 linh hoạt theo loại dữ liệu
    tab2_name = "🎵 Lịch sử Bài hát" if "song" in df.columns else "💿 Lịch sử Phát hành"
    ts_tab1, ts_tab2 = st.tabs(["🌏 Xu hướng Thị trường (Global)", tab2_name])

  # --------------------------------------------------------------------------
    # 1. GLOBAL TRENDS (Thị trường thay đổi thế nào?)
    # --------------------------------------------------------------------------
    with ts_tab1:
        st.markdown("### 🌏 Bức tranh toàn cảnh thị trường qua các năm")

        # === LOGIC RIÊNG CHO ALBUM (Sử dụng dữ liệu Stream/Genre/Behavior) ===
        if data_type == "Album":
            if "Release Year" in df.columns and not df.empty:
                # Chuẩn bị dữ liệu: Gom nhóm theo Năm phát hành
                trend_df = df.groupby("Release Year").agg({
                    "Total Streams (Millions)": "sum",
                    "Monthly Listeners (Millions)": "sum",
                    "Skip Rate (%)": "mean",
                    "Avg Stream Duration (Min)": "mean",
                    "Album": "count" # Đếm số lượng album
                }).reset_index().sort_values("Release Year")

                # BIỂU ĐỒ 1: TĂNG TRƯỞNG QUY MÔ (STREAM & NGƯỜI NGHE)
                st.markdown("#### 📈 1. Quy mô thị trường: Stream & Người nghe")
                fig_growth = go.Figure()
                # Trục trái: Streams
                fig_growth.add_trace(go.Scatter(
                    x=trend_df["Release Year"], y=trend_df["Total Streams (Millions)"],
                    mode='lines+markers', name='Tổng Stream (Triệu)',
                    line=dict(color='#1DB954', width=3), marker=dict(size=8)
                ))
                # Trục phải: Listeners
                fig_growth.add_trace(go.Scatter(
                    x=trend_df["Release Year"], y=trend_df["Monthly Listeners (Millions)"],
                    mode='lines+markers', name='Người nghe hàng tháng (Triệu)',
                    line=dict(color='#E91E63', width=3, dash='dot'),
                    yaxis='y2'
                ))
                
                fig_growth.update_layout(
                    title="",
                    xaxis_title="Năm phát hành",
                    yaxis=dict(title="Tổng Stream (Triệu)"),
                    yaxis2=dict(title="Người nghe (Triệu)", overlaying='y', side='right'),
                    hovermode="x unified",
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig_growth, use_container_width=True)

                st.markdown("---")

                # BIỂU ĐỒ 2 & 3 (LAYOUT 2 CỘT)
                c_t1, c_t2 = st.columns(2)

                # Cột 1: SỰ THAY ĐỔI CỦA THỂ LOẠI NHẠC (GENRE EVOLUTION)
                with c_t1:
                    st.markdown("#### 🌊 2. Sự dịch chuyển xu hướng dòng nhạc")
                    if "Genre" in df.columns:
                        # Đếm số lượng album của mỗi Genre theo từng năm
                        genre_trend = df.groupby(["Release Year", "Genre"]).size().reset_index(name="Count")
                        
                        # Lọc lấy các Genre chính (Top 5-7 để đỡ rối)
                        top_genres = df["Genre"].value_counts().head(7).index.tolist()
                        genre_trend_filtered = genre_trend[genre_trend["Genre"].isin(top_genres)]

                        fig_genre = px.area(
                            genre_trend_filtered, 
                            x="Release Year", y="Count", color="Genre",
                            title="Thị phần Album theo Thể loại qua các năm",
                            labels={"Count": "Số lượng Album"},
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        st.plotly_chart(fig_genre, use_container_width=True)
                    else:
                        st.info("Không có dữ liệu Genre.")

                # Cột 2: HÀNH VI NGƯỜI DÙNG (SKIP RATE & DURATION)
                with c_t2:
                    st.markdown("#### ⏳ 3. Hành vi tiêu thụ Âm nhạc")
                    fig_behav = go.Figure()
                    
                    # Avg Duration
                    fig_behav.add_trace(go.Bar(
                        x=trend_df["Release Year"], y=trend_df["Avg Stream Duration (Min)"],
                        name="Thời lượng nghe TB (Phút)", marker_color='#535353', opacity=0.6
                    ))
                    
                    # Skip Rate (Line)
                    fig_behav.add_trace(go.Scatter(
                        x=trend_df["Release Year"], y=trend_df["Skip Rate (%)"],
                        name="Tỷ lệ Bỏ qua (%)", mode='lines+markers',
                        line=dict(color='#FF5722', width=3), yaxis='y2'
                    ))

                    fig_behav.update_layout(
                        title="Tương quan: Thời lượng nghe vs Tỷ lệ Skip",
                        xaxis_title="Năm",
                        yaxis=dict(title="Phút"),
                        yaxis2=dict(title="Skip Rate (%)", overlaying='y', side='right', range=[0, 100]),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(fig_behav, use_container_width=True)
                    
                    st.caption("💡 *Insight: Nếu cột xám (Thời lượng) giảm và đường cam (Skip) tăng -> Xu hướng nghe nhạc 'Mì ăn liền' (Short-form).*")

            else:
                st.warning("⚠️ Không tìm thấy cột 'Release Year' để vẽ chuỗi thời gian cho Album.")

        # === LOGIC CŨ CHO SINGLE (Giữ nguyên phần Audio Features nếu là Single) ===
        else:
            # Kiểm tra có cột date không
            date_col = "date" 
            if not df.empty and date_col in df.columns:
                # ... (GIỮ NGUYÊN CODE CŨ CỦA PHẦN SINGLE Ở ĐÂY NẾU BẠN MUỐN) ...
                # Nếu bạn đã có code cũ cho Single ở đây, hãy paste lại.
                # Nếu không, tôi có thể viết lại phần Single luôn cho bạn.
                
                # Ví dụ code Single cơ bản:
                df_trend = df.copy()
                df_trend['month_year'] = df_trend[date_col].dt.to_period('M').astype(str)
                common_feats = ["energy", "valence", "danceability", "acousticness"]
                available_feats = [f for f in common_feats if f in df_trend.columns]
                
                if available_feats:
                    monthly_stats = df_trend.groupby('month_year')[available_feats].mean().reset_index()
                    fig_evol = go.Figure()
                    for feature in available_feats:
                        fig_evol.add_trace(go.Scatter(x=monthly_stats['month_year'], y=monthly_stats[feature], mode='lines', name=feature.capitalize()))
                    fig_evol.update_layout(title="Audio Features theo thời gian", hovermode="x unified")
                    st.plotly_chart(fig_evol, use_container_width=True)
                else:
                    st.warning("Không đủ dữ liệu Audio Features.")
            else:
                st.info("Chưa chọn dữ liệu Single.")

    # --------------------------------------------------------------------------
    # 2. DETAIL HISTORY (Phân tách logic cho Album và Single)
    # --------------------------------------------------------------------------
# --------------------------------------------------------------------------
    # 2. DETAIL HISTORY (LỊCH SỬ PHÁT HÀNH - ĐÃ TỐI ƯU HÓA)
    # --------------------------------------------------------------------------
    with ts_tab2:
        # Kiểm tra xem có dữ liệu Album và Ngày phát hành không
        if "Album" in df.columns and ("Release Date" in df.columns or "Release Year" in df.columns):
            
            # --- BƯỚC 1: XỬ LÝ DỮ LIỆU (QUAN TRỌNG: GOM NHÓM ĐỂ LOẠI BỎ TRÙNG LẶP) ---
            # Gom nhóm theo Tên Album để tính tổng Stream toàn cầu cho Album đó
            # Giả sử mỗi Album có 1 ngày phát hành duy nhất
            df_unique_album = df.groupby("Album").agg({
                "Total Streams (Millions)": "sum",       # Cộng dồn stream các nước
                "Release Date": "first",                 # Lấy ngày đầu tiên tìm thấy
                "Genre": "first",                        # Lấy Genre đại diện
                "Artist": "first",
                "totalTracks": "max"                     # Lấy số track
            }).reset_index()

            # Lọc bỏ các giá trị lỗi thời gian (nếu có)
            df_unique_album = df_unique_album.dropna(subset=["Release Date"])
            df_unique_album = df_unique_album.sort_values("Release Date")

            st.markdown("### 🗓️ Dòng thời gian: Những cột mốc Âm nhạc")
            st.caption("Biểu đồ chỉ hiển thị mỗi Album một lần (tổng hợp số liệu toàn cầu), giúp nhìn rõ các 'siêu phẩm' ra mắt khi nào.")

            # --- BIỂU ĐỒ 1: TIMELINE BONG BÓNG (DẠNG LOLLIPOP HOẶC SCATTER SẠCH) ---
            # X: Ngày phát hành, Y: Tổng Stream, Size: Tổng Stream
            
            fig_timeline = px.scatter(
                df_unique_album,
                x="Release Date",
                y="Total Streams (Millions)",
                size="Total Streams (Millions)",  # Bong bóng to = Album hot
                color="Genre",                    # Màu theo thể loại
                hover_name="Album",
                text="Album",                     # Hiển thị tên Album cạnh bong bóng
                title="",
                labels={"Release Date": "Thời điểm ra mắt", "Total Streams (Millions)": "Tổng lượt nghe (Triệu)"},
                size_max=50,                      # Kích thước tối đa
                color_discrete_sequence=px.colors.qualitative.Prism
            )

            # Tinh chỉnh giao diện để tên không bị chồng chéo quá nhiều
            fig_timeline.update_traces(textposition='top center')
            fig_timeline.update_layout(height=500, xaxis_title="Năm phát hành", yaxis_title="Độ thành công (Stream)")
            st.plotly_chart(fig_timeline, use_container_width=True)

            st.markdown("---")

            # --- BIỂU ĐỒ 2 & 3: PHÂN TÍCH MÙA VỤ & TẦN SUẤT ---
            c_h1, c_h2 = st.columns([1, 1])

            with c_h1:
                st.markdown("#### 🍂 Phân tích Mùa vụ (Seasonality)")
                st.caption("Nghệ sĩ/Thị trường thường ra mắt sản phẩm vào tháng nào?")
                
                # Trích xuất tháng
                df_unique_album['Month'] = df_unique_album['Release Date'].dt.month_name()
                df_unique_album['Month_Num'] = df_unique_album['Release Date'].dt.month
                
                # Đếm số lượng album theo tháng
                month_counts = df_unique_album.groupby(['Month_Num', 'Month']).size().reset_index(name='Count')
                month_counts = month_counts.sort_values('Month_Num')

                fig_season = px.bar(
                    month_counts,
                    x='Month',
                    y='Count',
                    text='Count',
                    title="Số lượng Album phát hành theo Tháng",
                    color='Count',
                    color_continuous_scale='Viridis'
                )
                fig_season.update_layout(xaxis_title="", yaxis_title="Số lượng Album")
                st.plotly_chart(fig_season, use_container_width=True)

            with c_h2:
                st.markdown("#### 📅 Xu hướng phát hành theo Năm")
                st.caption("Nhịp độ sản xuất âm nhạc tăng hay giảm?")
                
                df_unique_album['Year'] = df_unique_album['Release Date'].dt.year
                year_counts = df_unique_album.groupby('Year')['Total Streams (Millions)'].mean().reset_index()
                
                fig_velocity = px.line(
                    year_counts,
                    x='Year',
                    y='Total Streams (Millions)',
                    markers=True,
                    title="Sức hút trung bình của Album qua các năm",
                    line_shape='spline' # Đường cong mềm mại
                )
                fig_velocity.update_traces(line_color='#FF6F61', line_width=3)
                fig_velocity.update_layout(xaxis_title="Năm", yaxis_title="Stream TB / Album")
                st.plotly_chart(fig_velocity, use_container_width=True)
                
            # --- INSIGHT TEXT ---
            # Tìm tháng có nhiều album nhất
            if not month_counts.empty:
                peak_month = month_counts.loc[month_counts['Count'].idxmax()]['Month']
                st.info(f"💡 **Insight:** Tháng **{peak_month}** là thời điểm sôi động nhất với nhiều Album được ra mắt.")

        else:
            st.warning("⚠️ Không tìm thấy dữ liệu 'Release Date' hoặc 'Album' để vẽ lịch sử.")
# ==============================================================================
# TAB: OTHER INSIGHTS
# ==============================================================================
insight_tab = t_insight

with insight_tab:
    st.subheader("🧩 Các Insights Chuyên sâu & Xu hướng Hiện tại")

    if data_type == "Album":
        # --- HÀNG 1: PHÂN TÍCH HÃNG ĐĨA & HÀNH VI NGHE ---
        c_i1, c_i2 = st.columns([1, 1.2])

        # 1. TOP HÃNG ĐĨA (THEO TỔNG STREAM - KHÔNG PHẢI SỐ LƯỢNG)
        with c_i1:
            st.markdown("##### 🏷️ Top 10 Hãng thu âm quyền lực nhất")
            st.caption("Xếp hạng dựa trên Tổng lượt Stream (Thay vì số lượng Album).")
            
            if "label" in df.columns and "Total Streams (Millions)" in df.columns:
                # Gom nhóm tính tổng stream
                label_stats = df.groupby("label")["Total Streams (Millions)"].sum().reset_index()
                top_labels = label_stats.nlargest(10, "Total Streams (Millions)").sort_values("Total Streams (Millions)", ascending=True)
                
                fig_lbl = px.bar(
                    top_labels, 
                    y="label", 
                    x="Total Streams (Millions)", 
                    orientation='h',
                    text_auto='.2s',
                    color="Total Streams (Millions)",
                    color_continuous_scale="Blues"
                )
                fig_lbl.update_layout(xaxis_title="Tổng Stream (Triệu)", yaxis_title="", showlegend=False)
                st.plotly_chart(fig_lbl, use_container_width=True)
            else:
                st.warning("Thiếu dữ liệu Label hoặc Stream.")

        # 2. TƯƠNG QUAN: THỜI LƯỢNG VS SKIP RATE (GOM THEO GENRE)
        with c_i2:
            st.markdown("##### ⏳ Thể loại nào 'giữ chân' người nghe tốt nhất?")
            st.caption("Thay thế biểu đồ bong bóng cũ bằng biểu đồ gom nhóm theo Genre.")
            
            required_cols = ["Genre", "Avg Stream Duration (Min)", "Skip Rate (%)", "Total Streams (Millions)"]
            if all(col in df.columns for col in required_cols):
                # Gom nhóm theo Genre tính trung bình
                genre_behavior = df.groupby("Genre").agg({
                    "Avg Stream Duration (Min)": "mean",
                    "Skip Rate (%)": "mean",
                    "Total Streams (Millions)": "sum",
                    "Album": "count"
                }).reset_index()
                
                # Lọc bớt các Genre quá nhỏ (ít hơn 2 album) để biểu đồ sạch
                genre_behavior = genre_behavior[genre_behavior["Album"] >= 2]

                fig_corr = px.scatter(
                    genre_behavior,
                    x="Avg Stream Duration (Min)",
                    y="Skip Rate (%)",
                    size="Total Streams (Millions)", # Bong bóng to = Thể loại Hot
                    color="Genre",
                    text="Genre",
                    title="Thời lượng TB vs Tỷ lệ Bỏ qua (Theo Thể loại)",
                    labels={
                        "Avg Stream Duration (Min)": "Thời lượng TB (Phút)",
                        "Skip Rate (%)": "Tỷ lệ Skip (%)"
                    }
                )
                # Thêm đường tham chiếu trung bình
                avg_skip = df["Skip Rate (%)"].mean()
                fig_corr.add_hline(y=avg_skip, line_dash="dash", line_color="gray", annotation_text="TB Skip Rate")
                
                fig_corr.update_traces(textposition='top center')
                st.plotly_chart(fig_corr, use_container_width=True)
                
                st.info("💡 **Insight:** Các thể loại nằm ở **Góc dưới bên phải** (Dài + Skip thấp) là nhạc có tính thưởng thức cao (High engagement).")
            else:
                st.warning("Thiếu dữ liệu Duration hoặc Skip Rate.")

        st.markdown("---")

        # --- HÀNG 2: TRENDING (LAST 30 DAYS) ---
        st.markdown("### 🔥 Đang thịnh hành: Top Album trong 30 ngày qua")
        
        if "Streams Last 30 Days (Millions)" in df.columns:
            # Lấy Top 10 theo 30 ngày gần nhất
            trending_df = df.nlargest(10, "Streams Last 30 Days (Millions)").sort_values("Streams Last 30 Days (Millions)", ascending=True)
            
            # Tạo biểu đồ kết hợp (Bar chart + Line chart nếu cần, ở đây dùng Bar màu mè cho đẹp)
            fig_trend = px.bar(
                trending_df,
                x="Streams Last 30 Days (Millions)",
                y="Album",
                orientation='h',
                text="Artist", # Hiển thị tên nghệ sĩ trên thanh
                color="Skip Rate (%)", # Màu sắc thể hiện chất lượng (Skip rate thấp là xanh/tốt)
                color_continuous_scale="RdYlGn_r", # Đỏ (Cao) -> Xanh (Thấp) cho Skip Rate
                title="Top 10 Album được nghe nhiều nhất tháng qua (Màu sắc = Tỷ lệ Skip)",
                labels={"Streams Last 30 Days (Millions)": "Lượt nghe 30 ngày qua (Triệu)", "Album": ""},
                hover_data=["Total Streams (Millions)", "Genre"]
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("Không có dữ liệu 'Streams Last 30 Days'.")

    else: # Code cũ cho Single (Giữ nguyên)
        c1, c2 = st.columns(2)
        with c1:
            if "is_explicit" in df.columns:
                explicit_counts = df["is_explicit"].map({0: "Clean", 1: "Explicit"}).value_counts()
                fig_pie = px.pie(names=explicit_counts.index, values=explicit_counts.values, 
                                    title="🔞 Tỷ lệ Nội dung nhạy cảm (Explicit)", color_discrete_sequence=["#1DB954", "#E91E63"])
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            if "key_name" in df.columns:
                key_counts = df["key_name"].value_counts().head(12)
                fig_key = px.bar(x=key_counts.index, y=key_counts.values, title="🎹 Phân bố Tone (Key)")
                st.plotly_chart(fig_key, use_container_width=True)

# -----------------------------
# Footer & Download
# -----------------------------
st.markdown("---")
st.subheader("📥 Dữ liệu chi tiết")
st.dataframe(df.head(100), use_container_width=True)

csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Tải xuống CSV",
    data=csv,
    file_name=f"spotify_data_{data_type}.csv",
    mime='text/csv',
)