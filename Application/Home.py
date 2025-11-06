# =========================
# 🌍 GLOBAL MUSIC ANALYTICS DASHBOARD
# =========================

import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import datetime
# ------------------------------
# 1️⃣ Kết nối MongoDB
# ------------------------------
MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "spotify_project"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

@st.cache_data
def load_data():
    album_df = pd.DataFrame(list(db["album_stats_global_2"].find()))
    top50_df = pd.DataFrame(list(db["top50_world"].find()))

    # Chuẩn hóa tên cột
    if "Genre" not in album_df.columns and "genre" in album_df.columns:
        album_df.rename(columns={"genre": "Genre"}, inplace=True)

    if "Release Date" in album_df.columns:
        album_df["Release Date"] = pd.to_datetime(album_df["Release Date"], errors="coerce")
        album_df["Release Year"] = album_df["Release Date"].dt.year
    elif "Release Year" not in album_df.columns:
        album_df["Release Year"] = pd.NA

    # Chuyển kiểu dữ liệu numeric
    for col in ["Total Streams (Millions)", "popularity", "energy", "danceability"]:
        if col in album_df.columns:
            album_df[col] = pd.to_numeric(album_df[col], errors="coerce")
        if col in top50_df.columns:
            top50_df[col] = pd.to_numeric(top50_df[col], errors="coerce")

    return album_df, top50_df

album_df, top50_df = load_data()

st.markdown("---")
st.header("🌎 Global Music Analytics – Spotify & Billboard Trends")

# ------------------------------
# 3️⃣ Bộ lọc
# ------------------------------
col1, col2, col3 = st.columns([1, 1, 1])

album_type_filter = col1.selectbox(
    "🎵 Chọn loại sản phẩm:",
    ["Tất cả", "album", "single"]
)


# ------------------------------
# 4️⃣ Phân tích theo album
# ------------------------------
if album_type_filter == "album":
    st.subheader("📊 Phân tích xu hướng theo album")

    trend_filter = col2.selectbox(
        "📈 Phân tích xu hướng theo:",
        [
            "Genre", "Release Year", "Release Date", "Popularity", "Country", "Label",
            "Total Streams (Millions)", "Streams Last 30 Days (Millions)", "Monthly Listeners"
        ]
    )

    # --- 1. Theo thể loại (Genre)
    if trend_filter == "Genre":
        trend_filter_2 = col3.selectbox(
                "📈 Phân tích xu hướng theo:",
                ["Time Series", "Skip Rate"]
        )
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
        if trend_filter_2 == "Time Series":
                st.subheader("📅 Xu hướng thể loại được nghe nhiều nhất theo ngày phát hành")

                if all(col in album_df.columns for col in ["releaseDate", "Genre", "Total Streams (Millions)"]):
                    ts_df = album_df.dropna(subset=["releaseDate", "Genre", "Total Streams (Millions)"]).copy()

                    # Đảm bảo releaseDate là kiểu datetime
                    ts_df["releaseDate"] = pd.to_datetime(ts_df["releaseDate"], errors="coerce")
                    ts_df = ts_df.dropna(subset=["releaseDate"])

                    # Gom nhóm theo khoảng 6 tháng và thể loại
                    ts_df["Period"] = ts_df["releaseDate"].dt.to_period("6M").dt.to_timestamp()
                    grouped = (
                        ts_df.groupby(["Period", "Genre"])["Total Streams (Millions)"]
                        .sum()
                        .reset_index()
                    )

                    # Tìm thể loại top trong mỗi khoảng 6 tháng
                    top_genres_by_period = grouped.loc[
                        grouped.groupby("Period")["Total Streams (Millions)"].idxmax()
                    ].reset_index(drop=True)

                    # Vẽ biểu đồ
                    fig_ts = px.bar(
                        top_genres_by_period,
                        x="Period",
                        y="Total Streams (Millions)",
                        color="Genre",
                        title="🎶 Thể loại album được nghe nhiều nhất theo ngày phát hành",
                        labels={
                            "Period": "Khoảng thời gian",
                            "Total Streams (Millions)": "Tổng lượt nghe (triệu)",
                            "Genre": "Thể loại"
                        },
                    )
                    st.plotly_chart(fig_ts, use_container_width=True)

                else:
                    st.info("Dữ liệu không có đủ các cột 'releaseDate', 'Genre' hoặc 'Total Streams (Millions)'.")
        elif trend_filter_2 == "Skip Rate":
            df_skip = album_df.dropna(subset=["Genre", "Skip Rate (%)"])
            fig = px.box(
                df_skip,
                x="Genre",
                y="Skip Rate (%)",
                title="🎧 Phân bố tỷ lệ bỏ qua (Skip Rate) theo thể loại",
                color="Genre",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            fig.update_layout(
                xaxis_title="Thể loại",
                yaxis_title="Tỷ lệ bỏ qua (%)",
                showlegend=False,
                template="plotly_white",
                margin=dict(l=40, r=20, t=80, b=100)
            )

            st.plotly_chart(fig, use_container_width=True)


    # --- 2. Theo năm phát hành (Release Year)
    elif trend_filter == "Release Year":
        fig = px.histogram(
            album_df.dropna(subset=["release_year"]),
            x="Release Year",
            nbins=20,
            title="📅 Phân bố năm phát hành album",
            color_discrete_sequence=["#4C78A8"]
        )
        fig.update_layout(xaxis_title="Năm phát hành", yaxis_title="Số lượng album")
        st.plotly_chart(fig, use_container_width=True)

    # --- 3. Theo ngày phát hành (Release Date)
    elif trend_filter == "Release Date":
        album_df["releaseDate"] = pd.to_datetime(album_df["releaseDate"], errors="coerce")
        df_sorted = album_df.dropna(subset=["releaseDate"]).sort_values("releaseDate")

        fig = px.line(
            df_sorted,
            x="releaseDate",
            y="popularity",
            title="📆 Xu hướng độ phổ biến theo ngày phát hành",
            markers=True,
            color_discrete_sequence=["#E45756"]
        )
        fig.update_layout(xaxis_title="Ngày phát hành", yaxis_title="Mức độ phổ biến")
        st.plotly_chart(fig, use_container_width=True)

    # --- 4. Theo độ phổ biến (Popularity)
    elif trend_filter == "Popularity":
        show_all_albums = col3.checkbox("📊 Album name", value=False)

        if show_all_albums:
            # Kiểm tra dữ liệu
            if all(col in album_df.columns for col in ["Album", "Artist", "popularity"]):
                # Loại bỏ dữ liệu null
                plot_df = album_df.dropna(subset=["Album", "Artist", "popularity"])

                # Vẽ biểu đồ scatter: mỗi điểm là một album
                fig_all = px.scatter(
                    plot_df,
                    x="Artist",
                    y="popularity",
                    color="popularity",
                    hover_data=["Album", "Artist"],
                    color_continuous_scale="Viridis",
                    title="📈 Độ phổ biến của các album theo nghệ sĩ",
                )
                fig_all.update_layout(
                    xaxis_title="Nghệ sĩ",
                    yaxis_title="Độ phổ biến",
                    height=700,
                    xaxis={'categoryorder': 'total descending'}
                )
                st.plotly_chart(fig_all, use_container_width=True)
            else:
                st.warning("⚠️ Dữ liệu không có đủ cột 'Album', 'Artist' hoặc 'popularity'.")
        # Biểu đồ phân bố độ phổ biến (chung)
        fig = px.histogram(
            album_df,
            x="popularity",
            nbins=30,
            title="🔥 Phân bố độ phổ biến của album",
            color_discrete_sequence=["#72B7B2"]
        )
        fig.update_layout(xaxis_title="Độ phổ biến", yaxis_title="Số lượng album")
        st.plotly_chart(fig, use_container_width=True)

        # Nếu bật checkbox → hiển thị chi tiết từng album


    # --- 5. Theo quốc gia (Country)
    elif trend_filter == "Country":
        trend_filter_2 = col3.selectbox(
            "📈 Phân tích xu hướng theo:",
            ["Số lượng album", "Popularity", "Total Streams (Millions)","Monthly Listeners","Streams Last 30 Days (Millions)","Skip Rate"]
        )

        if trend_filter_2 == "Popularity":
            fig = px.box(
                album_df,
                x="Country",
                y="popularity",
                title="🌍 Độ phổ biến theo quốc gia",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Total Streams (Millions)":
            fig = px.box(
                album_df,
                x="Country",
                y="Total Streams (Millions)",
                title="🌍 Tổng lượt stream theo quốc gia",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Monthly Listeners":
            fig = px.box(
                album_df,
                x="Country",
                y="Monthly Listeners (Millions)",
                title="🌍 Lượt nghe hàng tháng theo quốc gia",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Streams Last 30 Days (Millions)":
            fig = px.box(
                album_df,
                x="Country",
                y="Streams Last 30 Days (Millions)",
                title="🌍 Lượt stream 30 ngày gần nhất theo quốc gia",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Skip Rate":
            df_skip = album_df.dropna(subset=["Country", "Skip Rate (%)"])
            fig = px.box(
                df_skip,
                x="Country",
                y="Skip Rate (%)",
                title="🌍 Phân bố tỷ lệ bỏ qua (Skip Rate) theo quốc gia",
                color="Country",
                color_discrete_sequence=px.colors.qualitative.Vivid,
            )

            fig.update_layout(
                xaxis_title="Quốc gia",
                yaxis_title="Tỷ lệ bỏ qua (%)",
                showlegend=False,
                template="plotly_white",
                margin=dict(l=40, r=20, t=80, b=100)
            )

            # Hiển thị biểu đồ trên Streamlit
            st.plotly_chart(fig, use_container_width=True)
        country_counts = album_df["Country"].value_counts().head(10)
        fig = px.bar(
            x=country_counts.index,
            y=country_counts.values,
            title="🌍 Top 10 quốc gia có nhiều album nhất",
            labels={"x": "Quốc gia", "y": "Số lượng album"},
            color=country_counts.index,
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. Theo hãng thu âm (Label)
    elif trend_filter == "Label":
        trend_filter_2 = col3.selectbox(
            "📈 Phân tích xu hướng theo:",
            ["Số lượng album", "Popularity", "Total Streams (Millions)","Monthly Listeners","Streams Last 30 Days (Millions)", "Skip Rate"]
        )
        if trend_filter_2 == "Popularity":
            fig = px.box(
                album_df,
                x="label",
                y="popularity",
                title="🏷️ Độ phổ biến theo hãng thu âm",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Total Streams (Millions)":
            fig = px.box(
                album_df,
                x="label",
                y="Total Streams (Millions)",
                title="🏷️ Tổng lượt stream theo hãng thu âm",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Monthly Listeners":
            fig = px.box(
                album_df,
                x="label",
                y="Monthly Listeners (Millions)",
                title="🏷️ Lượt nghe hàng tháng theo hãng thu âm",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Streams Last 30 Days (Millions)":
            fig = px.box(
                album_df,
                x="label",
                y="Streams Last 30 Days (Millions)",
                title="🏷️ Lượt stream 30 ngày gần nhất theo hãng thu âm",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig, use_container_width=True)
        elif trend_filter_2 == "Skip Rate":
            df_skip = album_df.dropna(subset=["label", "Skip Rate (%)"])
            fig = px.box(
                df_skip,
                x="label",
                y="Skip Rate (%)",
                title="🏷️ Phân bố tỷ lệ bỏ qua (Skip Rate) theo hãng thu âm",
                color="label",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            # Tùy chỉnh lại layout cho đẹp
            fig.update_layout(
                xaxis_title="Hãng thu âm",
                yaxis_title="Tỷ lệ bỏ qua (%)",
                showlegend=False,
                template="plotly_white",
                margin=dict(l=40, r=20, t=80, b=100)
            )

            # Hiển thị biểu đồ trên Streamlit
            st.plotly_chart(fig, use_container_width=True)
        label_counts = album_df["label"].value_counts().head(10)
        fig = px.bar(
            x=label_counts.index,
            y=label_counts.values,
            title="🏷️ Top 10 hãng thu âm phát hành nhiều album nhất",
            labels={"x": "Hãng thu âm", "y": "Số lượng album"},
            color=label_counts.index,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig, use_container_width=True)
        
    

    # --- 7. Top 10 album theo tổng lượt stream
# --- 7. Top 10 album theo tổng lượt stream (cộng toàn cầu)
    elif trend_filter == "Total Streams (Millions)":
        total_by_album = (
            album_df.groupby(["Album", "Artist"])["Total Streams (Millions)"]
            .sum()
            .reset_index()
        )

        top_streams = total_by_album.nlargest(10, "Total Streams (Millions)").sort_values(
            "Total Streams (Millions)", ascending=True
        )

        fig = px.bar(
            top_streams,
            x="Total Streams (Millions)",
            y="Album",
            orientation="h",
            color="Total Streams (Millions)",
            title="💿 Top 10 album có tổng lượt stream cao nhất (tổng hợp toàn cầu)",
            color_continuous_scale="Viridis",
            text="Artist"
        )
        fig.update_layout(yaxis_title="Album", xaxis_title="Tổng lượt nghe (triệu)")
        st.plotly_chart(fig, use_container_width=True)


# --- 8. Top 10 album theo lượt stream 30 ngày gần nhất (cộng toàn cầu)
    elif trend_filter == "Streams Last 30 Days (Millions)":
        total_30days = (
            album_df.groupby(["Album", "Artist"])["Streams Last 30 Days (Millions)"]
            .sum()
            .reset_index()
        )

        top_30days = total_30days.nlargest(10, "Streams Last 30 Days (Millions)").sort_values(
            "Streams Last 30 Days (Millions)", ascending=True
        )

        fig = px.bar(
            top_30days,
            x="Streams Last 30 Days (Millions)",
            y="Album",
            orientation="h",
            color="Streams Last 30 Days (Millions)",
            title="📈 Top 10 album được stream nhiều nhất trong 30 ngày gần nhất (tổng hợp toàn cầu)",
            color_continuous_scale="Sunset",
            text="Artist"
        )
        fig.update_layout(yaxis_title="Album", xaxis_title="Lượt stream 30 ngày gần nhất (triệu)")
        st.plotly_chart(fig, use_container_width=True)


    # --- 9. Top 10 album theo lượt nghe hàng tháng (cộng toàn cầu)
    elif trend_filter == "Monthly Listeners":
        total_monthly = (
            album_df.groupby(["Album", "Artist"])["Monthly Listeners (Millions)"]
            .sum()
            .reset_index()
        )

        top_monthly = total_monthly.nlargest(10, "Monthly Listeners (Millions)").sort_values(
            "Monthly Listeners (Millions)", ascending=True
        )

        fig = px.bar(
            top_monthly,
            x="Monthly Listeners (Millions)",
            y="Album",
            orientation="h",
            color="Monthly Listeners (Millions)",
            title="🎵 Top 10 album có lượt nghe hàng tháng cao nhất (tổng hợp toàn cầu)",
            color_continuous_scale="Tealgrn",
            text="Artist"
        )
        fig.update_layout(yaxis_title="Album", xaxis_title="Lượt nghe hàng tháng (triệu)")
        st.plotly_chart(fig, use_container_width=True)

#----------------------------------
    st.subheader("🏆 Top 10 nghệ sĩ theo tổng streams (triệu lượt)")

    if "Artist" in album_df.columns and "Total Streams (Millions)" in album_df.columns:
        artist_streams = (
            album_df.groupby("Artist")["Total Streams (Millions)"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig2 = px.bar(
            x=artist_streams.index,
            y=artist_streams.values,
            labels={"x": "Artist", "y": "Total Streams (M)"},
            title="Top 10 nghệ sĩ toàn cầu",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Không tìm thấy dữ liệu Artist hoặc Total Streams (Millions).")

#----------------------------------
#       PHÂN TÍCH THEO SINGLE
#----------------------------------

# mở comment dòng này rồi code cho single
# --------------------------------- 
if album_type_filter == "single":
#----------------------------------

    df = top50_df
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])  # bỏ dòng lỗi ngày
        df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)
    else:
        st.warning("Không tìm thấy cột 'date' trong dữ liệu!")
        df["week"] = pd.NaT  # tạo tạm để không lỗi

    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    st.subheader("📊 Phân tích xu hướng theo single")
    trend_filter_2 = col3.selectbox(
            "📈 Phân tích xu hướng theo:",
            ["Overview", "Artist", "Genre", "Audio Features", "Ranking Dynamics", "Explicit Content"]
        )
    if trend_filter_2 == "Overview":
        st.markdown("Tổng quan về single sẽ được cập nhật sau.")

        col1, col2 = st.columns(2)
        df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

        # --- 📅 Số lượng bài hát mới mỗi tuần
        new_songs = df.sort_values(["song", "date"]).drop_duplicates(["song"], keep="first")
        new_weekly = new_songs.groupby("week").size().reset_index(name="new_entries")
        fig1 = px.line(
            new_weekly,
            x="week",
            y="new_entries",
            title="📅 Số lượng bài hát mới lọt Top50 theo tuần",
            markers=True,
        )
        col1.plotly_chart(fig1, use_container_width=True)

        # --- 🎧 Popularity trung bình theo thời gian
        mean_pop = df.groupby("week")["popularity"].mean().reset_index()
        fig2 = px.line(
            mean_pop,
            x="week",
            y="popularity",
            title="🎧 Mức độ phổ biến trung bình theo thời gian",
            markers=True,
        )
        col2.plotly_chart(fig2, use_container_width=True)

        # --- 🔥 Số lần xuất hiện của mỗi bài hát
        song_counts = df["song"].value_counts().head(15)
        fig3 = px.bar(
            x=song_counts.index,
            y=song_counts.values,
            title="🔥 Số lần xuất hiện trong Top50 (Top 15 bài hát)",
            labels={"x": "Bài hát", "y": "Số lần xuất hiện"},
        )
        st.plotly_chart(fig3, use_container_width=True)

        # --- 🕗 Độ dài trung bình
        if "duration_ms" in df.columns:
            df["duration_min"] = df["duration_ms"] / 60000
            dur = df.groupby("week")["duration_min"].mean().reset_index()
            fig4 = px.line(
                dur,
                x="week",
                y="duration_min",
                title="🕗 Độ dài bài hát trung bình theo thời gian",
                markers=True,
            )
            st.plotly_chart(fig4, use_container_width=True)

    elif trend_filter_2 == "Artist":
        st.header("🎤 Phân tích nghệ sĩ")

# 🏆 Top nghệ sĩ xuất hiện nhiều nhất
        top_artists = df["artist"].value_counts().head(15)
        fig1 = px.bar(
            x=top_artists.index,
            y=top_artists.values,
            title="🏆 Nghệ sĩ xuất hiện nhiều nhất trong Top50",
            labels={"x": "Nghệ sĩ", "y": "Số lần xuất hiện"},
        )
        st.plotly_chart(fig1, use_container_width=True)

        # 📈 Thứ hạng trung bình theo thời gian
        avg_pos = df.groupby(["artist", "week"])["position"].mean().reset_index()
        artists_to_plot = avg_pos["artist"].value_counts().head(5).index
        fig2 = px.line(
            avg_pos[avg_pos["artist"].isin(artists_to_plot)],
            x="week",
            y="position",
            color="artist",
            title="📈 Thứ hạng trung bình theo thời gian (Top 5 nghệ sĩ)",
        )
        fig2.update_yaxes(autorange="reversed")
        st.plotly_chart(fig2, use_container_width=True)

        # 🔊 So sánh phong cách (energy, valence, danceability)
        if all(c in df.columns for c in ["energy", "valence", "danceability"]):
            mean_feat = df.groupby("artist")[["energy", "valence", "danceability"]].mean().reset_index()
            mean_feat_top = mean_feat[mean_feat["artist"].isin(artists_to_plot)]
            fig3 = px.scatter_3d(
                mean_feat_top,
                x="energy",
                y="valence",
                z="danceability",
                color="artist",
                title="🔊 So sánh phong cách âm nhạc (Energy - Valence - Danceability)",
            )
            st.plotly_chart(fig3, use_container_width=True)

    elif trend_filter_2 == "Genre":
        st.header("🎶 Phân tích thể loại âm nhạc")

        if "main_genre" in df.columns:
            df["month"] = df["date"].dt.to_period("M").astype(str)
            genre_month = df.groupby(["month", "main_genre"]).size().reset_index(name="count")

            # 📚 Tỷ trọng thể loại qua thời gian
            fig1 = px.area(
                genre_month,
                x="month",
                y="count",
                color="main_genre",
                title="📚 Tỷ trọng thể loại qua thời gian",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # 🎵 Đa dạng thể loại mỗi tháng
            unique_genre = genre_month.groupby("month")["main_genre"].nunique().reset_index()
            fig2 = px.line(
                unique_genre,
                x="month",
                y="main_genre",
                title="🎵 Số lượng thể loại đa dạng mỗi tháng",
                markers=True,
            )
            st.plotly_chart(fig2, use_container_width=True)

            # 🧠 Trung bình đặc trưng theo thể loại
            features = ["energy", "valence", "danceability"]
            avg_feat = df.groupby("main_genre")[features].mean().reset_index()
            fig3 = px.bar(
                avg_feat.melt(id_vars="main_genre"),
                x="main_genre",
                y="value",
                color="variable",
                barmode="group",
                title="🧠 Trung bình energy, valence, danceability theo thể loại",
            )
            st.plotly_chart(fig3, use_container_width=True)
    
    elif trend_filter_2 == "Audio Features":
        st.header("🧠 Phân tích đặc trưng âm nhạc")

        if all(c in df.columns for c in ["energy", "valence", "danceability"]):
            feat_time = df.groupby("week")[["energy", "valence", "danceability"]].mean().reset_index()
            fig1 = px.line(
                feat_time,
                x="week",
                y=["energy", "valence", "danceability"],
                title="🎶 Xu hướng energy, valence, danceability theo thời gian",
            )
            st.plotly_chart(fig1, use_container_width=True)

        # 🔗 Ma trận tương quan
        audio_cols = ["acousticness", "danceability", "energy", "valence", "tempo", "loudness"]
        corr = df[audio_cols].corr()
        fig2 = px.imshow(corr, text_auto=True, title="🔗 Ma trận tương quan giữa các đặc trưng âm nhạc")
        st.plotly_chart(fig2, use_container_width=True)

        # 📈 Valence (cảm xúc âm nhạc)
        valence_trend = df.groupby("week")["valence"].mean().reset_index()
        fig3 = px.line(
            valence_trend,
            x="week",
            y="valence",
            title="📈 'Cảm xúc âm nhạc toàn cầu' (Valence trung bình theo thời gian)",
            markers=True,
        )
        st.plotly_chart(fig3, use_container_width=True)
    elif trend_filter_2 == "Ranking Dynamics":
        st.header("🏆 Phân tích vị trí xếp hạng")

        selected_song = st.selectbox("🎵 Chọn bài hát để xem đường di chuyển:", sorted(df["song"].unique()))
        song_df = df[df["song"] == selected_song]
        fig1 = px.line(
            song_df,
            x="date",
            y="position",
            title=f"🔄 Đường di chuyển của '{selected_song}' trong bảng xếp hạng",
            markers=True,
        )
        fig1.update_yaxes(autorange="reversed")
        st.plotly_chart(fig1, use_container_width=True)

        # ⏳ Thời gian bài hát duy trì trong Top50
        song_duration = df.groupby("song")["date"].nunique().reset_index(name="days_in_chart")
        fig2 = px.histogram(
            song_duration,
            x="days_in_chart",
            nbins=30,
            title="⏳ Số ngày bài hát duy trì trong Top50",
        )
        st.plotly_chart(fig2, use_container_width=True)
    elif trend_filter_2 == "Explicit Content":
        st.header("🚫 Phân tích nhạc explicit (18+)")

        if "is_explicit" in df.columns:
            df["year"] = df["date"].dt.year
            explicit_ratio = df.groupby("year")["is_explicit"].mean().reset_index()
            fig1 = px.line(
                explicit_ratio,
                x="year",
                y="is_explicit",
                title="🚫 Tỷ lệ nhạc explicit theo năm",
                markers=True,
            )
            st.plotly_chart(fig1, use_container_width=True)

            # 🔊 So sánh đặc trưng nhạc explicit vs non-explicit
            feat_cols = ["energy", "valence", "danceability"]
            for col in feat_cols:
                fig = px.box(
                    df,
                    x="is_explicit",
                    y=col,
                    color="is_explicit",
                    title=f"🔊 So sánh {col} giữa explicit và non-explicit",
                )
                st.plotly_chart(fig, use_container_width=True)
