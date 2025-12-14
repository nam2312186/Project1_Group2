import os
import random
import time
from pathlib import Path
from typing import Any, List, Optional

# Import LangChain & Google GenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_mongodb.agent_toolkit.database import MongoDBDatabase
from pymongo import MongoClient
from dotenv import load_dotenv

# =========================================================
# 1. CẤU HÌNH MÔI TRƯỜNG & API KEYS
# =========================================================

# Load file .env (Dùng đường dẫn tuyệt đối để tránh lỗi không tìm thấy file)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# +srv
# Cấu hình MongoDB
MONGO_URI = os.getenv("MONGO_URI") or "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "spotify_project" 

# Lấy và làm sạch danh sách API Key
keys_string = os.getenv("GOOGLE_API_KEYS") or os.getenv("API_KEYS")
if not keys_string:
    raise ValueError(f"❌ Không tìm thấy key! Hãy kiểm tra file .env tại {env_path}")

raw_list = keys_string.split(",")
API_KEYS = []
for k in raw_list:
    # Làm sạch kỹ càng các ký tự thừa
    clean_k = k.strip().replace("\n", "").replace("\r", "").replace("'", "").replace('"', "").replace("[", "").replace("]", "")
    if len(clean_k) > 20: # Key Google thường dài hơn 20 ký tự
        API_KEYS.append(clean_k)





if len(API_KEYS) == 0:
    raise ValueError("❌ Danh sách Key rỗng sau khi lọc! Kiểm tra lại file .env")




# =========================================================
# 2. QUẢN LÝ XOAY VÒNG KEY (KEY ROTATION)
# =========================================================


class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = random.randint(0, len(self.keys) - 1)
        
        # --- [NEW] Biến theo dõi các key đã dùng trong 1 phiên ---
        self.session_used_keys = set() 

    def get_next_key(self):
        """Lấy key tiếp theo và ghi nhận vào lịch sử dùng"""
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        
        # Ghi nhận key này đã được dùng
        self._mark_as_used(key)
        
        return key
    
    def _mark_as_used(self, key):
        """Hàm phụ trợ để lưu key vào set (xử lý cả SecretStr)"""
        if hasattr(key, "get_secret_value"):
            k_str = key.get_secret_value()
        else:
            k_str = str(key)
        self.session_used_keys.add(k_str)

    def reset_usage_stats(self):
        """Reset bộ đếm (gọi khi bắt đầu 1 câu hỏi mới của User)"""
        self.session_used_keys.clear()
        
    def get_usage_count(self):
        """Trả về số lượng key DUY NHẤT đã dùng"""
        return len(self.session_used_keys)

# Khởi tạo instance
key_manager = APIKeyManager(API_KEYS)

print(f"✅ Đã tải thành công {len(key_manager.keys)} API Keys hợp lệ.")

# =========================================================
# 3. CUSTOM LLM WRAPPER (CƠ CHẾ TỰ HỒI PHỤC)
# =========================================================

class ResilientChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """
    Lớp vỏ bọc thông minh: Tự động bắt lỗi Quota/Permission và đổi Key ngay lập tức
    để thực thi lại mà không làm sập chương trình.
    """
    key_manager: Any = None # Nhận vào trình quản lý key

# Trong file config.py
def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        
        # Thử tối đa số lượng key đang có
        max_retries = len(self.key_manager.keys)
        
        for attempt in range(max_retries):
            # --- [LOG 1] LOG KEY ĐANG SỬ DỤNG (ĐÃ SỬA LỖI SECRETSTR) ---
            current_key = self.google_api_key
            
            # Kiểm tra nếu là SecretStr thì lấy giá trị thật ra
            if hasattr(current_key, "get_secret_value"):
                key_str = current_key.get_secret_value()
            else:
                key_str = str(current_key)
            
            masked_key = f"{key_str[:5]}...{key_str[-5:]}"
            
            # Lấy vị trí key trong list
            try:
                # Lưu ý: Tìm trong key_manager cần dùng key_str (string thuần)
                key_index = self.key_manager.keys.index(key_str) + 1
            except:
                key_index = "?"
            
            print(f"🔑 [API] Đang request bằng Key #{key_index} ({masked_key})...")

            try:
                # Gọi hàm gốc
                return super()._generate(messages, stop, run_manager, **kwargs)
            
            except Exception as e:
                error_msg = str(e)
                short_error = error_msg.splitlines()[0] if error_msg else "Unknown Error"

                # --- [LOG 2] LOG LỖI CHI TIẾT ---
                print(f"❌ [Lỗi API] Key #{key_index} gặp lỗi: {short_error}")

                retry_codes = [
                    "429", "Quota", "ResourceExhausted", 
                    "403", "AccessDenied", "API_KEY_INVALID", 
                    "Key not found", "limit: 0",
                    "503", "Overloaded", "UNAVAILABLE", "parse", "corresponding"
                ]
                
                if any(code in error_msg for code in retry_codes):
                    # Lấy key mới
                    new_key = self.key_manager.get_next_key()
                    
                    print(f"🔄 [System] Đang tự động đổi sang Key tiếp theo...")
                    
                    # Cập nhật key mới (LangChain sẽ tự convert sang SecretStr nếu cần)
                    self.google_api_key = new_key
                    
                    # Xóa cache client cũ triệt để
                    for attr in ["_client", "client", "_async_client", "async_client"]:
                        if hasattr(self, attr):
                            delattr(self, attr)
                    
                    time.sleep(1) 
                    continue
                else:
                    print(f"☠️ [Fatal] Lỗi không thể cứu vãn trên Key #{key_index}: {error_msg}")
                    raise e
        
        print("⛔ [Stop] Đã thử hết tất cả API Key mà vẫn thất bại!")
        raise Exception("❌ All API Keys exhausted!")

# =========================================================
# 4. HÀM KHỞI TẠO LLM CHUẨN
# =========================================================

def get_resilient_llm():
    """
    Trả về instance LLM 'bất tử' với cấu hình tối ưu cho đồ án Spotify.
    """
    # Lấy key khởi đầu
    initial_key = key_manager.get_next_key()
    
    # Cấu hình an toàn để không bị chặn khi hỏi về nhạc Explicit
    safety_settings = {
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
    }

    return ResilientChatGoogleGenerativeAI(
        # Dùng Alias "latest" là an toàn nhất, tránh lỗi 404 hoặc Limit 0
        model="models/gemini-flash-latest", 
        
        google_api_key=initial_key,
        key_manager=key_manager, # Truyền trình quản lý key vào
        
        temperature=0, # Bằng 0 để query chính xác
        safety_settings=safety_settings,
        convert_system_message_to_human=True,
        max_output_tokens=8192,
        max_retries=1 # Tắt retry mặc định của thư viện để dùng retry của mình
    )

# =========================================================
# 5. KHỞI TẠO DATABASE
# =========================================================

db = MongoDBDatabase.from_connection_string(MONGO_URI, database=DB_NAME)

mongo_client = MongoClient(
    MONGO_URI, 
    appname="spotify_project_agent"
)


