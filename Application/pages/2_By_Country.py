# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from pymongo import MongoClient
# from datetime import datetime

# # =========================
# # ⚙️ 1️⃣ Cấu hình giao diện
# # =========================
# st.set_page_config(page_title="Spotify Top 50 — Country Dashboard", layout="wide")
# st.title("🌍 Spotify Top 50 – Phân tích theo quốc gia")

# # 🎨 Spotify Dashboard Theme
# st.markdown("""
# <style>
# body { background-color: #F9F9F9; color: #222; font-family: "Poppins", sans-serif; }
# h1, h2, h3, h4 { color: #1DB954; font-weight: 600; }
# [data-testid="stMetricLabel"] { color: #1DB954 !important; }
# [data-testid="stMetricValue"] { color: #0a8f44 !important; font-weight: bold; }
# div[data-testid="stPlotlyChart"] {
#     border-radius: 12px; background: #ffffff;
#     box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 10px;
# }
# [data-testid="stDataFrame"] table { border-radius: 10px; border: 1px solid #e5e5e5; }
# thead tr th {
#     background-color: #E8F8EF !important; color: #0a8f44 !important;
#     font-weight: 600 !important;
# }
# tbody tr:hover { background-color: #F2FFF8 !important; }
# .stRadio > label { color: #1DB954 !important; font-weight: 600; }
# .stSelectbox label { color: #1DB954 !important; }
# </style>
# """, unsafe_allow_html=True)

# # =========================
# # 2️⃣ Chọn quốc gia
# # =========================
# if "selected_country" in st.session_state:
#     default_country = st.session_state["selected_country"]
# else:
#     default_country = "France"

# country_name = st.selectbox(
#     "🌍 Chọn quốc gia để phân tích",
#     ["France", "Italy", "Japan", "Mexico", "South Korea", "Spain", "Argentina"],
#     index=["France", "Italy", "Japan", "Mexico", "South Korea", "Spain", "Argentina"].index(default_country)
# )
# st.success(f"🎧 Đang xem dữ liệu cho **{country_name}**")

# # =========================
# # 3️⃣ Kết nối MongoDB
# # =========================
# uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# client = MongoClient(uri)
# db = client["spotify_project"]

# collection_name = f"top50_{country_name.lower().replace(' ', '_')}"
# collection = db[collection_name]
# @st.cache_data(ttl=3600)
# def load_data(country):
#     collection_name = f"top50_{country.lower().replace(' ', '_')}"
#     collection = db[collection_name]
#     data = list(collection.find({}, {"_id": 0}))
#     return pd.DataFrame(data)

# df = load_data(country_name)

# if df.empty:
#     st.error(f"🚫 Không có dữ liệu cho {country_name}.")
#     st.stop()

# # =========================
# # 4️⃣ Làm sạch dữ liệu
# # =========================
# numeric_cols = ["energy","danceability","valence","tempo","popularity","position","is_explicit"]
# for col in numeric_cols:
#     df[col] = pd.to_numeric(df[col], errors="coerce")
# if "date" in df.columns:
#     df["date"] = pd.to_datetime(df["date"], errors="coerce")

# # =========================
# # 5️⃣ Tổng quan
# # =========================
# st.subheader("📊 Tổng quan dữ liệu")
# col1, col2, col3, col4 = st.columns(4)
# col1.metric("🎵 Số bài hát", len(df))
# col2.metric("👩‍🎤 Số nghệ sĩ", df["artist"].nunique())
# col3.metric("🎶 Số thể loại", df["main_genre"].nunique())
# col4.metric("🔥 Độ phổ biến TB", round(df["popularity"].mean(), 1))

# # =========================
# # 6️⃣ Xu hướng thể loại
# # =========================
# st.subheader("🎧 Xu hướng thể loại")
# feature = st.selectbox("Chọn đặc trưng âm nhạc", ["energy","danceability","valence","tempo","popularity"])
# genre_avg = df.groupby("main_genre")[feature].mean().sort_values(ascending=False).reset_index()
# fig_genre = px.bar(genre_avg, x="main_genre", y=feature, color=feature,
#                    color_continuous_scale="greens", title=f"Top Thể Loại Theo {feature.title()}")
# st.plotly_chart(fig_genre, use_container_width=True)

# # =========================
# # 7️⃣ Nghệ sĩ & Bài hát nổi bật
# # =========================
# st.subheader("🌟 Nghệ sĩ & Bài hát nổi bật")
# choice = st.radio("Chọn tiêu chí hiển thị:", ["Top 10 Nghệ sĩ", "Top 10 Bài hát"], horizontal=True)

# if choice == "Top 10 Nghệ sĩ":
#     top_artist = df["artist"].value_counts().head(10)
#     fig_artist = px.bar(x=top_artist.values, y=top_artist.index,
#                         orientation="h", color=top_artist.values,
#                         color_continuous_scale="Greens",
#                         title="🎤 Top 10 Nghệ Sĩ Có Nhiều Track Nhất")
#     st.plotly_chart(fig_artist, use_container_width=True)
    
#     # 🎯 Solo vs Collab
#     st.subheader("👥 Tỷ lệ Nghệ sĩ Solo vs Collaboration")
#     df["collab_type"] = df["artist"].apply(lambda x: "Collab" if "," in x or "&" in x else "Solo")
#     collab_count = df["collab_type"].value_counts().reset_index()
#     collab_count.columns = ["Type", "Count"]
#     fig_collab = px.pie(collab_count, values="Count", names="Type",
#                         color="Type", color_discrete_map={"Solo":"#1DB954","Collab":"#5ed88d"},
#                         title="Tỷ lệ Bài Hát Solo vs Collaboration")
#     st.plotly_chart(fig_collab, use_container_width=True)

# else:
#     top_song = df.groupby(["song","main_genre"])["popularity"].mean().sort_values(ascending=False).head(10).reset_index()
#     fig_song = px.bar(top_song, x="popularity", y="song", color="main_genre",
#                       orientation="h", title="🎵 Top 10 Bài Hát Phổ Biến Nhất (Theo Thể Loại)",
#                       color_discrete_sequence=px.colors.sequential.Greens)
#     st.plotly_chart(fig_song, use_container_width=True)
    
#     # 🚫 Explicit ratio
#     st.subheader("🚫 Tỷ lệ Explicit vs Non-Explicit")
#     explicit_ratio = df["is_explicit"].value_counts().reset_index()
#     explicit_ratio.columns = ["Explicit","Count"]
#     explicit_ratio["Label"] = explicit_ratio["Explicit"].map({1:"Explicit",0:"Clean"})
#     fig_explicit = px.pie(explicit_ratio, values="Count", names="Label", hole=0.4,
#                           color="Label", color_discrete_map={"Explicit":"#1DB954","Clean":"#b3e8c8"},
#                           title="Tỷ lệ Bài Hát Có Nội Dung Explicit")
#     st.plotly_chart(fig_explicit, use_container_width=True)

# # =========================
# # (các phần còn lại giữ nguyên — Seasonal, Longevity, Time-series, Boxplot...)
# # =========================
# # (toàn bộ logic biểu đồ gốc vẫn chạy bình thường, chỉ thay đổi phần chọn quốc gia)


# # =========================
# # 8️⃣ Seasonal Pattern
# # =========================
# if "date" in df.columns:
#     st.subheader("🌤️ Đặc trưng âm nhạc theo mùa (Seasonal Patterns)")
#     df["month"] = df["date"].dt.month
#     df["season"] = df["month"].map({
#         12:"Winter",1:"Winter",2:"Winter",
#         3:"Spring",4:"Spring",5:"Spring",
#         6:"Summer",7:"Summer",8:"Summer",
#         9:"Autumn",10:"Autumn",11:"Autumn"
#     })
#     season_avg = df.groupby("season")[["energy","danceability","valence"]].mean().reset_index()
#     fig_season = px.bar(season_avg, x="season", y=["energy","danceability","valence"],
#                         barmode="group", title="Đặc Trưng Âm Nhạc Trung Bình Theo Mùa",
#                         color_discrete_sequence=px.colors.sequential.Greens)
#     st.plotly_chart(fig_season, use_container_width=True)

# # =========================
# # 9️⃣ Longevity vs Peak Rank
# # =========================
# if "position" in df.columns and "date" in df.columns:
#     st.subheader("📈 Phân tích độ bền & Thứ hạng (Longevity vs Peak Rank)")
#     song_stats = df.groupby("song").agg({
#         "position": "min",
#         "date": lambda x: (x.max() - x.min()).days
#     }).reset_index().rename(columns={"position":"best_rank","date":"days_on_chart"})
#     fig_longevity = px.scatter(song_stats, x="best_rank", y="days_on_chart",
#                                hover_data=["song"], color="best_rank",
#                                title="⏳ Độ Bền Bài Hát vs Thứ Hạng Cao Nhất",
#                                color_continuous_scale="Greens_r")
#     fig_longevity.update_xaxes(autorange="reversed")
#     st.plotly_chart(fig_longevity, use_container_width=True)

# # =========================
# # 🔥 10️⃣ Song Popularity Trend
# # =========================
# if "date" in df.columns:
#     st.subheader("🔥 Biến động độ hot của bài hát trong năm 2025")
#     songs_available = df["song"].value_counts().head(30).index.tolist()
#     selected_song = st.selectbox("🎵 Chọn bài hát để xem độ hot:", songs_available)
#     song_df = df[df["song"] == selected_song].sort_values("date")
#     if not song_df.empty:
#         fig_hot = px.line(song_df, x="date", y="popularity", markers=True,
#                           title=f"🔥 Độ Hot của '{selected_song}' theo thời gian",
#                           color_discrete_sequence=["#1DB954"])
#         st.plotly_chart(fig_hot, use_container_width=True)

#     # Multi-song trend (Top 5)
#     st.subheader("📊 So sánh Top 5 bài hot nhất theo thời gian")
#     top5 = df.groupby("song")["popularity"].mean().sort_values(ascending=False).head(5).index
#     top5_df = df[df["song"].isin(top5)]
#     fig_multi = px.line(top5_df, x="date", y="popularity", color="song",
#                         title="Biến động độ hot của Top 5 bài hát phổ biến nhất",
#                         color_discrete_sequence=px.colors.sequential.Greens)
#     st.plotly_chart(fig_multi, use_container_width=True)

# # =========================
# # 11️⃣ Genre Heatmap theo tháng
# # =========================
# if "date" in df.columns:
#     st.subheader("🎶 Phân bố thể loại theo thời gian")
#     df["month"] = df["date"].dt.to_period("M").astype(str)
#     genre_month = df.groupby(["month","main_genre"]).size().reset_index(name="count")
#     fig_heat = px.density_heatmap(genre_month, x="month", y="main_genre", z="count",
#                                   color_continuous_scale="greens",
#                                   title="Phân Bố Thể Loại Theo Tháng")
#     st.plotly_chart(fig_heat, use_container_width=True)

# # =========================
# # 12️⃣ Boxplot đặc trưng âm nhạc
# # =========================
# st.subheader("🎚️ Phân bố các đặc trưng âm nhạc")
# melted = df.melt(value_vars=["energy","danceability","valence","tempo"],
#                  var_name="Feature", value_name="Value")
# fig_box = px.box(melted, x="Feature", y="Value", color="Feature",
#                  color_discrete_sequence=px.colors.sequential.Greens,
#                  title="Phân bố Đặc Trưng Âm Nhạc Trong Top 50")
# st.plotly_chart(fig_box, use_container_width=True)

# # =========================
# # 13️⃣ Bảng dữ liệu gốc
# # =========================
# st.subheader("📋 Dữ liệu Top 50 Gốc")
# show_cols = ["date","position","song","artist","main_genre","popularity","is_explicit","href"]
# st.dataframe(df[show_cols].sort_values("position"), use_container_width=True)

# # =========================
# # 📎 Footer
# # =========================
# st.markdown("---")
# st.caption(f"🎵 Spotify Top 50 — {country_name}")
# st.caption("📊 Dữ liệu phân tích từ MongoDB Atlas – database `spotify_project`")


import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime

# =========================
# ⚙️ 1️⃣ Cấu hình giao diện + Theme Spotify
# =========================
st.set_page_config(page_title="Spotify Top 50 — Country Dashboard", layout="wide")

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
    background-color: #E8F8EF !important; color: #0a8f44 !important;
    font-weight: 600 !important;
}
tbody tr:hover { background-color: #F2FFF8 !important; }
.stRadio > label { color: #1DB954 !important; font-weight: 600; }
.stSelectbox label { color: #1DB954 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# 💚 2️⃣ HÀM CHÍNH HIỂN THỊ DASHBOARD
# =========================
def render_country_dashboard(country_name=None):

    # 1️⃣ Lấy quốc gia từ session_state (nếu có)
    # =========================
    if "selected_country" in st.session_state and country_name is None:
        country_name = st.session_state["selected_country"]
        
    # =========================
    # 1️⃣ Thanh chọn quốc gia (chỉ hiển thị nếu chạy độc lập)
    # =========================
    available_countries = [
        "United_States","France", "Italy", "Japan", "Mexico", "South Korea", "Spain", "Argentina"
    ]
    if country_name is None:
        country_name = st.selectbox("🌍 Chọn quốc gia để phân tích", available_countries, index=0)
        st.success(f"🎧 Đang xem dữ liệu cho **{country_name}**")
    else:
        st.success(f"🎧 Đang hiển thị dữ liệu cho **{country_name}**")

    # =========================
    # 2️⃣ Kết nối MongoDB
    # =========================
    uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client["spotify_project"]
    collection_name = f"top50_{country_name.lower().replace(' ', '_')}"
    collection = db[collection_name]

    # =========================
    # 3️⃣ Load dữ liệu
    # =========================
    @st.cache_data(ttl=3600)
    def load_data(country):
        data = list(collection.find({}, {"_id": 0}))
        return pd.DataFrame(data)

    df = load_data(country_name)
    if df.empty:
        st.warning(f"⚠️ Không có dữ liệu cho {country_name}.")
        return

    # =========================
    # 4️⃣ Làm sạch dữ liệu
    # =========================
    numeric_cols = ["energy","danceability","valence","tempo","popularity","position","is_explicit"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # =========================
    # 5️⃣ Tổng quan
    # =========================
    st.title(f"🌍 Spotify Top 50 – {country_name} Dashboard")
    st.subheader("📊 Tổng quan dữ liệu")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎵 Số bài hát", len(df))
    col2.metric("👩‍🎤 Số nghệ sĩ", df["artist"].nunique())
    col3.metric("🎶 Số thể loại", df["main_genre"].nunique())
    col4.metric("🔥 Độ phổ biến TB", round(df["popularity"].mean(), 1))

    # =========================
    # 6️⃣ Xu hướng thể loại
    # =========================
    st.subheader("🎧 Xu hướng thể loại")
    feature = st.selectbox("Chọn đặc trưng âm nhạc", ["energy","danceability","valence","tempo","popularity"], key=f"feature_{country_name}")
    genre_avg = df.groupby("main_genre")[feature].mean().sort_values(ascending=False).reset_index()
    fig_genre = px.bar(genre_avg, x="main_genre", y=feature, color=feature,
                       color_continuous_scale="greens", title=f"Top Thể Loại Theo {feature.title()}")
    st.plotly_chart(fig_genre, use_container_width=True)

    # =========================
    # 7️⃣ Nghệ sĩ & Bài hát nổi bật
    # =========================
    st.subheader("🌟 Nghệ sĩ & Bài hát nổi bật")
    choice = st.radio("Chọn tiêu chí hiển thị:", ["Top 10 Nghệ sĩ", "Top 10 Bài hát"], horizontal=True, key=f"choice_{country_name}")

    if choice == "Top 10 Nghệ sĩ":
        top_artist = df["artist"].value_counts().head(10)
        fig_artist = px.bar(x=top_artist.values, y=top_artist.index,
                            orientation="h", color=top_artist.values,
                            color_continuous_scale="Greens",
                            title=f"🎤 Top 10 Nghệ Sĩ Có Nhiều Track Nhất ({country_name})")
        st.plotly_chart(fig_artist, use_container_width=True)
        
        # 🎯 Solo vs Collab
        st.subheader("👥 Tỷ lệ Nghệ sĩ Solo vs Collaboration")
        df["collab_type"] = df["artist"].apply(lambda x: "Collab" if "," in x or "&" in x else "Solo")
        collab_count = df["collab_type"].value_counts().reset_index()
        collab_count.columns = ["Type", "Count"]
        fig_collab = px.pie(collab_count, values="Count", names="Type",
                            color="Type", color_discrete_map={"Solo":"#1DB954","Collab":"#5ed88d"},
                            title="Tỷ lệ Bài Hát Solo vs Collaboration")
        st.plotly_chart(fig_collab, use_container_width=True)

    else:
        top_song = df.groupby(["song","main_genre"])["popularity"].mean().sort_values(ascending=False).head(10).reset_index()
        fig_song = px.bar(top_song, x="popularity", y="song", color="main_genre",
                          orientation="h", title="🎵 Top 10 Bài Hát Phổ Biến Nhất (Theo Thể Loại)",
                          color_discrete_sequence=px.colors.sequential.Greens)
        st.plotly_chart(fig_song, use_container_width=True)
        
        # 🚫 Explicit ratio
        st.subheader("🚫 Tỷ lệ Explicit vs Non-Explicit")
        explicit_ratio = df["is_explicit"].value_counts().reset_index()
        explicit_ratio.columns = ["Explicit","Count"]
        explicit_ratio["Label"] = explicit_ratio["Explicit"].map({1:"Explicit",0:"Clean"})
        fig_explicit = px.pie(explicit_ratio, values="Count", names="Label", hole=0.4,
                              color="Label", color_discrete_map={"Explicit":"#1DB954","Clean":"#b3e8c8"},
                              title="Tỷ lệ Bài Hát Có Nội Dung Explicit")
        st.plotly_chart(fig_explicit, use_container_width=True)

    # =========================
    # 🔥 Popularity Trend
    # =========================
    if "date" in df.columns:
        st.subheader("🔥 Biến động độ hot theo thời gian")
        songs_available = df["song"].value_counts().head(20).index.tolist()
        selected_song = st.selectbox("🎵 Chọn bài hát để xem độ hot:", songs_available, key=f"song_{country_name}")
        song_df = df[df["song"] == selected_song].sort_values("date")

        if not song_df.empty:
            fig_hot = px.line(song_df, x="date", y="popularity", markers=True,
                              color_discrete_sequence=["#1DB954"],
                              title=f"🔥 Độ Hot của '{selected_song}' theo thời gian")
            st.plotly_chart(fig_hot, use_container_width=True)

    # =========================
    # 📈 Longevity vs Rank
    # =========================
    if "position" in df.columns and "date" in df.columns:
        st.subheader("📈 Độ bền & Thứ hạng (Longevity vs Peak Rank)")
        song_stats = df.groupby("song").agg({
            "position": "min",
            "date": lambda x: (x.max() - x.min()).days
        }).reset_index().rename(columns={"position":"best_rank","date":"days_on_chart"})
        fig_longevity = px.scatter(song_stats, x="best_rank", y="days_on_chart",
                                   hover_data=["song"], color="best_rank",
                                   color_continuous_scale="Greens_r",
                                   title="⏳ Độ Bền Bài Hát vs Thứ Hạng Cao Nhất")
        fig_longevity.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_longevity, use_container_width=True)

    # =========================
    # 🎚️ Boxplot Features
    # =========================
    st.subheader("🎚️ Phân bố các đặc trưng âm nhạc")
    melted = df.melt(value_vars=["energy","danceability","valence","tempo"],
                     var_name="Feature", value_name="Value")
    fig_box = px.box(melted, x="Feature", y="Value", color="Feature",
                     color_discrete_sequence=px.colors.sequential.Greens,
                     title="Phân bố Đặc Trưng Âm Nhạc Trong Top 50")
    st.plotly_chart(fig_box, use_container_width=True)

    # =========================
    # 📋 Dữ liệu Gốc
    # =========================
    st.subheader("📋 Dữ liệu Gốc")
    show_cols = ["date","position","song","artist","main_genre","popularity","is_explicit","href"]
    st.dataframe(df[show_cols].sort_values("position"), use_container_width=True)

    # Footer
    st.markdown("---")
    st.caption(f"🎵 Spotify Top 50 — {country_name}")
    st.caption("📊 Dữ liệu từ MongoDB Atlas – database `spotify_project`")

# =========================
# ⚙️ 3️⃣ Chạy độc lập
# =========================
if __name__ == "__main__":
    render_country_dashboard()