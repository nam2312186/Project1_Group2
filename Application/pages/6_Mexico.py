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

collection_spotify = db["spotify_top50_mexico"]

@st.cache_data
def load_spotify_data():
    data = list(collection_spotify.find({}, {"_id": 0}))
    return pd.DataFrame(data)

df_spotify = load_spotify_data()

st.header("🎧 Spotify Top 50 (2024)")
st.write("Hiển thị dữ liệu Spotify 2024 cho Argentina (đang cập nhật...)")

if not df_spotify.empty:
    st.dataframe(df_spotify.head(20))
else:
    st.warning("Chưa có dữ liệu Spotify Top 50 (2024) trong MongoDB.")