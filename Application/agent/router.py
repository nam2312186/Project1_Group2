from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agent.config import get_resilient_llm
from typing import List, Tuple

# Lưu ý: Không cần import build_fresh_agent vì Router chạy độc lập, nhẹ nhàng hơn.

ROUTER_PROMPT = """
Bạn là một Router Agent thông minh. Nhiệm vụ của bạn là phân loại câu hỏi hiện tại của người dùng vào 1 trong 2 nhóm: **DATABASE** hoặc **KNOWLEDGE**.

HÃY SỬ DỤNG LỊCH SỬ HỘI THOẠI ĐỂ HIỂU NGỮ CẢNH (nếu câu hỏi ngắn gọn hoặc mơ hồ).

1. **DATABASE**: 
   - Truy xuất số liệu, thống kê, danh sách, so sánh, thông tin cụ thể về bài hát/nghệ sĩ.
   - Ngữ cảnh: Nếu người dùng đang hỏi về số liệu và hỏi tiếp "còn bài kia thì sao?", "top 10 thì sao?".
   - Các câu hỏi phân tích bài hát, nghệ sĩ, xu hướng cần dữ liệu cụ thể.

2. **KNOWLEDGE**: 
   - Định nghĩa, khái niệm, giải thích ý nghĩa KPI, quy trình, thông tin chung.
   - Ngữ cảnh: Nếu người dùng đang hỏi định nghĩa và hỏi tiếp "nó có ý nghĩa gì?".

---
LỊCH SỬ HỘI THOẠI:
{history}
---
CÂU HỎI HIỆN TẠI: "{question}"

YÊU CẦU ĐẦU RA:
- Chỉ trả về đúng 1 từ duy nhất: **DATABASE** hoặc **KNOWLEDGE**.
"""

def route_query(user_query: str, chat_history: List[Tuple[str, str]] = []) -> str:
    """
    Phân loại câu hỏi với cơ chế RETRY & XOAY KEY (Chống lỗi 429).
    """
    # 1. Xử lý lịch sử chat thành chuỗi văn bản (Làm 1 lần dùng chung)
    history_text = "Không có lịch sử."
    if chat_history:
        recent_history = chat_history[-4:] 
        history_lines = []
        for role, msg in recent_history:
            role_name = "User" if role == "user" else "Bot"
            clean_msg = str(msg).replace("\n", " ").strip()[:150]
            history_lines.append(f"{role_name}: {clean_msg}")
        history_text = "\n".join(history_lines)

    # 2. CƠ CHẾ RETRY XOAY KEY (Giống agent/core.py)
    max_retries = 37 # Thử tối đa 3 key khác nhau nếu lỗi
    
    for attempt in range(max_retries):
        try:
            # --- LẤY KEY MỚI MỖI LẦN THỬ ---
            llm = get_resilient_llm() 
            
            # Tạo chain
            prompt = PromptTemplate.from_template(ROUTER_PROMPT)
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser
            
            # Chạy phân loại
            result = chain.invoke({
                "history": history_text,
                "question": user_query
            })
            
            cleaned_result = result.strip().upper()
            
            if "DATABASE" in cleaned_result:
                return "query"
            else:
                return "knowledge"
                
        except Exception as e:
            error_msg = str(e)
            # Kiểm tra lỗi Quota để đổi key
            if "429" in error_msg or "Quota" in error_msg or "ResourceExhausted" in error_msg:
                print(f"⚠️ Router: Key lỗi (Lần {attempt+1}). Đang đổi key khác...")
                continue # Thử lại vòng lặp với key mới
            else:
                # Nếu lỗi khác (không phải quota), in ra và fallback về knowledge cho an toàn
                print(f"⚠️ Lỗi Router (Không phải Quota): {e}")
                return "knowledge"

    # Nếu thử hết 3 lần vẫn lỗi
    print("⚠️ Router: Hết sạch quota sau 3 lần thử. Fallback về Knowledge.")
    return "knowledge"