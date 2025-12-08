import os
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mongodb.agent_toolkit.database import MongoDBDatabase
from pymongo import MongoClient

# 1. Cấu hình MongoDB
# Lưu ý: Nên dùng st.secrets trong thực tế, nhưng hardcode tạm cũng được
MONGO_URI = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "spotify_project" # Đảm bảo tên DB đúng

# 2. Danh sách API Key (Đã cắt bớt để gọn, bạn paste full list của bạn vào)
API_KEYS = [
    "AIzaSyA-qum1Rr9TG9GpYXUFuKSb0aVM0OJKNIs",
    "AIzaSyCMExI2cUX8vVkVucMGfwLt4jQJqtXJNrk",
    "AIzaSyDKh8SmyE6ILNV3bYEhNy4X-eTSYe8-zMY",
    "AIzaSyBGBWVQhJiKbqGVjXW7iuts9GdUyGyFZ80",
    "AIzaSyCuttcW56fBgRbz6C4W6b72FxBc3yGtNm0",
    "AIzaSyCoj1KxFOm7xUicQinc-6pvirgYsnb1Kxs",
    "AIzaSyBnrIXwj35Fx64AeNYDM59FqsRzBZxzAdg",
    "AIzaSyDx3XaNaBK1EAb258qQHGEAniAnNBTdMsw",
    "AIzaSyCmgq9ukVZS75TtEwzVGR2DKP4il859pWc",
    "AIzaSyB3XoD9XEhkGU2PCsolvRiYeO0FY6B9heA",
    "AIzaSyDK2mGjOD1JknDkjAz38RVRXAvIlHDGKAc",
    "AIzaSyACY0xOZwRwE-9GxN6jFkahMN1GPIKPG3E",
    "AIzaSyD0Ib7B-mp3kY3t_HZeEFgWYANTGgQj5jU",
    "AIzaSyDdVijzTur3SoRRBlNYIy5zD16D2ZIbDLU",
    "AIzaSyC2wxDN_yK1e3UfAi2LfBB7Q3A0arsHNzs",
    "AIzaSyATC-JSLsNHJDCacViB3hIUQs-JsTXcxNA",
    "AIzaSyCayTvvqZh1uRoDHoHdAVqQmMUKbR_b6j4",
    "AIzaSyDPnAJCf1lZvaBll_5vl7ZzCwOG2T_gR3U",
    "AIzaSyAKnlUPhM-40yi71lHZRHxmU7HfiSNhQts",
    "AIzaSyD8YeCf0qZoIBJhH66WzB3K1yM93gTqfUE",
    "AIzaSyCSXH4jZ78WdKacSP39CPTQpGE6TjhpBSc",
    "AIzaSyC6DawNeJ4gngqfE7V2vfHD586gE-wKGP8",
    "AIzaSyCLeo92kszjQiUveXIgT-hC-eD3tRC99E8",
    "AIzaSyCQ-4E3-nwz1NDYT0HCPfFC261uD6bJp6w",
    "AIzaSyAnmz9Rkw0Y6qEGAbT-QpRNnd5VevRRT6M",
    "AIzaSyAss-Vc3vZtj6WU2ykaAFhKPb0u5UOoHdA",
    "AIzaSyCIMl_or2WMrvRJN7UerrPdM0WnyVSC5yo",
    "AIzaSyDluupHOTk733Pq16JoIZ7JVsZ-nMZ_a4w",
    "AIzaSyAq6ZcNvtXLgUnRiBgiZpeDaJzksHMnAus",
    "AIzaSyCimazJT46huIJ5foOZQTF-xx4Hf10mUV4",
    "AIzaSyBOd21_uDZD0ZTNE6P35UXJeMkiBaZ8fig",
    "AIzaSyA57dS7XwcGOobaDYyHExEkrDjAe7aFjhU",
    "AIzaSyCBeNMUs0Zmo3YjajXuwsx5sd1KXH55XZw",
    "AIzaSyBlmJ8CVSUVKAyOX06dkj34GcVyUrhLxlA",
    "AIzaSyCkPvqo0_B5FQQGFRYXm7J00Io2VfSXZig",
    "AIzaSyBDcUn-A0EjsRUsfNU202OcvnOVuUHBYuU",
    "AIzaSyD3cKG2IfXzj7qvThwDiUrw5IyZqAPh86Q"
]

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