import time
import uuid
from langgraph.prebuilt import create_react_agent
from langchain_mongodb.agent_toolkit.toolkit import MongoDBDatabaseToolkit

# Import các thành phần từ config, memory, prompt
from agent.config import db, mongo_client, get_resilient_llm, key_manager
from agent.memory import LLMSummarizingMongoDBSaver
from agent.prompt import MONGODB_AGENT_SYSTEM_PROMPT

# =========================================================
# CẤU HÌNH
# =========================================================
# Giới hạn số bước lưu trong bộ nhớ để tránh ngữ cảnh quá dài gây lú lẫn cho AI
MAX_CHECKPOINTS = 300 # Khoảng 30 câu hỏi-đáp

# Khởi tạo Memory Saver một lần (Dùng chung client)
checkpointer = LLMSummarizingMongoDBSaver(mongo_client)

# =========================================================
# HÀM KHỞI TẠO AGENT
# =========================================================

def build_agent():
    """
    Tạo Agent với LLM 'bất tử' (Resilient Wrapper) và bộ công cụ MongoDB.
    """
    # 1. Lấy LLM (Đã tích hợp cơ chế tự đổi Key khi lỗi Quota)
    llm = get_resilient_llm()
    
    # 2. Khởi tạo Toolkit với LLM này (để nó soi Schema)
    toolkit = MongoDBDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    
    # 3. Lọc bỏ tool 'query_checker'
    # Lý do: Tool này thường gây lỗi parse với Gemini mà không đem lại nhiều giá trị thực tế
    safe_tools = [t for t in tools if t.name != "mongodb_query_checker"]
    
    # 4. Tạo ReAct Agent
    return create_react_agent(
        llm,
        safe_tools,
        prompt=MONGODB_AGENT_SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

# =========================================================
# HÀM XỬ LÝ CHÍNH (MAIN PROCESS)
# =========================================================

# Trong file core.py

def process_user_query(user_input: str, thread_id: str) -> str:
    """
    Xử lý câu hỏi với Báo cáo Hiệu suất (Time & Keys).
    """
    # --- 1. KHỞI TẠO BỘ ĐẾM ---
    start_time = time.time()          # Bấm giờ
    key_manager.reset_usage_stats()   # Reset bộ đếm key về 0
    
    # Lấy key đầu tiên cho Agent cũng cần tính vào bộ đếm
    # (Vì build_agent gọi get_resilient_llm -> gọi get_next_key)
    
    print(f"\n{'='*40}")
    print(f"🧵 [Thread] Bắt đầu xử lý: {thread_id}")
    print(f"👤 [User] Input: {user_input}")
    print(f"{'='*40}\n")
    
    active_thread_id = thread_id
    
    # ... (Giữ nguyên phần Logic kiểm tra Memory Checkpoint cũ của bạn) ...
    try:
        db_check = mongo_client["checkpointing_db"] 
        col_check = db_check["checkpoints"]
        count = col_check.count_documents({"thread_id": thread_id})
        if count >= MAX_CHECKPOINTS:
            active_thread_id = f"{thread_id}_{uuid.uuid4().hex[:4]}"
            print(f"⚠️ [Memory] Đổi sang Thread mới: {active_thread_id}")
    except Exception:
        pass
    # ... (Hết phần Logic cũ) ...

    config = {"configurable": {"thread_id": active_thread_id}}
    
    try:
        # Tạo agent (Hành động này sẽ lấy 1 key -> bộ đếm tăng lên 1)
        agent = build_agent()
        
        print(f"🤖 [Agent] Đang thực thi...")

        events = agent.stream(
            {"messages": [("user", user_input)]},
            config,
            stream_mode="values"
        )
        
        final_response = "Xin lỗi, tôi không tìm thấy thông tin."
        
        # Xử lý kết quả trả về
        for event in events:
            messages = event.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if last_msg.type == "ai":
                    content = last_msg.content
                    if isinstance(content, list):
                        text_parts = [item["text"] if isinstance(item, dict) else item for item in content]
                        final_response = "".join(text_parts)
                    else:
                        final_response = str(content)
        
        # --- 2. TÍNH TOÁN HIỆU SUẤT ---
        end_time = time.time()
        duration = end_time - start_time
        used_keys_count = key_manager.get_usage_count()
        
        # Làm đẹp thời gian (vd: 12.53s)
        duration_str = f"{duration:.2f}s"
        
        # --- 3. IN BÁO CÁO RA CONSOLE ---
        print(f"\n{'-'*40}")
        print(f"📊 [PERFORMANCE REPORT]")
        print(f"⏱️  Thời gian xử lý : {duration_str}")
        print(f"🔑 Số Key đã dùng  : {used_keys_count} key(s)")
        print(f"{'-'*40}\n")

        if active_thread_id != thread_id:
            final_response += "\n\n*(Hệ thống: Đã tự động làm mới phiên chat)*"
            
        return final_response

    except Exception as e:
        print(f"❌ [Error] {e}")
        return f"⚠️ Lỗi: {str(e)}"