# 2_By_Country.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime

# =========================
# ⚙️ Cấu hình giao diện
# =========================
st.set_page_config(page_title="Spotify Top 50 — Country Dashboard", layout="wide")

# ---- Theme nhẹ nhàng Spotify
st.markdown("""
<style>
body { background-color: #F9F9F9; color: #222; font-family: "Poppins", sans-serif; }
h1, h2, h3, h4 { color: #1DB954; font-weight: 600; }
[data-testid="stMetricLabel"] { color: #1DB954 !important; }
[data-testid="stMetricValue"] { color: #0a8f44 !important; font-weight: bold; }
div[data-testid="stPlotlyChart"] {
  border-radius: 12px; background: #ffffff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 10px;
}
[data-testid="stDataFrame"] table { border-radius: 10px; border: 1px solid #e5e5e5; }
thead tr th {
  background-color: #E8F8EF !important; color: #0a8f44 !important; font-weight: 600 !important;
}
tbody tr:hover { background-color: #F2FFF8 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 🧠 Helper
# ============================================================
def _split_artists(s: str):
    """Tách nghệ sĩ khi là collab: 'A, B & C' -> ['A','B','C']"""
    if not isinstance(s, str):
        return []
    parts = []
    for chunk in s.replace("&", ",").split(","):
        c = chunk.strip()
        if c:
            parts.append(c)
    return parts


def _preprocess(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch & chuẩn hoá:
    - Ép kiểu numeric
    - Chuẩn hoá cột date
    - Khử trùng lặp theo (date, song) giữ position tốt nhất
    """
    df = df_raw.copy()

    num_cols = ["energy", "danceability", "valence", "tempo",
                "popularity", "position", "is_explicit"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Khử trùng lặp: cùng 1 bài tại cùng 1 ngày -> giữ rank tốt nhất
    keep_cols = list(df.columns)
    if {"date", "song", "position"}.issubset(df.columns):
        df = (
            df.sort_values(["date", "song", "position"])
              .groupby(["date", "song"], as_index=False)
              .first()
        )
        df = df[keep_cols]

    return df


# Các country KHÔNG muốn xuất hiện trong dropdown chọn tay
EXCLUDED_DROPDOWN_COUNTRIES = {
    "United States",   # loại Mỹ khỏi dropdown, nhưng vẫn render được nếu truyền tham số
    "World"
}
# Map tên country khi click từ Home → tên nội bộ dùng cho collection
ALIAS_FROM_HOME = {
    "United States": "Usa",
    "USA": "Usa",
    "United Kingdom": "Uk",
    "UK": "Uk",
}


MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


def get_db():
    client = MongoClient(MONGO_URI)
    return client["spotify_project"]


# ============================================================
# 🔧 HÀM CHÍNH
# ============================================================
def render_country_dashboard(country_name: str | None = None):
    db = get_db()  # ✅ luôn có db từ đầu

    # 1) Nếu có chọn từ Home → dùng
    if country_name is None and "selected_country" in st.session_state:
        country_name = st.session_state["selected_country"]

    # 1.1) Chuẩn hoá alias từ Home ("United States" -> "Usa", "United Kingdom" -> "Uk")
    if country_name in ALIAS_FROM_HOME:
        country_name = ALIAS_FROM_HOME[country_name]

    # 1.2) Tách tên hiển thị (display_name) và tên nội bộ (country_name)
    display_name = country_name
    if country_name == "Usa":
        display_name = "United States"
    elif country_name == "Uk":
        display_name = "United Kingdom"

    # 2) Nếu vẫn None → dropdown lấy ĐỘNG từ Mongo
    if country_name is None:
        try:
            collections = db.list_collection_names()

            countries_from_mongo = []
            for col in collections:
                if col.startswith("top50_"):
                    raw = col.replace("top50_", "")         # ví dụ: 'south_korea'
                    name = raw.replace("_", " ").title()    # -> 'South Korea'
                    countries_from_mongo.append(name)

            # loại các nước không muốn hiển thị
            available = sorted({
                c for c in countries_from_mongo
                if c not in EXCLUDED_DROPDOWN_COUNTRIES
            })

            # fallback nếu vì lý do gì đó không lấy được
            if not available:
                available = ["France", "Italy", "Japan", "Mexico", "Spain", "South Korea", "Argentina"]
        except Exception:
            available = ["France", "Italy", "Japan", "Mexico", "Spain", "South Korea", "Argentina"]

        country_name = st.selectbox("🌍 Chọn quốc gia để phân tích", available, index=0)
        # khi chọn từ dropdown, tên hiển thị = tên select
        display_name = country_name

    if country_name is None:
        st.error("❌ Không thể xác định quốc gia.")
        return

    # 👉 từ đây trở đi dùng display_name cho tiêu đề, country_name cho collection
    st.title(f"🌍 Spotify Top 50 – {display_name} Dashboard")

    # -----------------------------
    # Lấy collection tương ứng
    # -----------------------------
    collection_name = f"top50_{country_name.lower().replace(' ', '_')}"
    collection = db[collection_name]

    @st.cache_data(ttl=3600, show_spinner=False)
    def load_data(col_name: str):
        data = list(db[col_name].find({}, {"_id": 0}))
        return pd.DataFrame(data)

    df_raw = load_data(collection_name)
    if df_raw.empty:
        st.warning(f"⚠️ Không có dữ liệu cho {country_name}.")
        return

    df = _preprocess(df_raw)

    # -----------------------------
    # 5️⃣ Bộ lọc thời gian chung (đặt ngay đầu trang)
    # -----------------------------
    time_col = None
    if "week" in df.columns:
        time_col = "week"
    elif "date" in df.columns:
        time_col = "date"

    if time_col is not None:
        st.markdown("### 📆 Bộ lọc thời gian phân tích")
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        min_date = df[time_col].min()
        max_date = df[time_col].max()

        if pd.notna(min_date) and pd.notna(max_date):
            start_date, end_date = st.slider(
                "Chọn phạm vi thời gian muốn phân tích:",
                min_value=min_date.to_pydatetime(),
                max_value=max_date.to_pydatetime(),
                value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                format="YYYY-MM-DD",
            )

            st.caption(
                f"📅 Dữ liệu trong khoảng "
                f"**{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}**"
            )

            df = df[
                (df[time_col] >= pd.to_datetime(start_date)) &
                (df[time_col] <= pd.to_datetime(end_date))
            ]
        else:
            st.warning("⚠️ Cột thời gian không có giá trị hợp lệ, không áp dụng được bộ lọc thời gian.")

    # ============================================================
    # 1) Metric tổng quan
    # ============================================================
    songs_count = df["song"].nunique() if "song" in df.columns else len(df)
    artists_count = df["artist"].nunique() if "artist" in df.columns else 0
    genres_count = df["main_genre"].nunique() if "main_genre" in df.columns else 0
    pop_metric = (
        df.groupby("song")["popularity"].mean().mean()
        if {"song", "popularity"}.issubset(df.columns) else float("nan")
    )

    st.subheader("📊 Tổng quan dữ liệu")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎵 Số bài hát (unique)", songs_count)
    c2.metric("👩‍🎤 Số nghệ sĩ", artists_count)
    c3.metric("🎶 Số thể loại", genres_count)
    c4.metric(
        "🔥 Độ phổ biến TB (trung bình theo bài)",
        None if pd.isna(pop_metric) else round(pop_metric, 1)
    )

    # =========================
    # 3️⃣ Xu hướng thể loại
    # =========================
    st.subheader("🎧 Xu hướng thể loại")

    feature = st.selectbox(
        "Chọn đặc trưng âm nhạc",
        ["energy", "danceability", "valence", "tempo", "popularity"],
        key=f"feature_{country_name}"
    )

    if "main_genre" in df.columns and feature in df.columns and "song" in df.columns:
        # Gộp theo bài – mỗi bài chỉ tính 1 lần
        song_level = (
            df.groupby(["song", "main_genre"], as_index=False)[feature]
              .mean()
              .rename(columns={feature: f"{feature}_per_song"})
        )

        # Bỏ các thể loại "unknown"
        remove_unknown = ["unknown", "unknow", "n/a", "none", "undefined", ""]
        song_level = song_level[
            ~song_level["main_genre"].str.lower().isin(remove_unknown)
        ]

        # Lọc thể loại có số bài tối thiểu
        min_tracks = st.slider(
            "🔢 Lọc thể loại có ít nhất bao nhiêu bài",
            1, 20, 3,
            key=f"min_tracks_{feature}"
        )
        genre_counts = song_level["main_genre"].value_counts()
        keep_genres = genre_counts[genre_counts >= min_tracks].index
        song_level = song_level[song_level["main_genre"].isin(keep_genres)]

        genre_agg = (
            song_level.groupby("main_genre")[f"{feature}_per_song"]
                      .mean()
                      .sort_values(ascending=False)
                      .reset_index()
                      .rename(columns={f"{feature}_per_song": feature})
        )
        genre_agg["#tracks"] = genre_agg["main_genre"].map(genre_counts)

        fig_genre = px.bar(
            genre_agg, x="main_genre", y=feature, color=feature,
            color_continuous_scale="greens",
            title=f"Top Thể Loại theo {feature.title()} (chuẩn hoá theo bài)",
            hover_data=["#tracks"],
            labels={"main_genre": "Thể loại", feature: feature, "#tracks": "Số bài (unique)"}
        )
        fig_genre.update_layout(
            xaxis_title="Thể loại",
            yaxis_title=feature,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_genre, use_container_width=True)

    # ============================================================
    # 4) Nghệ sĩ & Bài hát nổi bật
    # ============================================================
    st.subheader("🌟 Nghệ sĩ & Bài hát nổi bật")
    choice = st.radio(
        "Chọn tiêu chí hiển thị:",
        ["Top 10 Nghệ sĩ", "Top 10 Bài hát"],
        horizontal=True,
        key=f"choice_{country_name}"
    )

    # --- Top 10 Bài hát ---
    if choice == "Top 10 Bài hát" and {"song", "main_genre", "popularity"}.issubset(df.columns):
        top_song = (
            df.groupby(["song", "main_genre"])["popularity"]
              .mean()
              .sort_values(ascending=False)
              .head(10)
              .reset_index()
        )

        fig_song = px.bar(
            top_song,
            x="popularity",
            y="song",
            color="popularity",
            color_continuous_scale="Greens",
            orientation="h",
            title="🎵 Top 10 Bài Hát Phổ Biến Nhất",
            labels={
                "popularity": "Độ nổi TB (0–100)",
                "song": "Bài hát"
            },
            hover_data=["main_genre"]
        )
        # Bài nổi nhất nằm TRÊN
        fig_song.update_yaxes(autorange="reversed")
        fig_song.update_coloraxes(colorbar_title="Độ nổi")
        st.plotly_chart(fig_song, use_container_width=True)

    # --- Top 10 Nghệ sĩ ---
    if choice == "Top 10 Nghệ sĩ" and {"artist", "song"}.issubset(df.columns):
        artist_song = (
            df[["artist", "song"]]
              .dropna()
              .assign(artist_list=lambda d: d["artist"].apply(_split_artists))
              .explode("artist_list")
              .drop(columns=["artist"])
              .rename(columns={"artist_list": "artist"})
              .drop_duplicates()
        )

        top_artist = (
            artist_song.groupby("artist")["song"].nunique()
                       .sort_values(ascending=False)
                       .head(10)
                       .reset_index(name="tracks")
        )

        fig_artist = px.bar(
            top_artist,
            x="tracks",
            y="artist",
            orientation="h",
            color="tracks",
            color_continuous_scale="Greens",
            title=f"🎤 Top 10 Nghệ Sĩ Có Nhiều Bài Nhất ({country_name})",
            labels={"tracks": "Số bài (unique)", "artist": "Nghệ sĩ"}
        )
        fig_artist.update_layout(xaxis_title="Số bài (unique)", yaxis_title="Nghệ sĩ")
        fig_artist.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_artist, use_container_width=True)

        # Solo vs Collab
        st.subheader("👥 Tỷ lệ Nghệ sĩ Solo vs Collaboration")
        df_collab = df.copy()
        df_collab["collab_type"] = df_collab["artist"].apply(
            lambda s: "Collab" if len(_split_artists(s)) > 1 else "Solo"
        )
        collab_count = df_collab["collab_type"].value_counts().reset_index()
        collab_count.columns = ["Type", "Count"]
        fig_collab = px.pie(
            collab_count,
            values="Count",
            names="Type",
            color="Type",
            color_discrete_map={"Solo": "#1DB954", "Collab": "#5ed88d"},
            title="Tỷ lệ Bài Hát Solo vs Collaboration"
        )
        st.plotly_chart(fig_collab, use_container_width=True)

    elif choice == "Top 10 Bài hát" and "is_explicit" in df.columns:
        st.subheader("🚫 Tỷ lệ Explicit vs Clean")
        explicit_ratio = df["is_explicit"].value_counts(dropna=False).reset_index()
        explicit_ratio.columns = ["Explicit", "Count"]
        explicit_ratio["Label"] = explicit_ratio["Explicit"].map({1: "Explicit", 0: "Clean"})
        fig_explicit = px.pie(
            explicit_ratio, values="Count", names="Label", hole=0.4,
            color="Label",
            color_discrete_map={"Explicit": "#1DB954", "Clean": "#b3e8c8"},
            title="Tỷ lệ Bài Hát Có Nội Dung Explicit"
        )
        st.plotly_chart(fig_explicit, use_container_width=True)

    # 🔥 Popularity Trend
    if "date" in df.columns:
        st.subheader("🔥 Biến động độ hot theo thời gian")
        songs_available = df["song"].value_counts().head(50).index.tolist()
        selected_songs = st.multiselect(
            "🎵 Chọn 1 hoặc nhiều bài để so sánh:",
            options=songs_available,
            default=songs_available[:1],
            key=f"multi_song_{country_name}"
        )
        if selected_songs:
            song_df = df[df["song"].isin(selected_songs)].sort_values("date")
            if not song_df.empty:
                fig_hot = px.line(
                    song_df,
                    x="date",
                    y="popularity",
                    color="song",
                    markers=True,
                    title="🔥 Popularity theo thời gian (So sánh nhiều bài)",
                    labels={"popularity": "Popularity", "date": "date", "song": "Bài hát"},
                )
                st.plotly_chart(fig_hot, use_container_width=True)

    # 📈 Longevity vs Rank
    if {"position", "date", "song"}.issubset(df.columns):
        st.subheader("📈 Độ bền & Thứ hạng (Longevity vs Peak Rank)")
        song_stats = (
            df.groupby("song")
              .agg(
                  best_rank=("position", "min"),
                  first_date=("date", "min"),
                  last_date=("date", "max"),
              )
              .reset_index()
        )
        song_stats["days_on_chart"] = (
            song_stats["last_date"] - song_stats["first_date"]
        ).dt.days + 1
        song_stats = song_stats[song_stats["days_on_chart"].notna()]

        fig_longevity = px.scatter(
            song_stats,
            x="best_rank",
            y="days_on_chart",
            hover_data=["song"],
            color="best_rank",
            color_continuous_scale="Greens_r",
            title="⏳ Độ Bền Bài Hát vs Thứ Hạng Cao Nhất",
            labels={
                "best_rank": "Best Rank (nhỏ là tốt)",
                "days_on_chart": "Số ngày xuất hiện",
            },
        )
        fig_longevity.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_longevity, use_container_width=True)

    # 🎚️ Boxplot đặc trưng
    if {"energy", "danceability", "valence", "tempo"}.issubset(df.columns):
        st.subheader("🎚️ Phân bố các đặc trưng âm nhạc")
        melted = df.melt(
            value_vars=["energy", "danceability", "valence", "tempo"],
            var_name="Feature", value_name="Value"
        )
        fig_box = px.box(
            melted, x="Feature", y="Value", color="Feature",
            color_discrete_sequence=px.colors.sequential.Greens,
            title="Phân bố Đặc Trưng Âm Nhạc Trong Top 50"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # ============================================================
    # 8) Bảng dữ liệu gốc + bộ lọc & link Spotify
    # ============================================================
    st.subheader("📋 Dữ liệu Gốc")

    show_cols = [
        c for c in ["date", "position", "song", "artist",
                    "main_genre", "popularity", "is_explicit", "href"]
        if c in df.columns
    ]

    base_df = df.copy()
    if {"date", "position"}.issubset(df.columns):
        base_df = base_df.sort_values(["date", "position"])
    base_df = base_df[show_cols]

    with st.expander("🔎 Bộ lọc dữ liệu", expanded=True):
        global_search = st.text_input("🔍 Tìm kiếm nhanh (tất cả cột)", "")
        st.caption("Lọc theo từng cột (substring, không phân biệt hoa thường):")
        col_widgets = st.columns(len(show_cols))
        col_filters = {}
        for ui_col, col_name in zip(col_widgets, show_cols):
            col_filters[col_name] = ui_col.text_input(
                col_name, key=f"filter_{col_name}"
            )

    filtered_df = base_df.copy()

    if global_search:
        mask = pd.Series(False, index=filtered_df.index)
        for c in show_cols:
            mask |= filtered_df[c].astype(str).str.contains(
                global_search, case=False, na=False
            )
        filtered_df = filtered_df[mask]

    for c, val in col_filters.items():
        if val:
            filtered_df = filtered_df[
                filtered_df[c].astype(str).str.contains(val, case=False, na=False)
            ]

    # 👉 Hiển thị: ẩn index + biến href thành LinkColumn
    df_show = filtered_df.reset_index(drop=True).copy()
    if "href" in df_show.columns:
        df_show["href"] = df_show["href"].replace("None", None)

        st.data_editor(
            df_show,
            hide_index=True,
            use_container_width=True,
            column_config={
                "href": st.column_config.LinkColumn(
                    "Spotify",
                    display_text="Mở trên Spotify"
                )
            },
        )
    else:
        st.dataframe(df_show, use_container_width=True)

    st.markdown("---")
    st.caption(f"🎵 Spotify Top 50 — {country_name}")
    st.caption("📊 Dữ liệu từ MongoDB Atlas – database `spotify_project`")


# =========================
# ▶️ Chạy độc lập
# =========================
if __name__ == "__main__":
    render_country_dashboard()

# # 2_By_Country.py
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from pymongo import MongoClient
# from datetime import datetime
# import streamlit.components.v1 as components  # ✅ thêm cho smooth scroll

# # =========================
# # ⚙️ Cấu hình giao diện
# # =========================
# st.set_page_config(page_title="Spotify Top 50 — Country Dashboard", layout="wide")

# # ---- Theme nhẹ nhàng Spotify
# st.markdown("""
# <style>
# body { background-color: #F9F9F9; color: #222; font-family: "Poppins", sans-serif; }
# h1, h2, h3, h4 { color: #1DB954; font-weight: 600; }
# [data-testid="stMetricLabel"] { color: #1DB954 !important; }
# [data-testid="stMetricValue"] { color: #0a8f44 !important; font-weight: bold; }
# div[data-testid="stPlotlyChart"] {
#   border-radius: 12px; background: #ffffff;
#   box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 10px;
# }
# [data-testid="stDataFrame"] table { border-radius: 10px; border: 1px solid #e5e5e5; }
# thead tr th {
#   background-color: #E8F8EF !important; color: #0a8f44 !important; font-weight: 600 !important;
# }
# tbody tr:hover { background-color: #F2FFF8 !important; }
# </style>
# """, unsafe_allow_html=True)


# # ============================================================
# # 🧠 Helper
# # ============================================================
# def _split_artists(s: str):
#     """Tách nghệ sĩ khi là collab: 'A, B & C' -> ['A','B','C']"""
#     if not isinstance(s, str):
#         return []
#     # Thường dữ liệu có dấu ',' và '&'
#     parts = []
#     for chunk in s.replace("&", ",").split(","):
#         c = chunk.strip()
#         if c:
#             parts.append(c)
#     return parts

# # Các country KHÔNG muốn xuất hiện trong dropdown chọn tay
# EXCLUDED_DROPDOWN_COUNTRIES = {
#     "World","w"
# }



# def _preprocess(df_raw: pd.DataFrame) -> pd.DataFrame:
#     """Làm sạch & chuẩn hoá để dữ liệu 'mịn':
#     - Ép kiểu numeric
#     - Chuẩn hoá cột date
#     - Khử trùng lặp theo (date, song) giữ vị trí tốt nhất (position nhỏ nhất)
#     """
#     df = df_raw.copy()

#     num_cols = ["energy", "danceability", "valence", "tempo",
#                 "popularity", "position", "is_explicit"]
#     for c in num_cols:
#         if c in df.columns:
#             df[c] = pd.to_numeric(df[c], errors="coerce")

#     if "date" in df.columns:
#         df["date"] = pd.to_datetime(df["date"], errors="coerce")

#     # Khử trùng lặp: cùng 1 bài tại cùng 1 ngày -> giữ rank tốt nhất
#     keep_cols = list(df.columns)
#     if "date" in df.columns and "song" in df.columns and "position" in df.columns:
#         df = (
#             df.sort_values(["date", "song", "position"])
#               .groupby(["date", "song"], as_index=False)
#               .first()
#         )
#         df = df[keep_cols]

#     return df


# # ============================================================
# # 🔧 HÀM CHÍNH
# # ============================================================
# def render_country_dashboard(country_name: str | None = None):


#     # -----------------------------
#     # MongoDB
#     # -----------------------------
#     uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
#     client = MongoClient(uri)
#     db = client["spotify_project"]
#     collection_name = f"top50_{country_name.lower().replace(' ', '_')}"
#     collection = db[collection_name]

#     # 1) Đọc lựa chọn từ Home (nếu có)
#     if country_name is None and "selected_country" in st.session_state:
#         country_name = st.session_state["selected_country"]

#     # 2) Dropdown chỉ hiện khi chạy độc lập
#     #    👉 Danh sách country lấy ĐỘNG từ MongoDB, rồi loại bỏ những nước trong EXCLUDED_DROPDOWN_COUNTRIES
#     if country_name is None:
#         try:
#             collections = db.list_collection_names()

#             countries_from_mongo = []
#             for col in collections:
#                 if col.startswith("top50_"):
#                     raw = col.replace("top50_", "")        # ví dụ: 'south_korea'
#                     name = raw.replace("_", " ").title()   # -> 'South Korea'
#                     countries_from_mongo.append(name)

#             # Loại bỏ các country không muốn hiện trong dropdown
#             available = sorted({
#                 c for c in countries_from_mongo
#                 if c not in EXCLUDED_DROPDOWN_COUNTRIES
#             })

#             # Nếu vì lý do gì đó không lấy được gì từ Mongo → tránh dropdown rỗng
#             if not available:
#                 available = ["France", "Italy", "Japan", "Mexico", "South Korea", "Spain", "Argentina"]

#         except Exception as e:
#             # st.warning(f"Không lấy được danh sách country từ MongoDB, dùng danh sách mặc định. (Chi tiết: {e})")
#             available = ["France", "Italy", "Japan", "Mexico", "South Korea", "Spain", "Argentina"]

#         country_name = st.selectbox("🌍 Chọn quốc gia để phân tích", available, index=0)




#     @st.cache_data(ttl=3600, show_spinner=False)
#     def load_data(col_name: str):
#         data = list(db[col_name].find({}, {"_id": 0}))
#         return pd.DataFrame(data)

#     df_raw = load_data(collection_name)
#     if df_raw.empty:
#         st.warning(f"⚠️ Không có dữ liệu cho {country_name}.")
#         return

#     df = _preprocess(df_raw)

#     # -----------------------------
#     # 5️⃣ Bộ lọc thời gian chung (trên đầu trang)
#     # -----------------------------
#     time_col = None
#     if "week" in df.columns:
#         time_col = "week"
#     elif "date" in df.columns:
#         time_col = "date"

#     if time_col is not None:
#         st.markdown("### 📆 Bộ lọc thời gian phân tích")

#         df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
#         min_date = df[time_col].min()
#         max_date = df[time_col].max()

#         if pd.notna(min_date) and pd.notna(max_date):
#             start_date, end_date = st.slider(
#                 "Chọn phạm vi thời gian muốn phân tích:",
#                 min_value=min_date.to_pydatetime(),
#                 max_value=max_date.to_pydatetime(),
#                 value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
#                 format="YYYY-MM-DD",
#             )

#             st.caption(
#                 f"📅 Dữ liệu trong khoảng "
#                 f"**{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}**"
#             )

#             df = df[
#                 (df[time_col] >= pd.to_datetime(start_date)) &
#                 (df[time_col] <= pd.to_datetime(end_date))
#             ]
#         else:
#             st.warning("⚠️ Cột thời gian không có giá trị hợp lệ, không áp dụng được bộ lọc thời gian.")

#     # ============================================================
#     # 1) Metric tổng quan
#     # ============================================================
#     songs_count = df["song"].nunique() if "song" in df.columns else len(df)
#     artists_count = df["artist"].nunique() if "artist" in df.columns else 0
#     genres_count = df["main_genre"].nunique() if "main_genre" in df.columns else 0
#     pop_metric = (
#         df.groupby("song")["popularity"].mean().mean()
#         if "song" in df.columns and "popularity" in df.columns else float("nan")
#     )

#     st.subheader("📊 Tổng quan dữ liệu")
#     c1, c2, c3, c4 = st.columns(4)
#     c1.metric("🎵 Số bài hát (unique)", songs_count)
#     c2.metric("👩‍🎤 Số nghệ sĩ", artists_count)
#     c3.metric("🎶 Số thể loại", genres_count)
#     c4.metric(
#         "🔥 Độ phổ biến TB (trung bình theo bài)",
#         None if pd.isna(pop_metric) else round(pop_metric, 1)
#     )

#     # =========================
#     # 3️⃣ Xu hướng thể loại
#     # =========================
#     st.subheader("🎧 Xu hướng thể loại")

#     feature = st.selectbox(
#         "Chọn đặc trưng âm nhạc",
#         ["energy", "danceability", "valence", "tempo", "popularity"],
#         key=f"feature_{country_name}"
#     )

#     if "main_genre" in df.columns and feature in df.columns and "song" in df.columns:
#         song_level = (
#             df.groupby(["song", "main_genre"], as_index=False)[feature]
#               .mean()
#               .rename(columns={feature: f"{feature}_per_song"})
#         )

#         remove_unknown = ["unknown", "unknow", "n/a", "none", "undefined", ""]
#         song_level = song_level[
#             ~song_level["main_genre"].str.lower().isin(remove_unknown)
#         ]

#         min_tracks = st.slider(
#             "🔢 Lọc thể loại có ít nhất bao nhiêu bài",
#             1, 20, 3,
#             key=f"min_tracks_{feature}"
#         )
#         genre_counts = song_level["main_genre"].value_counts()
#         keep_genres = genre_counts[genre_counts >= min_tracks].index
#         song_level = song_level[song_level["main_genre"].isin(keep_genres)]

#         genre_agg = (
#             song_level.groupby("main_genre")[f"{feature}_per_song"]
#                       .mean()
#                       .sort_values(ascending=False)
#                       .reset_index()
#                       .rename(columns={f"{feature}_per_song": feature})
#         )
#         genre_agg["#tracks"] = genre_agg["main_genre"].map(genre_counts)

#         fig_genre = px.bar(
#             genre_agg, x="main_genre", y=feature, color=feature,
#             color_continuous_scale="greens",
#             title=f"Top Thể Loại theo {feature.title()} (chuẩn hoá theo bài)",
#             hover_data=["#tracks"],
#             labels={"main_genre": "Thể loại", feature: feature, "#tracks": "Số bài (unique)"}
#         )
#         fig_genre.update_layout(
#             xaxis_title="Thể loại",
#             yaxis_title=feature,
#             xaxis_tickangle=-45
#         )
#         st.plotly_chart(fig_genre, use_container_width=True)

#     # ============================================================
#     # 4) Nghệ sĩ & Bài hát nổi bật
#     # ============================================================
#     st.subheader("🌟 Nghệ sĩ & Bài hát nổi bật")
#     choice = st.radio(
#         "Chọn tiêu chí hiển thị:",
#         ["Top 10 Nghệ sĩ", "Top 10 Bài hát"],
#         horizontal=True,
#         key=f"choice_{country_name}"
#     )

#     if choice == "Top 10 Bài hát" and {"song", "main_genre", "popularity"}.issubset(df.columns):
#         top_song = (
#             df.groupby(["song", "main_genre"])["popularity"]
#               .mean()
#               .sort_values(ascending=False)
#               .head(10)
#               .reset_index()
#         )

#         fig_song = px.bar(
#             top_song,
#             x="popularity",
#             y="song",
#             color="popularity",
#             color_continuous_scale="Greens",
#             orientation="h",
#             title="🎵 Top 10 Bài Hát Phổ Biến Nhất",
#             labels={
#                 "popularity": "Popularity TB",
#                 "song": "Bài hát",
#                 "popularity": "Độ nổi (0–100)"
#             },
#             hover_data=["main_genre"]
#         )
#         fig_song.update_yaxes(autorange="reversed")
#         fig_song.update_coloraxes(colorbar_title="Độ nổi")
#         st.plotly_chart(fig_song, use_container_width=True)

#     if choice == "Top 10 Nghệ sĩ" and "artist" in df.columns and "song" in df.columns:
#         artist_song = (
#             df[["artist", "song"]]
#               .dropna()
#               .assign(artist_list=lambda d: d["artist"].apply(_split_artists))
#               .explode("artist_list")
#               .drop(columns=["artist"])
#               .rename(columns={"artist_list": "artist"})
#               .drop_duplicates()
#         )

#         top_artist = (
#             artist_song.groupby("artist")["song"].nunique()
#                        .sort_values(ascending=False)
#                        .head(10)
#                        .reset_index(name="tracks")
#         )

#         fig_artist = px.bar(
#             top_artist,
#             x="tracks",
#             y="artist",
#             orientation="h",
#             color="tracks",
#             color_continuous_scale="Greens",
#             title=f"🎤 Top 10 Nghệ Sĩ Có Nhiều Bài Nhất ({country_name})",
#             labels={"tracks": "Số bài (unique)", "artist": "Nghệ sĩ"}
#         )
#         fig_artist.update_layout(xaxis_title="Số bài (unique)", yaxis_title="Nghệ sĩ")
#         fig_artist.update_yaxes(autorange="reversed")
#         st.plotly_chart(fig_artist, use_container_width=True)

#         st.subheader("👥 Tỷ lệ Nghệ sĩ Solo vs Collaboration")
#         df_collab = df.copy()
#         df_collab["collab_type"] = df_collab["artist"].apply(
#             lambda s: "Collab" if len(_split_artists(s)) > 1 else "Solo"
#         )
#         collab_count = df_collab["collab_type"].value_counts().reset_index()
#         collab_count.columns = ["Type", "Count"]
#         fig_collab = px.pie(
#             collab_count,
#             values="Count",
#             names="Type",
#             color="Type",
#             color_discrete_map={"Solo": "#1DB954", "Collab": "#5ed88d"},
#             title="Tỷ lệ Bài Hát Solo vs Collaboration"
#         )
#         st.plotly_chart(fig_collab, use_container_width=True)

#     elif choice == "Top 10 Bài hát" and {"song", "main_genre", "popularity"}.issubset(df.columns):
#         if "is_explicit" in df.columns:
#             st.subheader("🚫 Tỷ lệ Explicit vs Clean")
#             explicit_ratio = df["is_explicit"].value_counts(dropna=False).reset_index()
#             explicit_ratio.columns = ["Explicit", "Count"]
#             explicit_ratio["Label"] = explicit_ratio["Explicit"].map({1: "Explicit", 0: "Clean"})
#             fig_explicit = px.pie(
#                 explicit_ratio, values="Count", names="Label", hole=0.4,
#                 color="Label",
#                 color_discrete_map={"Explicit": "#1DB954", "Clean": "#b3e8c8"},
#                 title="Tỷ lệ Bài Hát Có Nội Dung Explicit"
#             )
#             st.plotly_chart(fig_explicit, use_container_width=True)

#     # 🔥 Popularity Trend
#     if "date" in df.columns:
#         st.subheader("🔥 Biến động độ hot theo thời gian")
#         songs_available = df["song"].value_counts().head(50).index.tolist()
#         selected_songs = st.multiselect(
#             "🎵 Chọn 1 hoặc nhiều bài để so sánh:",
#             options=songs_available,
#             default=songs_available[:1],
#             key=f"multi_song_{country_name}"
#         )
#         if selected_songs:
#             song_df = df[df["song"].isin(selected_songs)].sort_values("date")
#             if not song_df.empty:
#                 fig_hot = px.line(
#                     song_df,
#                     x="date",
#                     y="popularity",
#                     color="song",
#                     markers=True,
#                     title="🔥 Popularity theo thời gian (So sánh nhiều bài)",
#                     labels={"popularity": "Popularity", "date": "date", "song": "Bài hát"},
#                 )
#                 st.plotly_chart(fig_hot, use_container_width=True)

#     # 📈 Longevity vs Rank
#     if {"position", "date", "song"}.issubset(df.columns):
#         st.subheader("📈 Độ bền & Thứ hạng (Longevity vs Peak Rank)")
#         song_stats = (
#             df.groupby("song")
#               .agg(
#                   best_rank=("position", "min"),
#                   first_date=("date", "min"),
#                   last_date=("date", "max"),
#               )
#               .reset_index()
#         )
#         song_stats["days_on_chart"] = (
#             song_stats["last_date"] - song_stats["first_date"]
#         ).dt.days + 1
#         song_stats = song_stats[song_stats["days_on_chart"].notna()]

#         fig_longevity = px.scatter(
#             song_stats,
#             x="best_rank",
#             y="days_on_chart",
#             hover_data=["song"],
#             color="best_rank",
#             color_continuous_scale="Greens_r",
#             title="⏳ Độ Bền Bài Hát vs Thứ Hạng Cao Nhất",
#             labels={
#                 "best_rank": "Best Rank (nhỏ là tốt)",
#                 "days_on_chart": "Số ngày xuất hiện",
#             },
#         )
#         fig_longevity.update_xaxes(autorange="reversed")
#         st.plotly_chart(fig_longevity, use_container_width=True)

#     # 🎚️ Boxplot
#     if {"energy", "danceability", "valence", "tempo"}.issubset(df.columns):
#         st.subheader("🎚️ Phân bố các đặc trưng âm nhạc")
#         melted = df.melt(
#             value_vars=["energy", "danceability", "valence", "tempo"],
#             var_name="Feature", value_name="Value"
#         )
#         fig_box = px.box(
#             melted, x="Feature", y="Value", color="Feature",
#             color_discrete_sequence=px.colors.sequential.Greens,
#             title="Phân bố Đặc Trưng Âm Nhạc Trong Top 50"
#         )
#         st.plotly_chart(fig_box, use_container_width=True)

#     # ============================================================
#     # 8) Bảng dữ liệu gốc + bộ lọc & link Spotify
#     # ============================================================
#     st.subheader("📋 Dữ liệu Gốc")

#     show_cols = [
#         c for c in ["date", "position", "song", "artist",
#                     "main_genre", "popularity", "is_explicit", "href"]
#         if c in df.columns
#     ]

#     base_df = df.copy()
#     if {"date", "position"}.issubset(df.columns):
#         base_df = base_df.sort_values(["date", "position"])
#     base_df = base_df[show_cols]

#     with st.expander("🔎 Bộ lọc dữ liệu", expanded=True):
#         global_search = st.text_input("🔍 Tìm kiếm nhanh (tất cả cột)", "")
#         st.caption("Lọc theo từng cột (substring, không phân biệt hoa thường):")
#         col_widgets = st.columns(len(show_cols))
#         col_filters = {}
#         for ui_col, col_name in zip(col_widgets, show_cols):
#             col_filters[col_name] = ui_col.text_input(
#                 col_name, key=f"filter_{col_name}"
#             )

#     filtered_df = base_df.copy()

#     if global_search:
#         mask = pd.Series(False, index=filtered_df.index)
#         for c in show_cols:
#             mask |= filtered_df[c].astype(str).str.contains(
#                 global_search, case=False, na=False
#             )
#         filtered_df = filtered_df[mask]

#     for c, val in col_filters.items():
#         if val:
#             filtered_df = filtered_df[
#                 filtered_df[c].astype(str).str.contains(val, case=False, na=False)
#             ]

#     # 👉 Chuẩn bị hiển thị: ẩn index + biến href thành LinkColumn
#     df_show = filtered_df.reset_index(drop=True).copy()
#     if "href" in df_show.columns:
#         df_show["href"] = df_show["href"].replace("None", None)

#         st.data_editor(
#             df_show,
#             hide_index=True,
#             use_container_width=True,
#             column_config={
#                 "href": st.column_config.LinkColumn(
#                     "Spotify",
#                     display_text="Mở trên Spotify"
#                 )
#             },
#         )
#     else:
#         st.dataframe(df_show, use_container_width=True)

#     st.markdown("---")
#     st.caption(f"🎵 Spotify Top 50 — {country_name}")
#     st.caption("📊 Dữ liệu từ MongoDB Atlas – database `spotify_project`")



# # =========================
# # ▶️ Chạy độc lập
# # =========================
# if __name__ == "__main__":
#     render_country_dashboard()