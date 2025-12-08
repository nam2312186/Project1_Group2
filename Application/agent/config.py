import os
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mongodb.agent_toolkit.database import MongoDBDatabase
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
# 1. Cấu hình MongoDB
# Lưu ý: Nên dùng st.secrets trong thực tế, nhưng hardcode tạm cũng được
MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "spotify_project" # Đảm bảo tên DB đúng

# 2. Danh sách API Key (Đã cắt bớt để gọn, bạn paste full list của bạn vào)
# 2. Lấy danh sách Key từ file .env và tách thành List
# --- CODE LÀM SẠCH KEY MỚI (MẠNH MẼ HƠN) ---
# 1. Load file .env (Dùng đường dẫn tuyệt đối để chắc chắn tìm thấy)
# 1. Load file .env (Dùng đường dẫn tuyệt đối)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 2. Lấy danh sách Key (Hỗ trợ cả 2 tên biến)
keys_string = os.getenv("GOOGLE_API_KEYS")
if not keys_string:
    keys_string = os.getenv("API_KEYS")

if not keys_string:
    print(f"⚠️ Đang tìm file .env tại: {env_path}")
    raise ValueError("❌ Không tìm thấy key! Hãy kiểm tra file .env")

# 3. Làm sạch Key
raw_list = keys_string.split(",")
API_KEYS = []
for k in raw_list:
    clean_k = k.strip().replace("\n", "").replace("\r", "").replace("'", "").replace('"', "").replace("[", "").replace("]", "")
    if len(clean_k) > 30:
        API_KEYS.append(clean_k)

print(f"✅ Đã tải thành công {len(API_KEYS)} API Keys hợp lệ.")

if len(API_KEYS) == 0:
    raise ValueError("❌ Danh sách Key rỗng sau khi lọc! Kiểm tra lại file .env")

class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0

    def get_next_key(self):
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key

key_manager = APIKeyManager(API_KEYS)

def get_resilient_llm():
    """Lấy LLM với key xoay vòng"""
    api_key = key_manager.get_next_key()

    # --- THÊM DÒNG NÀY ĐỂ KIỂM TRA ---
    print(f"🔍 DEBUG: Code đang dùng Key là: '{api_key}'") 
    # ---------------------------------
    return ChatGoogleGenerativeAI(
        model="gemini-flash-latest", # Hoặc gemini-pro nếu flash lỗi
        google_api_key=api_key,
        temperature=0,
        convert_system_message_to_human=True,
        max_output_tokens=8192,
        max_retries=0
    )

# Khởi tạo Global Objects để dùng chung
# db = MongoDBDatabase.from_connection_string(MONGO_URI, database=DB_NAME)


db = MongoDBDatabase.from_connection_string(MONGO_URI, database=DB_NAME)

# --- ĐOẠN NÀY CHÍNH LÀ ĐOẠN BẠN HỎI ---
mongo_client = MongoClient(
    MONGO_URI, 
    appname="spotify_project_agent" # Đã thêm lại appname (tùy chỉnh tên cho dễ nhớ)
)