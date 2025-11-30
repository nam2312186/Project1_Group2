# pages/3_Chatbot_Gemini.py

import os
import re
from collections import Counter

import streamlit as st
import google.generativeai as genai
from pymongo import MongoClient
import pandas as pd

# =========================
#   CẤU HÌNH GIAO DIỆN
# =========================
st.set_page_config(page_title="Chatbot Gemini", layout="wide")
st.title("💬 Chatbot Gemini – Spotify & Billboard Assistant")

st.caption(
    "Chatbot dùng Google Gemini + MongoDB.\n"
    "Bạn có thể:\n"
    "- Hỏi tự do về dashboard, báo cáo.\n"
    "- Dùng lệnh dữ liệu, ví dụ:\n"
    "  • /data count_songs country=usa\n"
    "  • /data top_artists country=uk limit=10\n"
    "  • /data top_billboard limit=10\n"
)

# =========================
#   LẤY API KEY TỪ ENV
# =========================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ Thiếu GEMINI_API_KEY trong biến môi trường.")
    st.stop()

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-flash-latest"
model = genai.GenerativeModel(MODEL_NAME)

# =========================
#   KẾT NỐI MONGODB
# =========================
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    st.error(
        "❌ Thiếu MONGO_URI trong biến môi trường.\n"
        "Ví dụ: set MONGO_URI=mongodb+srv://user:pass@cluster/spotify_project"
    )
    st.stop()

client = MongoClient(MONGO_URI)
db = client["spotify_project"]  # đổi nếu bạn đặt tên khác

# =========================
#   ĐỌC FILE KIẾN THỨC
# =========================
def load_knowledge() -> str:
    candidate_paths = [
        r"D:\Daihoc\Nam3\DAHKTDL\Code\Project_Spotify\Application\knowledge\data_dictionary.txt",
        "knowledge/data_dictionary.txt",
        "./knowledge/data_dictionary.txt",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return ""


KNOWLEDGE = load_knowledge()

SYSTEM_PROMPT = f"""
Bạn là chatbot hỗ trợ hệ thống dashboard phân tích âm nhạc Spotify & Billboard
của sinh viên Bách Khoa. Bạn có 2 khả năng:

1. Trả lời dựa trên tài liệu nội bộ (data dictionary, báo cáo).
2. Khi người dùng dùng lệnh /data ..., ứng dụng sẽ tự truy vấn MongoDB và
   hiển thị kết quả; sau đó bạn có thể giải thích ý nghĩa.

Tài liệu nội bộ:

==== START OF INTERNAL DATA DOCUMENTATION ====
{KNOWLEDGE}
==== END OF INTERNAL DATA DOCUMENTATION ====

Luôn trả lời bằng tiếng Việt, dễ hiểu, ngắn gọn; ưu tiên bối cảnh dashboard,
MongoDB, Spotify, Billboard.
"""

if KNOWLEDGE:
    st.success("📚 Đã nạp `data_dictionary.txt`.")
else:
    st.warning("⚠ Chưa tìm thấy `data_dictionary.txt` – chatbot sẽ chỉ hiểu theo prompt tổng quát.")

# =========================
#   HÀM TRUY VẤN MONGO
# =========================

def normalize_country(country: str) -> str:
    """Chuẩn hóa tên country -> đúng collection top50_<country>_2024."""
    return country.strip().lower().replace(" ", "_")


def get_spotify_collection_2024(country: str):
    """
    Trả về collection Top 50 2024 cho 1 quốc gia.
    Giả sử tên collection là top50_<country>_2024, ví dụ:
    - top50_usa_2024
    - top50_uk_2024
    """
    c = normalize_country(country)
    coll_name = f"top50_{c}_2024"
    return db[coll_name]


def data_count_songs(country: str):
    coll = get_spotify_collection_2024(country)
    count = coll.count_documents({})
    return count


def data_top_artists(country: str, limit: int = 10):
    coll = get_spotify_collection_2024(country)
    docs = list(coll.find({}, {"artist": 1, "artists": 1, "_id": 0}))
    names = []
    for d in docs:
        if "artists" in d and isinstance(d["artists"], list):
            names.extend(d["artists"])
        elif "artist" in d:
            names.append(d["artist"])
    counter = Counter(names)
    top = counter.most_common(limit)
    df = pd.DataFrame(top, columns=["artist", "count"])
    return df


def data_top_billboard(limit: int = 10):
    """
    Lấy Top N bài hát từ collection Billboard 2025 Mỹ.
    Giả sử collection: top100_usa_2025, field:
    - song, artist, peak_rank, weeks_on_chart
    """
    coll = db["top100_usa_2025"]
    cursor = coll.find(
        {},
        {"song": 1, "artist": 1, "peak_rank": 1, "weeks_on_chart": 1, "_id": 0},
    ).sort("peak_rank", 1).limit(limit)
    df = pd.DataFrame(list(cursor))
    return df

# =========================
#   PARSE LỆNH /data
# =========================

def parse_data_command(msg: str):
    """
    Nhận chuỗi /data ... và trả về dict:
    {"action": "count_songs" / "top_artists" / "top_billboard", ...}
    """
    # /data count_songs country=usa
    # /data top_artists country=uk limit=10
    # /data top_billboard limit=10
    msg = msg.strip()
    if not msg.lower().startswith("/data"):
        return None

    # tách phần sau /data
    try:
        _, rest = msg.split(" ", 1)
    except ValueError:
        return None

    parts = rest.strip().split()
    if not parts:
        return None

    action = parts[0]
    params = {"action": action}

    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.lower()] = v

    return params

# =========================
#   SESSION STATE
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list[(role, msg)]

st.subheader("🗨️ Chat với bot")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🧹 Xóa lịch sử chat"):
        st.session_state.chat_history = []
        st.rerun()

# Hiển thị lịch sử
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**👤 Bạn:** {msg}")
    else:
        st.markdown(f"**🤖 Bot:** {msg}")

# =========================
#   Ô NHẬP TIN NHẮN
# =========================
user_msg = st.chat_input("Nhập câu hỏi (hoặc lệnh /data ...)")

if user_msg:
    st.session_state.chat_history.append(("user", user_msg))

    # 1) Nếu là lệnh /data → truy vấn MongoDB
    data_cmd = parse_data_command(user_msg)
    if data_cmd:
        try:
            action = data_cmd.get("action")

            if action == "count_songs":
                country = data_cmd.get("country", "usa")
                count = data_count_songs(country)
                answer = f"Số bài hát trong Top 50 năm 2024 của {country.upper()} là: **{count}**."

            elif action == "top_artists":
                country = data_cmd.get("country", "usa")
                limit = int(data_cmd.get("limit", 10))
                df = data_top_artists(country, limit)
                st.markdown(f"**Top {limit} nghệ sĩ xuất hiện nhiều nhất trong Top 50 {country.upper()} 2024:**")
                st.dataframe(df, use_container_width=True)
                answer = "Mình đã hiển thị bảng Top nghệ sĩ cho bạn ở phía trên."

            elif action == "top_billboard":
                limit = int(data_cmd.get("limit", 10))
                df = data_top_billboard(limit)
                st.markdown(f"**Top {limit} bài hát Billboard Hot 100 USA 2025 theo peak_rank:**")
                st.dataframe(df, use_container_width=True)
                answer = "Mình đã hiển thị bảng Top bài hát Billboard cho bạn ở phía trên."

            else:
                answer = "Mình chưa hiểu lệnh /data này. Các lệnh hỗ trợ: count_songs, top_artists, top_billboard."

        except Exception as e:
            answer = f"⚠️ Lỗi khi truy vấn MongoDB: `{e}`"

        st.session_state.chat_history.append(("assistant", answer))
        st.rerun()

    # 2) Không phải /data → cho Gemini trả lời
    else:
        history_text = SYSTEM_PROMPT + "\n\n"
        for role, msg in st.session_state.chat_history[-15:]:
            history_text += f"{role}: {msg}\n"

        try:
            response = model.generate_content(history_text)
            answer = response.text
        except Exception as e:
            answer = f"⚠️ Lỗi API Gemini: `{e}`"

        st.session_state.chat_history.append(("assistant", answer))
        st.rerun()
