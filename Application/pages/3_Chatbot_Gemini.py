# # pages/3_Chatbot_Gemini.py
# """
# Chatbot Page 3 – Router 2 loại chatbot:
# - Chatbot KIẾN THỨC (txt + embeddings): dùng data_dictionary.txt + Gemini.
# - Chatbot TRUY VẤN (MongoDB): hiện tại chỉ in "chatbot truy vấn",
#   sau này bạn/bạn của bạn chèn code Text-to-MLQ vào đây.

# UI kiểu Messenger: bong bóng user/bot, avatar 2 bên.
# """

# import os
# import re
# import sys
# import html
# from typing import List, Tuple
# from pathlib import Path
# from agent.router import route_query
# import streamlit as st
# import google.generativeai as genai

# # Import các module tự viết
# from knowledge.embedding_utils import search_similar_chunks

# from agent.core import process_user_query 

# # 👇 QUAN TRỌNG: Import hàm lấy key xoay vòng từ config
# from agent.config import get_resilient_llm

# # =========================
# #   FIX ĐƯỜNG IMPORT CHO PAGES
# # =========================
# # File này nằm ở: Application/pages/3_Chatbot_Gemini.py
# # → Thêm thư mục Application/ vào sys.path để import knowledge.*
# PAGES_DIR = Path(__file__).resolve().parent           # .../Application/pages
# APP_DIR = PAGES_DIR.parent                            # .../Application

# if str(APP_DIR) not in sys.path:
#     sys.path.insert(0, str(APP_DIR))



# # =========================
# #   CẤU HÌNH GIAO DIỆN
# # =========================
# st.set_page_config(page_title="Chatbot Gemini", layout="wide")
# st.title("💬 Chatbot Gemini Spotify Assistant")

# st.caption(
#     "Trang này có 2 kiểu chatbot:\n \n"
#     "1️⃣ Chatbot KIẾN THỨC (từ file data_dictionary.txt + embeddings).\n \n"
#     "2️⃣ Chatbot TRUY VẤN số liệu từ MongoDB (text → MLQ).\n\n"
#     "Hiện tại đang thử nghiệm có gì lỗi mong bạn thông cảm! 😊"
# )

# # 🎨 CSS – khung chat kiểu Messenger, gọn, không khoảng trắng dư
# st.markdown(
#     """
#     <style>
#     .chat-outer {
#         max-width: 900px;
#         margin: 0.75rem auto;
#         min-height: 0px;
#         max-height: 0px;
#         border: 1px solid #e5e7eb;   /* viền nhẹ */
#         border-radius: 12px;
#         background: #148BDB;
#         padding: 0.75rem;
#         overflow-y: auto;            /* scroll trong box */
#         display: flex;
#         flex-direction: column;
#         gap: 0.4rem;
#         box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
#     }
#     .message-row {
#         display: flex;
#         align-items: flex-end;
#         margin-bottom: 0.1rem;
#     }
#     .message-row.user {
#         justify-content: flex-end;
#     }
#     .message-row.assistant {
#         justify-content: flex-start;
#     }
#     .message-bubble {
#         padding: 0.45rem 0.8rem;
#         border-radius: 16px;
#         max-width: 70%;
#         font-size: 0.95rem;
#         line-height: 1.4;
#         word-wrap: break-word;
#         white-space: pre-wrap;
#     }
#     .message-bubble.user {
#         background-color: #8DC86E;   
#         color: #520962;
#         border-bottom-right-radius: 4px;
#     }
#     .message-bubble.assistant {
#         background-color: #7CB7D7;
#         color: #8E4A01;
#         border-bottom-left-radius: 4px;
#     }
#     .message-meta {
#         font-size: 0.7rem;
#         color: #6b7280;
#         margin-bottom: 0.1rem;
#     }
#     .avatar {
#         width: 32px;
#         height: 32px;
#         border-radius: 999px;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         font-size: 18px;
#         margin: 0 0.35rem;
#         flex-shrink: 0;
#     }
#     .avatar.user {
#         background-color: #16a34a;
#         color: white;
#     }
#     .avatar.assistant {
#         background-color: #e5e7eb;
#         color: #111827;
#     }

# /* CSS cho bảng trong tin nhắn */
#     .message-bubble table {
#         width: 100%;
#         border-collapse: collapse;
#         margin: 10px 0;
#         font-size: 0.9em;
#         border-radius: 5px 5px 0 0;
#         overflow: hidden;
#         box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
#     }
#     .message-bubble th {
#         background-color: #009879; /* Màu xanh Spotify */
#         color: #ffffff;
#         text-align: left;
#         font-weight: bold;
#         padding: 12px 15px;
#     }
#     .message-bubble td {
#         padding: 12px 15px;
#         border-bottom: 1px solid #dddddd;
#     }
#     .message-bubble tr:nth-of-type(even) {
#         background-color: #f3f3f3; /* Màu xen kẽ cho dễ đọc */
#     }
#     .message-bubble tr:last-of-type {
#         border-bottom: 2px solid #009879;
#     }

#     .message-bubble table {
#         width: 100%;
#         border-collapse: collapse;
#         margin: 15px 0;
#         font-size: 0.9em;
#         font-family: sans-serif;
#         min-width: 400px;
#         border-radius: 8px 8px 0 0;
#         overflow: hidden;
#         box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
#         background-color: white; /* Nền bảng màu trắng */
#     }
    
#     /* Header của bảng */
#     .message-bubble th {
#         background-color: #1DB954; /* Màu xanh Spotify */
#         color: #ffffff;
#         text-align: left;
#         font-weight: bold;
#         padding: 12px 15px;
#     }
    
#     /* Các dòng dữ liệu */
#     .message-bubble td {
#         padding: 12px 15px;
#         color: #333; /* Chữ màu đen dễ đọc */
#         border-bottom: 1px solid #dddddd;
#     }
    
#     /* Hiệu ứng dòng chẵn lẻ (Zebra striping) */
#     .message-bubble tr:nth-of-type(even) {
#         background-color: #f3f3f3;
#     }
    
#     /* Dòng cuối cùng có viền đậm hơn */
#     .message-bubble tr:last-of-type {
#         border-bottom: 2px solid #1DB954;
#     }
    
#     /* Highlight chữ đậm trong bảng */
#     .message-bubble strong {
#         color: #d63384; /* Màu hồng đậm cho điểm nhấn */
#     }

#     </style>
#     """,
#     unsafe_allow_html=True,
# )


# # # =========================
# #   ĐỌC FILE KIẾN THỨC (TXT)
# # =========================
# def load_knowledge() -> str:
#     """
#     Đọc Application/knowledge/data_dictionary.txt (dùng __file__).
#     Chỉ để kiểm tra file có tồn tại hay không (embeddings đã build từ file này).
#     """
#     base_dir = os.path.dirname(os.path.abspath(__file__))  # Application/pages
#     knowledge_path = os.path.abspath(
#         os.path.join(base_dir, "..", "knowledge", "data_dictionary.txt")
#     )
#     if os.path.exists(knowledge_path):
#         with open(knowledge_path, "r", encoding="utf-8") as f:
#             return f.read()
#     return ""


# KNOWLEDGE = load_knowledge()

# if KNOWLEDGE:
#     st.success("")
# else:
#     st.warning(
#         "⚠ Chưa tìm thấy `data_dictionary.txt`. "
#         "Hãy kiểm tra lại đường dẫn Application/knowledge/data_dictionary.txt."
#     )

# # Prompt hệ thống cho chatbot kiến thức (không nhét full txt vào đây nữa)
# SYSTEM_PROMPT_TXT = """
# Bạn là chatbot KIẾN THỨC cho dự án dashboard Spotify & Billboard (2024–2025).

# Nhiệm vụ:
# - Giải thích khái niệm, các trường dữ liệu, KPI, logic phân tích trong dashboard.
# - Trả lời dựa trên nội dung tài liệu nội bộ (context được cung cấp) và kiến thức về dữ liệu âm nhạc.
# - Không bịa số liệu cụ thể như stream, thứ hạng, tuần xuất hiện.
# - Không nhắc đến các mục như “Mục 7”, “biểu đồ số”, “section”, “hình minh hoạ”, vì người dùng chatbot không xem được report.
# - Khi cần nói về biểu đồ hoặc trực quan hoá, hãy nói chung chung theo kiểu:
#   “Trong dashboard, trường này thường được sử dụng để phân tích xu hướng.  
#    Nếu bạn muốn xem trực quan hơn, bạn có thể mở dashboard để xem nhé!”

# Quy tắc định dạng:
# - Trả lời bằng văn bản thuần, không sử dụng Markdown phức tạp như bảng, code block, tiêu đề ###, ký tự đặc biệt.
# - Có thể sử dụng bullet dạng “•” cho dễ đọc.
# - Viết thân thiện, rõ ràng, mạch lạc, giúp người dùng dễ hiểu.

# Nếu câu hỏi liên quan đến số liệu, top, rank, lọc dữ liệu, hãy gợi ý chuyển sang chatbot TRUY VẤN.

# Trả lời bằng tiếng Việt.
# """.strip()



# def answer_from_txt(user_msg: str, history: List[Tuple[str, str]]) -> str:
#     """
#     Chatbot kiến thức sử dụng LangChain + Cơ chế xoay vòng Key.
#     Đã fix lỗi 'list object has no attribute strip'.
#     """
#     try:
#         # 1. Tìm các chunk liên quan (Bước này không tốn API Key Gemini)
#         top_chunks = search_similar_chunks(user_msg, top_k=3)
#         context_text = "\n\n---\n\n".join(ch["text"] for ch in top_chunks)

#         # 2. Xử lý lịch sử chat
#         history_text = ""
#         for role, msg in history[-4:]:
#             prefix = "Người dùng" if role == "user" else "Trợ lý"
#             history_text += f"{prefix}: {msg}\n"

#         # 3. Tạo prompt đầy đủ
#         full_prompt = f"""{SYSTEM_PROMPT_TXT}

# Dưới đây là một số đoạn tài liệu nội bộ liên quan:
# {context_text}

# Lịch sử hội thoại gần đây:
# {history_text}

# Câu hỏi của người dùng:
# {user_msg}

# Hãy trả lời dựa trên các đoạn tài liệu trên. Nếu không chắc chắn, hãy nói rõ là bạn không có đủ thông tin.
# """

#         # 4. VÒNG LẶP RETRY VÀ XOAY KEY
#         max_retries = 35 
        
#         for attempt in range(max_retries):
#             try:
#                 # --- LẤY KEY MỚI MỖI LẦN THỬ ---
#                 llm = get_resilient_llm()
                
#                 # Gọi LLM
#                 response = llm.invoke(full_prompt)
                
#                 # --- FIX LỖI: XỬ LÝ NỘI DUNG TRẢ VỀ ---
#                 content = response.content
                
#                 final_text = ""
#                 if isinstance(content, list):
#                     # Nếu là List, ghép các phần tử lại thành chuỗi
#                     for part in content:
#                         if isinstance(part, str):
#                             final_text += part
#                         elif isinstance(part, dict) and "text" in part:
#                             final_text += part["text"]
#                         else:
#                             final_text += str(part)
#                 else:
#                     # Nếu là String thì dùng luôn
#                     final_text = str(content)
                
#                 return final_text.strip()
#                 # --------------------------------------
                
#             except Exception as e:
#                 error_msg = str(e)
#                 # Danh sách các lỗi cần đổi Key
#                 retry_errors = [
#                     "429", "Quota", "ResourceExhausted", 
#                     "400", "403", "Key not found", "API_KEY_INVALID", 
#                     "Invalid argument"
#                 ]
                
#                 if any(err in error_msg for err in retry_errors):
#                     print(f"⚠️ Knowledge Bot: Key lỗi (Lần {attempt+1}). Đang đổi key khác...")
#                     continue 
#                 else:
#                     return f"⚠️ Lỗi xử lý Chatbot Kiến thức: {error_msg}"

#         return "⚠️ Hệ thống đang quá tải (Đã thử hết tất cả API Key). Vui lòng thử lại sau."

#     except Exception as e:
#         return f"⚠️ Lỗi hệ thống RAG: `{e}`"


# # =========================
# def render_message(role: str, msg: str):
#     # --- ĐOẠN FIX LỖI QUAN TRỌNG ---
#     # Kiểm tra nếu msg là None thì gán giá trị mặc định
#     if msg is None:
#         msg = "⚠️ (Hệ thống không trả về nội dung)"
    
#     # Chuyển ép kiểu sang string để tránh lỗi html.escape
#     msg = str(msg)
#     # -------------------------------

#     if role == "user":
#         safe_msg = html.escape(msg).replace("\n", "<br>")
#         avatar_html = '<div class="avatar user">🧑</div>'
#         bubble_html = f"""
#             <div class="message-bubble user">
#               <div class="message-meta">Bạn</div>
#               <div>{safe_msg}</div>
#             </div>
#         """
#         row_html = f'<div class="message-row user">{bubble_html}{avatar_html}</div>'
#     else:
# # --- XỬ LÝ LINK CHO BOT ---
#         # 1. Thay thế xuống dòng thành thẻ <br>
#         safe_msg = msg.replace("\n", "<br>")
        
#         # 2. Dùng Regex để biến Markdown Link [Text](URL) thành HTML Link <a ...>
#         # Pattern: [bất kỳ ký tự nào ngoại trừ ]](bất kỳ ký tự nào ngoại trừ ))
#         markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
#         # Replacement: Thẻ a màu xanh, gạch chân, mở tab mới
#         html_link_replacement = r'<a href="\2" target="_blank" style="color: #0000EE; text-decoration: underline; font-weight: bold;">\1</a>'
        
#         safe_msg = re.sub(markdown_link_pattern, html_link_replacement, safe_msg)
#         # --------------------------

#         avatar_html = '<div class="avatar assistant">🤖</div>'
#         bubble_html = f"""
#             <div class="message-bubble assistant">
#               <div class="message-meta">Bot</div>
#               <div>{safe_msg}</div>
#             </div>
#         """
#         row_html = f'<div class="message-row assistant">{avatar_html}{bubble_html}</div>'

#     st.markdown(row_html, unsafe_allow_html=True)


# # =========================
# #   CHATBOT TRUY VẤN (PLACEHOLDER)
# # =========================
# def answer_from_query_bot(user_msg: str, history: List[Tuple[str, str]]) -> str:
#     """
#     Gọi Text-to-MQL Agent để lấy số liệu từ MongoDB.
#     """
#     # 1. Tạo thread_id cho phiên chat nếu chưa có
#     if "thread_id" not in st.session_state:
#         import uuid
#         st.session_state.thread_id = f"user_{uuid.uuid4().hex[:8]}"
    
#     thread_id = st.session_state.thread_id

#     # 2. Gọi hàm xử lý logic
#     try:
#         # Import hàm process_user_query từ file agent/core.py
#         # (Đảm bảo bạn đã tạo file core.py theo hướng dẫn ở câu trả lời trước)
#         from agent.core import process_user_query
        
#         # Gọi hàm
#         response = process_user_query(user_msg, thread_id)
#         return response
        
#     except Exception as e:
#         return f"⚠️ Lỗi Agent: {str(e)}"



#     # return "chatbot truy vấn"

# # =========================
# #   SESSION STATE
# # =========================
# if "chat_history" not in st.session_state:
#     # Khởi tạo với 1 lời chào để trang nhìn đỡ trống
#     st.session_state.chat_history: List[Tuple[str, str]] = [
#         (
#             "assistant",
#             "Xin chào, tôi là chatbot hỗ trợ dự án Spotify & Billboard.\n"
#             "• Hỏi về khái niệm, trường dữ liệu, KPI, insight → tôi dùng tài liệu txt (embeddings) để trả lời.\n"
#             "• Hỏi về số liệu/top/rank/bài hát cụ thể → tôi sẽ chuyển sang chatbot TRUY VẤN.\n"
#             "• Tôi luôn sẵn sàng giúp bạn! 😊",
#         )
#     ]

# st.subheader("💬 Chat với bot")

# # =========================
# #   KHUNG HIỂN THỊ CHAT
# # =========================
# st.markdown('<div class="chat-outer">', unsafe_allow_html=True)

# # Lịch sử cũ
# for role, msg in st.session_state.chat_history:
#     render_message(role, msg)

# # Placeholder cho message mới trong lần run hiện tại
# new_user_placeholder = st.empty()
# bot_placeholder = st.empty()

# st.markdown("</div>", unsafe_allow_html=True)

# # =========================
# #   THANH DƯỚI: NÚT XÓA + Ô NHẬP
# # =========================
# bottom_bar = st.container()
# with bottom_bar:
#     col_clear, col_input = st.columns([1, 9])

#     with col_clear:
#         if st.button("🧹 Xóa lịch sử", help="Xóa lịch sử chat", key="clear_chat"):
#             st.session_state.chat_history = []
#             st.rerun()

#     with col_input:
#         user_msg = st.chat_input("Nhập câu hỏi (về dữ liệu / kiến thức ...)")

# # =========================
# #   XỬ LÝ TIN NHẮN MỚI
# # =========================
# if user_msg:
#     # 1. Hiện ngay tin nhắn user ở placeholder (real-time feel)
#     with new_user_placeholder:
#         render_message("user", user_msg)

#     # 2. Router intent
#     # intent = classify_intent(user_msg)
#     with st.spinner("🧠 Đang phân tích ngữ cảnh..."):
#         # --- SỬA DÒNG NÀY ---
#         intent = route_query(user_msg, st.session_state.chat_history)

#     # 3. Gọi chatbot phù hợp
#     if intent == "knowledge":
#         with st.spinner("📖 Tôi đang phản hồi vui lòng chờ trong giây lát"):
#             answer = answer_from_txt(user_msg, st.session_state.chat_history)
#     else:
#         with st.spinner("📊 Chuyển sang chatbot truy vấn chờ tui tý nhe "):
#             answer = answer_from_query_bot(user_msg, st.session_state.chat_history)

#     # 4. Hiện bot trả lời
#     with bot_placeholder:
#         render_message("assistant", answer)

#     # 5. Lưu vào lịch sử cho các lần chat tiếp theo
#     st.session_state.chat_history.append(("user", user_msg))
#     st.session_state.chat_history.append(("assistant", answer))



# pages/3_Chatbot_Gemini.py
"""
Chatbot Page 3 – UI Nâng cấp:
- Logic: Giữ nguyên (Router, Key Rotation, Retry).
- UI: Đẹp hơn (Spotify Theme), Bảng Markdown render chuẩn, Link clickable.
"""

import os
import re
import sys
import html
from typing import List, Tuple
from pathlib import Path
import streamlit as st
import markdown # 👈 Cần cài: pip install markdown

# =========================
#   FIX ĐƯỜNG IMPORT
# =========================
PAGES_DIR = Path(__file__).resolve().parent
APP_DIR = PAGES_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Import logic
from knowledge.embedding_utils import search_similar_chunks
from agent.router import route_query
from agent.core import process_user_query 
from agent.config import get_resilient_llm

# =========================
#   CẤU HÌNH GIAO DIỆN
# =========================
st.set_page_config(page_title="Spotify Chatbot", page_icon="🎵", layout="wide")

st.title("💬 Chatbot Gemini Spotify Assistant")
st.caption(
    "🤖 **Trợ lý dữ liệu âm nhạc:**\n"
    "1️⃣ **Hỏi Kiến thức:** Giải thích thuật ngữ, xu hướng (Nguồn: Tài liệu).\n"
    "2️⃣ **Truy vấn Số liệu:** Lấy dữ liệu thực tế từ MongoDB (Top BXH, Stream...)."
)

# =========================
#   🎨 CSS - GIAO DIỆN ĐẸP & BẢNG CHUẨN
# =========================
st.markdown(
    """
    <style>
    /* Khung chat tổng */
    .chat-outer {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f9f9f9;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
    }

    /* Hàng tin nhắn */
    .message-row {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
    }
    .message-row.user { justify-content: flex-end; }
    .message-row.assistant { justify-content: flex-start; }

    /* Bong bóng chat */
    .message-bubble {
        padding: 12px 18px;
        border-radius: 12px;
        max-width: 85%;
        font-size: 1rem;
        line-height: 1.6;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        overflow-x: auto; /* Để bảng không bị vỡ nếu quá rộng */
    }

    /* User: Màu Gradient Xanh Spotify */
    .message-bubble.user {
        background: linear-gradient(135deg, #1DB954 0%, #117a36 100%);
        color: white;
        border-bottom-right-radius: 2px;
    }
    .message-bubble.user a { color: #fff; text-decoration: underline; }

    /* Bot: Màu Trắng, Chữ Đen */
    .message-bubble.assistant {
        background-color: #ffffff;
        color: #222;
        border: 1px solid #e0e0e0;
        border-bottom-left-radius: 2px;
    }

    .avatar {
        width: 45px; /* Tăng kích thước chút cho rõ */
        height: 45px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 10px;
        flex-shrink: 0;
        overflow: hidden; /* Để ảnh không bị lòi ra ngoài hình tròn */
        background-color: white; /* Nền trắng để logo trong suốt vẫn nổi */
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        border: 2px solid #1DB954; /* Viền xanh Spotify đặc trưng */
    }
    .avatar.user { background-color: #e8f5e9; border: 2px solid #1DB954; }
    .avatar.assistant { background-color: #1DB954; border: 2px solid #530; }

    
    


    /* --- CSS QUAN TRỌNG CHO BẢNG (TABLE) --- */
    .message-bubble table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 0.95em;
        background-color: white;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #ddd;
    }
    .message-bubble th {
        background-color: #1DB954; /* Header xanh */
        color: white;
        font-weight: bold;
        padding: 10px 15px;
        text-align: left;
    }
    .message-bubble td {
        padding: 8px 15px;
        border-bottom: 1px solid #eee;
        color: #333;
    }
    .message-bubble tr:nth-child(even) { background-color: #f8f9fa; }
    .message-bubble tr:hover { background-color: #f1f1f1; }

    /* Link trong Bot */
    .message-bubble a {
        color: #1DB954;
        font-weight: bold;
        text-decoration: none;
    }
    .message-bubble a:hover { text-decoration: underline; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
#   CHECK FILE DATA
# =========================
def load_knowledge() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_path = os.path.abspath(os.path.join(base_dir, "..", "knowledge", "data_dictionary.txt"))
    if os.path.exists(knowledge_path):
        return "Found"
    return ""

if not load_knowledge():
    st.warning("⚠ Chưa tìm thấy `data_dictionary.txt`. Kiểm tra lại đường dẫn.")

# =========================
#   SYSTEM PROMPT (Giữ nguyên)
# =========================
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
#   HÀM HIỂN THỊ (QUAN TRỌNG: SỬA LINK & BẢNG)
# =========================
def render_message(role: str, msg: str):
    if msg is None: msg = "⚠️ (Không có nội dung)"
    msg = str(msg)

    if role == "user":
        # User: Text đơn giản
        safe_msg = html.escape(msg).replace("\n", "<br>")
        avatar = '<div class="avatar user">👤</div>'
        bubble = f'<div class="message-bubble user"><div style="font-size:0.75rem;opacity:0.8">Bạn</div>{safe_msg}</div>'
        html_row = f'<div class="message-row user">{bubble}{avatar}</div>'
    else:
        # Bot: Dùng thư viện Markdown để render Bảng & Link chuẩn xác
        try:
            # extensions=['tables'] giúp chuyển Markdown Table -> HTML Table
            html_content = markdown.markdown(msg, extensions=['tables', 'fenced_code', 'nl2br'])
            
            # Fix Link: Thêm target="_blank" để mở tab mới
            html_content = html_content.replace('<a href=', '<a target="_blank" href=')
            
        except Exception:
            # Fallback nếu lỗi
            html_content = html.escape(msg).replace("\n", "<br>")

        avatar = '<div class="avatar assistant">🤖</div>'
        bubble = f'<div class="message-bubble assistant"><div style="font-size:0.75rem;color:#1DB954;font-weight:bold">Spotify Bot</div>{html_content}</div>'
        html_row = f'<div class="message-row assistant">{avatar}{bubble}</div>'

    st.markdown(html_row, unsafe_allow_html=True)

# =========================
#   CHATBOT KIẾN THỨC (GIỮ NGUYÊN LOGIC)
# =========================
def answer_from_txt(user_msg: str, history: List[Tuple[str, str]]) -> str:
    try:
        top_chunks = search_similar_chunks(user_msg, top_k=3)
        context_text = "\n\n---\n\n".join(ch["text"] for ch in top_chunks)

        history_text = ""
        for role, msg in history[-4:]:
            prefix = "User" if role == "user" else "Assistant"
            history_text += f"{prefix}: {msg}\n"

        full_prompt = f"""{SYSTEM_PROMPT_TXT}
        CONTEXT: {context_text}
        HISTORY: {history_text}
        QUESTION: {user_msg}
        """

        max_retries = 35 
        for attempt in range(max_retries):
            try:
                llm = get_resilient_llm()
                response = llm.invoke(full_prompt)
                
                content = response.content
                final_text = ""
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, str): final_text += part
                        elif isinstance(part, dict): final_text += part.get("text", "")
                        else: final_text += str(part)
                else:
                    final_text = str(content)
                
                return final_text.strip()

            except Exception as e:
                error_msg = str(e)
                if any(c in error_msg for c in ["429", "Quota", "400", "403", "Key", "INVALID"]):
                    print(f"⚠️ Knowledge Bot: Key lỗi ({attempt+1}). Đổi key...")
                    continue 
                return f"⚠️ Lỗi Knowledge: {error_msg}"

        return "⚠️ Hệ thống quá tải. Vui lòng thử lại sau."
    except Exception as e:
        return f"⚠️ Lỗi RAG: {e}"

# =========================
#   CHATBOT TRUY VẤN (GIỮ NGUYÊN LOGIC)
# =========================
def answer_from_query_bot(user_msg: str, history: List[Tuple[str, str]]) -> str:
    if "thread_id" not in st.session_state:
        import uuid
        st.session_state.thread_id = f"user_{uuid.uuid4().hex[:8]}"
    
    try:
        from agent.core import process_user_query
        # Có thể thêm history vào input nếu muốn
        response = process_user_query(user_msg, st.session_state.thread_id)
        return response
    except Exception as e:
        return f"⚠️ Lỗi Agent: {str(e)}"

# =========================
#   MAIN APP
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        ("assistant", "Chào bạn! 🎵 Tôi là trợ lý Spotify. Bạn cần tìm hiểu thông tin gì?")
    ]

# 1. Hiển thị Lịch sử
st.markdown('<div class="chat-outer">', unsafe_allow_html=True)
for role, msg in st.session_state.chat_history:
    render_message(role, msg)

new_user_placeholder = st.empty()
bot_placeholder = st.empty()
st.markdown('</div>', unsafe_allow_html=True)

# 2. Input
with st.container():
    col1, col2 = st.columns([8, 1])
    with col1:
        user_msg = st.chat_input("Nhập câu hỏi...")
    with col2:
        if st.button("🗑️", help="Xóa lịch sử"):
            st.session_state.chat_history = []
            st.rerun()

# 3. Xử lý
if user_msg:
    with new_user_placeholder:
        render_message("user", user_msg)

    with st.spinner("🔄 Đang xử lý..."):
        intent = route_query(user_msg, st.session_state.chat_history)
    
    if intent == "knowledge":
        with st.spinner("📚 Đang tra cứu tài liệu..."):
            answer = answer_from_txt(user_msg, st.session_state.chat_history)
    else:
        with st.spinner("🔍 Đang truy vấn Database..."):
            answer = answer_from_query_bot(user_msg, st.session_state.chat_history)
    
    with bot_placeholder:
        render_message("assistant", answer)
    
    st.session_state.chat_history.append(("user", user_msg))
    st.session_state.chat_history.append(("assistant", answer))