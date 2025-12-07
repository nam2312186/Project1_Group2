# pages/3_Chatbot_Gemini.py
"""
Chatbot Page 3 – Router 2 loại chatbot:
- Chatbot KIẾN THỨC (txt + embeddings): dùng data_dictionary.txt + Gemini.
- Chatbot TRUY VẤN (MongoDB): hiện tại chỉ in "chatbot truy vấn",
  sau này bạn/bạn của bạn chèn code Text-to-MLQ vào đây.

UI kiểu Messenger: bong bóng user/bot, avatar 2 bên.
"""

import os
import sys
import html
from typing import List, Tuple
from pathlib import Path

import streamlit as st
import google.generativeai as genai

# =========================
#   FIX ĐƯỜNG IMPORT CHO PAGES
# =========================
# File này nằm ở: Application/pages/3_Chatbot_Gemini.py
# → Thêm thư mục Application/ vào sys.path để import knowledge.*
PAGES_DIR = Path(__file__).resolve().parent           # .../Application/pages
APP_DIR = PAGES_DIR.parent                            # .../Application

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from knowledge.embedding_utils import search_similar_chunks

# =========================
#   CẤU HÌNH GIAO DIỆN
# =========================
st.set_page_config(page_title="Chatbot Gemini", layout="wide")
st.title("💬 Chatbot Gemini – Spotify & Billboard Assistant")

st.caption(
    "Trang này có 2 kiểu chatbot:\n \n"
    "1️⃣ Chatbot KIẾN THỨC (từ file data_dictionary.txt + embeddings).\n \n"
    "2️⃣ Chatbot TRUY VẤN số liệu từ MongoDB (text → MLQ).\n\n"
    "Hiện tại đang thử nghiệm có gì lỗi mong bạn thông cảm! 😊"
)

# 🎨 CSS – khung chat kiểu Messenger, gọn, không khoảng trắng dư
st.markdown(
    """
    <style>
    .chat-outer {
        max-width: 900px;
        margin: 0.75rem auto;
        min-height: 0px;
        max-height: 0px;
        border: 1px solid #e5e7eb;   /* viền nhẹ */
        border-radius: 12px;
        background: #148BDB;
        padding: 0.75rem;
        overflow-y: auto;            /* scroll trong box */
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
    }
    .message-row {
        display: flex;
        align-items: flex-end;
        margin-bottom: 0.1rem;
    }
    .message-row.user {
        justify-content: flex-end;
    }
    .message-row.assistant {
        justify-content: flex-start;
    }
    .message-bubble {
        padding: 0.45rem 0.8rem;
        border-radius: 16px;
        max-width: 70%;
        font-size: 0.95rem;
        line-height: 1.4;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    .message-bubble.user {
        background-color: #1DB954;   /* Spotify green */
        color: #ffffff;
        border-bottom-right-radius: 4px;
    }
    .message-bubble.assistant {
        background-color: #72D3FF;
        color: #111827;
        border-bottom-left-radius: 4px;
    }
    .message-meta {
        font-size: 0.7rem;
        color: #6b7280;
        margin-bottom: 0.1rem;
    }
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        margin: 0 0.35rem;
        flex-shrink: 0;
    }
    .avatar.user {
        background-color: #16a34a;
        color: white;
    }
    .avatar.assistant {
        background-color: #e5e7eb;
        color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
#   KHAI BÁO GEMINI
# =========================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ Thiếu GEMINI_API_KEY trong biến môi trường.")
    st.stop()

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-flash-latest"
model = genai.GenerativeModel(MODEL_NAME)

# =========================
#   ĐỌC FILE KIẾN THỨC (TXT)
# =========================
def load_knowledge() -> str:
    """
    Đọc Application/knowledge/data_dictionary.txt (dùng __file__).
    Chỉ để kiểm tra file có tồn tại hay không (embeddings đã build từ file này).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Application/pages
    knowledge_path = os.path.abspath(
        os.path.join(base_dir, "..", "knowledge", "data_dictionary.txt")
    )
    if os.path.exists(knowledge_path):
        with open(knowledge_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


KNOWLEDGE = load_knowledge()

if KNOWLEDGE:
    st.success("")
else:
    st.warning(
        "⚠ Chưa tìm thấy `data_dictionary.txt`. "
        "Hãy kiểm tra lại đường dẫn Application/knowledge/data_dictionary.txt."
    )

# Prompt hệ thống cho chatbot kiến thức (không nhét full txt vào đây nữa)
SYSTEM_PROMPT_TXT = """
Bạn là chatbot KIẾN THỨC cho dự án dashboard Spotify & Billboard (2024–2025).

Nhiệm vụ:
- Giải thích khái niệm, các trường dữ liệu, KPI, logic phân tích trong dashboard.
- Trả lời dựa trên nội dung tài liệu nội bộ (context được cung cấp) và kiến thức về dữ liệu âm nhạc.
- Không bịa số liệu cụ thể như stream, thứ hạng, tuần xuất hiện.
- Không nhắc đến các mục như “Mục 7”, “biểu đồ số”, “section”, “hình minh hoạ”, vì người dùng chatbot không xem được report.
- Khi cần nói về biểu đồ hoặc trực quan hoá, hãy nói chung chung theo kiểu:
  “Trong dashboard, trường này thường được sử dụng để phân tích xu hướng.  
   Nếu bạn muốn xem trực quan hơn, bạn có thể mở dashboard để xem nhé!”

Quy tắc định dạng:
- Trả lời bằng văn bản thuần, không sử dụng Markdown phức tạp như bảng, code block, tiêu đề ###, ký tự đặc biệt.
- Có thể sử dụng bullet dạng “•” cho dễ đọc.
- Viết thân thiện, rõ ràng, mạch lạc, giúp người dùng dễ hiểu.

Nếu câu hỏi liên quan đến số liệu, top, rank, lọc dữ liệu, hãy gợi ý chuyển sang chatbot TRUY VẤN.

Trả lời bằng tiếng Việt.
""".strip()



# =========================
#   HÀM VẼ BONG BÓNG CHAT
# =========================
def render_message(role: str, msg: str):
    if role == "user":
        safe_msg = html.escape(msg).replace("\n", "<br>")
        avatar_html = '<div class="avatar user">🧑</div>'
        bubble_html = f"""
            <div class="message-bubble user">
              <div class="message-meta">Bạn</div>
              <div>{safe_msg}</div>
            </div>
        """
        row_html = f'<div class="message-row user">{bubble_html}{avatar_html}</div>'
    else:
        # Bot: nội dung chỉ là văn bản thường, không markdown phức tạp nữa
        safe_msg = html.escape(msg).replace("\n", "<br>")
        avatar_html = '<div class="avatar assistant">🤖</div>'
        bubble_html = f"""
            <div class="message-bubble assistant">
              <div class="message-meta">Bot</div>
              <div>{safe_msg}</div>
            </div>
        """
        row_html = f'<div class="message-row assistant">{avatar_html}{bubble_html}</div>'

    st.markdown(row_html, unsafe_allow_html=True)

# =========================
#   ROUTER: PHÂN LOẠI Ý ĐỊNH
# =========================
def classify_intent(msg: str) -> str:
    """
    Trả về:
    - "query"     → câu hỏi về số liệu cụ thể, top, rank, bài hát cụ thể, thống kê...
    - "knowledge" → câu hỏi chung về khái niệm, cấu trúc dữ liệu, ý nghĩa KPI...
    """
    m = msg.lower().strip()

    # Lệnh /data chắc chắn là truy vấn
    if m.startswith("/data"):
        return "query"

    # Hỏi trực tiếp về bài hát / ca khúc cụ thể
    song_keywords = ["bài hát", "bai hat", "ca khúc", "ca khuc", "song "]
    ask_keywords = ["biết", "biet", "có trong", "co trong", "nằm trong", "nam trong", "xuất hiện", "xuat hien"]
    if any(sk in m for sk in song_keywords) and any(ak in m for ak in ask_keywords):
        # ví dụ: "bạn biết bài hát apt ko", "bài hát này có trong dữ liệu không"
        return "query"

    # Các từ khóa về thống kê / số liệu
    query_keywords = [
        "bao nhiêu", "bao nhieu", "số lượng", "so luong",
        "thống kê", "thong ke",
        "top ", "top10", "top 10", "top 5",
        "xếp hạng", "xep hang", "rank", "ranking",
        "tuần nào", "tuan nao", "ngày nào", "ngay nao",
        "mấy tuần", "may tuan", "weeks_on_chart",
        "peak rank", "peak_rank",
        "lớn nhất", "lon nhat", "nhỏ nhất", "nho nhat",
        "trung bình", "trung binh",
        "danh sách", "danh sach", "liệt kê", "liet ke",
        "lọc theo", "loc theo", "filter", "where ",
        "lượt stream", "luot stream",
        "truy cập", "truy cap",
        "truy vấn", "truy van",
        "số ca khúc", "so ca khuc",
    ]
    if any(kw in m for kw in query_keywords):
        return "query"

    # Mặc định: câu hỏi kiến thức
    return "knowledge"

# =========================
#   CHATBOT KIẾN THỨC (RAG)
# =========================
def answer_from_txt(user_msg: str, history: List[Tuple[str, str]]) -> str:
    """
    Chatbot kiến thức:
    - Dùng embeddings (kb_embeddings.json) để chọn vài đoạn tài liệu liên quan nhất.
    - Gửi các đoạn đó + câu hỏi + một ít history cho Gemini.
    """

    try:
        # 1. Tìm các chunk liên quan nhất từ embeddings
        top_chunks = search_similar_chunks(user_msg, top_k=3)
        context_text = "\n\n---\n\n".join(ch["text"] for ch in top_chunks)

        # 2. Gom một ít history gần nhất cho mạch hội thoại
        history_text = ""
        for role, msg in history[-4:]:
            prefix = "Người dùng" if role == "user" else "Trợ lý"
            history_text += f"{prefix}: {msg}\n"

        # 3. Tạo prompt đầy đủ cho Gemini
        full_prompt = f"""{SYSTEM_PROMPT_TXT}

Dưới đây là một số đoạn tài liệu nội bộ (data_dictionary/ mô tả dashboard) liên quan đến câu hỏi:

{context_text}

Lịch sử hội thoại gần đây:
{history_text}

Câu hỏi của người dùng:
{user_msg}

Hãy trả lời dựa trên các đoạn tài liệu trên. Nếu không chắc chắn, hãy nói rõ là bạn
không có đủ thông tin, đừng tự bịa số liệu cụ thể (streams, rank, tuần,...).
"""

        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Lỗi khi xử lý chatbot kiến thức (RAG): `{e}`"

# =========================
#   CHATBOT TRUY VẤN (PLACEHOLDER)
# =========================
def answer_from_query_bot(user_msg: str, history: List[Tuple[str, str]]) -> str:
    """
    Chatbot truy vấn – TẠM THỜI CHỈ PLACEHOLDER.

    Sau này bạn/bạn của bạn có thể:
    - Thêm code phân tích câu hỏi → sinh MLQ / pipeline MongoDB.
    - Thực hiện truy vấn, trả về bảng/biểu đồ + giải thích.

    Hiện tại hàm này chỉ trả đúng chuỗi "chatbot truy vấn".
    """
    return "chatbot truy vấn"

# =========================
#   SESSION STATE
# =========================
if "chat_history" not in st.session_state:
    # Khởi tạo với 1 lời chào để trang nhìn đỡ trống
    st.session_state.chat_history: List[Tuple[str, str]] = [
        (
            "assistant",
            "Xin chào, tôi là chatbot hỗ trợ dự án Spotify & Billboard.\n"
            "• Hỏi về khái niệm, trường dữ liệu, KPI, insight → tôi dùng tài liệu txt (embeddings) để trả lời.\n"
            "• Hỏi về số liệu/top/rank/bài hát cụ thể → tôi sẽ chuyển sang chatbot TRUY VẤN.\n"
            "• Tôi luôn sẵn sàng giúp bạn! 😊",
        )
    ]

st.subheader("💬 Chat với bot")

# =========================
#   KHUNG HIỂN THỊ CHAT
# =========================
st.markdown('<div class="chat-outer">', unsafe_allow_html=True)

# Lịch sử cũ
for role, msg in st.session_state.chat_history:
    render_message(role, msg)

# Placeholder cho message mới trong lần run hiện tại
new_user_placeholder = st.empty()
bot_placeholder = st.empty()

st.markdown("</div>", unsafe_allow_html=True)

# =========================
#   THANH DƯỚI: NÚT XÓA + Ô NHẬP
# =========================
bottom_bar = st.container()
with bottom_bar:
    col_clear, col_input = st.columns([1, 9])

    with col_clear:
        if st.button("🧹 Xóa lịch sử", help="Xóa lịch sử chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    with col_input:
        user_msg = st.chat_input("Nhập câu hỏi (về dữ liệu / kiến thức ...)")

# =========================
#   XỬ LÝ TIN NHẮN MỚI
# =========================
if user_msg:
    # 1. Hiện ngay tin nhắn user ở placeholder (real-time feel)
    with new_user_placeholder:
        render_message("user", user_msg)

    # 2. Router intent
    intent = classify_intent(user_msg)

    # 3. Gọi chatbot phù hợp
    if intent == "knowledge":
        with st.spinner("📖 Tôi đang phản hồi vui lòng chờ trong giây lát"):
            answer = answer_from_txt(user_msg, st.session_state.chat_history)
    else:
        with st.spinner("📊 Đang chuyển sang chatbot truy vấn (placeholder)..."):
            answer = answer_from_query_bot(user_msg, st.session_state.chat_history)

    # 4. Hiện bot trả lời
    with bot_placeholder:
        render_message("assistant", answer)

    # 5. Lưu vào lịch sử cho các lần chat tiếp theo
    st.session_state.chat_history.append(("user", user_msg))
    st.session_state.chat_history.append(("assistant", answer))
