# import time
# from langgraph.prebuilt import create_react_agent
# from langchain_mongodb.agent_toolkit.toolkit import MongoDBDatabaseToolkit

# # Import các thành phần từ config, memory, prompt
# from agent.config import db, mongo_client, get_resilient_llm
# from agent.memory import LLMSummarizingMongoDBSaver
# from agent.prompt import MONGODB_AGENT_SYSTEM_PROMPT

# # 1. Khởi tạo Toolkit & Memory (Cái này giữ cố định được)
# # Lưu ý: Toolkit cần LLM để đọc schema, ta dùng hàm get_resilient_llm() để mỗi lần init nó lấy key mới
# def get_toolkit():
#     return MongoDBDatabaseToolkit(db=db, llm=get_resilient_llm())

# checkpointer = LLMSummarizingMongoDBSaver(mongo_client)

# # 2. Hàm tạo Agent "Tươi" (Fresh Agent Factory)
# def build_fresh_agent():
#     """
#     Tạo một con Agent mới toanh với API Key mới nhất cho CẢ TOOLKIT và AGENT.
#     """
#     # Lấy key mới
#     new_llm = get_resilient_llm()
    
#     # --- QUAN TRỌNG: TẠO LẠI TOOLKIT VỚI KEY MỚI ---
#     # Nếu không tạo lại, Toolkit vẫn dùng key cũ để soi Schema -> Vẫn lỗi 429
#     toolkit = MongoDBDatabaseToolkit(db=db, llm=new_llm)
#     all_tools = toolkit.get_tools()
    
#     # Lọc bỏ tool gây lỗi
#     safe_tools = [t for t in all_tools if t.name != "mongodb_query_checker"]
    
#     return create_react_agent(
#         new_llm,
#         safe_tools, 
#         prompt=MONGODB_AGENT_SYSTEM_PROMPT,
#         checkpointer=checkpointer
#     )

# # 3. Hàm xử lý chính (CÓ CƠ CHẾ RETRY TỰ ĐỘNG)
# def process_user_query(user_input: str, thread_id: str) -> str:
#     """
#     Nhận input -> Chạy Agent -> Làm sạch kết quả -> Trả về text đẹp.
#     """
#     config = {"configurable": {"thread_id": thread_id}}
#     max_retries = 3 
    
#     for attempt in range(max_retries):
#         try:
#             # Tạo Agent mới
#             current_agent = build_fresh_agent()
            
#             # Chạy agent
#             events = current_agent.stream(
#                 {"messages": [("user", user_input)]}, 
#                 config, 
#                 stream_mode="values"
#             )

#             final_response = "Xin lỗi, tôi không tìm thấy thông tin."
            
#             # Lấy tin nhắn cuối cùng
#             for event in events:
#                 messages = event.get("messages", [])
#                 if messages:
#                     last_msg = messages[-1]
#                     if last_msg.type == "ai" and last_msg.content:
                        
#                         # --- ĐOẠN SỬA QUAN TRỌNG: LÀM SẠCH DỮ LIỆU ---
#                         raw_content = last_msg.content
                        
#                         if isinstance(raw_content, list):
#                             # Nếu là List (do Gemini trả về), chỉ lấy phần 'text' và ghép lại
#                             # Bỏ qua phần 'extras' hay 'signature'
#                             text_parts = []
#                             for item in raw_content:
#                                 if isinstance(item, dict):
#                                     text_parts.append(item.get("text", ""))
#                                 elif isinstance(item, str):
#                                     text_parts.append(item)
                            
#                             final_response = "".join(text_parts)
#                         else:
#                             # Nếu là String bình thường thì giữ nguyên
#                             final_response = str(raw_content)
#                         # ---------------------------------------------
            
#             return final_response

#         except Exception as e:
#             error_msg = str(e)
#             if "429" in error_msg or "Quota" in error_msg or "ResourceExhausted" in error_msg:
#                 print(f"⚠️ Lần thử {attempt+1} hết Quota. Đổi key...")
#                 continue 
#             else:
#                 return f"⚠️ Lỗi xử lý Agent: {error_msg}"

#     return "⚠️ Hệ thống đang quá tải. Vui lòng thử lại sau."



import time
import uuid
from langgraph.prebuilt import create_react_agent
from langchain_mongodb.agent_toolkit.toolkit import MongoDBDatabaseToolkit

# Import các thành phần từ config, memory, prompt
from agent.config import db, mongo_client, get_resilient_llm
from agent.memory import LLMSummarizingMongoDBSaver
from agent.prompt import MONGODB_AGENT_SYSTEM_PROMPT

# CẤU HÌNH GIỚI HẠN BỘ NHỚ
# 40 steps tương đương khoảng 20 câu hỏi đáp (Mỗi câu gồm User + AI = 2 steps)
MAX_CHECKPOINTS = 10000


# 1. Khởi tạo Toolkit & Memory
def get_toolkit():
    return MongoDBDatabaseToolkit(db=db, llm=get_resilient_llm())

checkpointer = LLMSummarizingMongoDBSaver(mongo_client)

# 2. Hàm tạo Agent "Tươi" (Fresh Agent Factory)
def build_fresh_agent():
    """
    Tạo một con Agent mới toanh với API Key mới nhất.
    Đã lọc bỏ tool 'mongodb_query_checker' để tránh lỗi.
    """
    toolkit = get_toolkit()
    all_tools = toolkit.get_tools()
    
    # Lọc bỏ tool gây lỗi
    safe_tools = [t for t in all_tools if t.name != "mongodb_query_checker"]
    
    # Lấy LLM mới từ kho key
    new_llm = get_resilient_llm()
    
    return create_react_agent(
        new_llm,
        safe_tools,
        prompt=MONGODB_AGENT_SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

# 3. Hàm xử lý chính (CÓ QUẢN LÝ CHECKPOINT & RETRY)
def process_user_query(user_input: str, thread_id: str) -> str:
    """
    Nhận input -> Kiểm tra dung lượng bộ nhớ -> Chạy Agent.
    Nếu bộ nhớ đầy -> Tự động tạo thread mới (Reset ngữ cảnh).
    """
    
    # --- LOGIC KIỂM TRA & GIỚI HẠN CHECKPOINT ---
    active_thread_id = thread_id
    try:
        # Truy cập trực tiếp vào DB checkpoint để đếm số lượng
        # MongoDBSaver mặc định lưu vào database tên "checkpoint_db" hoặc "my_db" tùy lúc khởi tạo client
        # Ở đây ta giả định là 'checkpointing_db' (tên mặc định của thư viện) hoặc tên trong config
        # Để an toàn, ta dùng db_name từ đối tượng checkpointer nếu có thể, hoặc hardcode tên DB checkpointer của bạn
        
        # LƯU Ý: Tên DB checkpoint mặc định của thư viện là 'langgraph_checkpoint' hoặc do bạn đặt
        # Hãy kiểm tra lại trong MongoDB Compass xem nó tên gì. 
        # Nếu không chắc, cứ để mặc định code thư viện tự xử lý việc ghi, ta chỉ đọc để đếm.
        
        # Cách an toàn nhất: Dùng đúng database name mà bạn thấy trong MongoDB Atlas
        db_check = mongo_client["checkpointing_db"] # Tên mặc định thường thấy
        col_check = db_check["checkpoints"]
        
        # Đếm số dòng checkpoint của thread hiện tại
        count = col_check.count_documents({"thread_id": thread_id})
        
        if count >= MAX_CHECKPOINTS:
            print(f"⚠️ Thread {thread_id} đã đầy ({count} steps). Đang tạo phiên mới...")
            
            # Tạo ID mới duy nhất bằng UUID để tránh trùng lặp tuyệt đối
            active_thread_id = f"{thread_id}_{uuid.uuid4().hex[:8]}"
            
    except Exception as e:
        # Nếu lỗi kết nối DB phụ thì in warning nhưng vẫn chạy tiếp với thread cũ
        print(f"⚠️ Lỗi kiểm tra checkpoint (vẫn tiếp tục): {e}")
        active_thread_id = thread_id
    # --------------------------------------------

    config = {"configurable": {"thread_id": active_thread_id}}
    
    # Số lần thử lại tối đa (Khớp với số lượng key của bạn để tận dụng hết)
    max_retries = 37 
    
    for attempt in range(max_retries):
        try:
            # Tạo Agent mới (Lấy Key mới)
            current_agent = build_fresh_agent()
            
            # Chạy agent
            events = current_agent.stream(
                {"messages": [("user", user_input)]}, 
                config, 
                stream_mode="values"
            )

            final_response = "Xin lỗi, tôi không tìm thấy thông tin."
            
            # Lấy tin nhắn cuối cùng
            for event in events:
                messages = event.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if last_msg.type == "ai" and last_msg.content:
                        # Làm sạch dữ liệu (Xử lý List/String)
                        raw_content = last_msg.content
                        if isinstance(raw_content, list):
                            text_parts = []
                            for item in raw_content:
                                if isinstance(item, dict):
                                    text_parts.append(item.get("text", ""))
                                elif isinstance(item, str):
                                    text_parts.append(item)
                            final_response = "".join(text_parts)
                        else:
                            final_response = str(raw_content)
            
            # Nếu đã tạo thread mới, thông báo nhẹ cho user biết ở cuối câu trả lời
            if active_thread_id != thread_id:
                final_response += "\n\n*(Hệ thống: Đã tự động làm mới phiên chat để tối ưu hiệu suất)*"
                
            # QUAN TRỌNG: Thành công thì thoát ngay lập tức
            return final_response

        except Exception as e:
            error_msg = str(e)
            # Chỉ retry khi gặp lỗi Quota (429)
            if "429" in error_msg or "Quota" in error_msg or "ResourceExhausted" in error_msg:
                print(f"⚠️ Lần thử {attempt+1}/{max_retries} hết Quota. Đang đổi Key mới...")
                continue 
            else:
                # Các lỗi khác (cú pháp, logic) thì dừng và báo lỗi ngay
                return f"⚠️ Lỗi xử lý Agent: {error_msg}"

    return "⚠️ Hệ thống đang quá tải (Hết Quota trên tất cả các Key). Vui lòng thử lại sau."