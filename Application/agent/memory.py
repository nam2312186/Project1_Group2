from typing import Dict, Any
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.runnables import RunnableConfig
from agent.config import get_resilient_llm 

class LLMSummarizingMongoDBSaver(MongoDBSaver):
    """MongoDB saver with LLM-powered intelligent summarization AND Key Rotation"""

    def __init__(self, client):
        # Gọi init của cha
        super().__init__(client)
        
        # Cache để tránh gọi LLM quá nhiều lần cho cùng một nội dung
        self._summary_cache = {}

    def summarize_step(self, checkpoint_data: Dict[str, Any]) -> str:
        """Generate contextual summary using LLM"""
        try:
            # 1. Trích xuất thông tin từ checkpoint
            channel_values = checkpoint_data.get("channel_values", {})
            messages = channel_values.get("messages", [])

            if not messages:
                return "🔄 Initial state"

            # Lấy tin nhắn cuối cùng
            last_message = messages[-1]
            if not last_message:
                return "📭 Empty step"

            # 2. Phân tích nội dung tin nhắn
            message_type = (
                type(last_message).__name__
                if hasattr(last_message, "__class__")
                else "unknown"
            )
            content = getattr(last_message, "content", "") or ""
            tool_calls = getattr(last_message, "tool_calls", [])

            # Xử lý trường hợp message dạng dict (fallback)
            if isinstance(last_message, dict):
                message_type = last_message.get("type", "unknown")
                content = last_message.get("content", "")
                tool_calls = last_message.get("tool_calls", [])

            # 3. Kiểm tra Cache
            # Tạo key đơn giản từ nội dung để tra cứu nhanh
            cache_key = f"{message_type}:{str(content)[:50]}:{len(tool_calls)}"
            if cache_key in self._summary_cache:
                return self._summary_cache[cache_key]

            # 4. Chuẩn bị ngữ cảnh cho Prompt
            context_parts = []
            if content:
                context_parts.append(f"Content: {str(content)[:200]}")
            if tool_calls:
                tool_info = []
                for tc in tool_calls[:2]:  # Chỉ lấy 2 tool đầu tiên
                    tool_name = tc.get("name", "unknown")
                    tool_args = str(tc.get("args", {}))[:100]
                    tool_info.append(f"{tool_name}({tool_args})")
                context_parts.append(f"Tool calls: {', '.join(tool_info)}")

            context = "\n".join(context_parts) if context_parts else "No content"

            # 5. LLM prompt
            prompt = f"""Summarize this conversation step in 2-5 words with a relevant emoji.

Message type: {message_type}
{context}

Guidelines:
- Use emojis: 👤 for user, 🤖 for AI, 🔧 for tools, 📊 for data, ✨ for results, 🎵 for music context.
- Be concise and descriptive.
- Focus on the action/intent.

Summary:"""

            # 6. Gọi LLM (Đã được tối ưu - bỏ vòng lặp thừa)
            try:
                # LLM này đã tự có cơ chế Resilience (retry & rotate key) bên trong
                llm = get_resilient_llm()
                response = llm.invoke(prompt)

                # XỬ LÝ LỖI LIST: Gemini Flash đôi khi trả về List thay vì String
                if isinstance(response.content, list):
                    summary_text = " ".join([item.get("text", "") for item in response.content if isinstance(item, dict)])
                else:
                    summary_text = str(response.content)

                summary = summary_text.strip()[:60]

            except Exception as e:
                # Nếu code chạy vào đây, nghĩa là ResilientLLM đã thử hết key mà vẫn lỗi
                # Hoặc là lỗi logic code (không phải lỗi network/api)
                print(f"⚠️ Memory Summarizer Failed: {str(e)[:100]}")
                return "📝 Step processed" # Fallback an toàn

            # 7. Lưu vào Cache và trả về
            self._summary_cache[cache_key] = summary
            
            # Giới hạn kích thước cache
            if len(self._summary_cache) > 100:
                oldest_keys = list(self._summary_cache.keys())[:50]
                for key in oldest_keys:
                    del self._summary_cache[key]

            return summary

        except Exception as e:
            # Fallback cuối cùng nếu mọi thứ đều hỏng (lỗi ở phần extract message chẳng hạn)
            error_msg = str(e)[:30]
            return f"❓ Step (error: {error_msg}...)"

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any],
    ) -> RunnableConfig:
        """Override put method to add LLM-generated step summary"""
        try:
            # Generate step summary using LLM
            step_summary = self.summarize_step(checkpoint)

            # Create enhanced metadata
            enhanced_metadata = metadata.copy() if metadata else {}
            enhanced_metadata["step_summary"] = step_summary
            enhanced_metadata["step_timestamp"] = checkpoint.get("ts", "unknown")

            # Add step number if available
            messages = checkpoint.get("channel_values", {}).get("messages", [])
            enhanced_metadata["step_number"] = len(messages)

            # Call parent's put method
            return super().put(config, checkpoint, enhanced_metadata, new_versions)

        except Exception as e:
            print(f"❌ Error adding LLM summary: {e}")
            # Fallback to basic metadata
            return super().put(config, checkpoint, metadata, new_versions)
        









# from typing import Dict, Any
# from langgraph.checkpoint.mongodb import MongoDBSaver
# from langchain_core.runnables import RunnableConfig
# from agent.config import get_resilient_llm, key_manager# Import hàm lấy key


# class LLMSummarizingMongoDBSaver(MongoDBSaver):
#     """MongoDB saver with LLM-powered intelligent summarization AND Key Rotation"""

#     def __init__(self, client):
#         # Gọi init của cha, không cần truyền llm vào đây nữa
#         super().__init__(client)
        
#         # Cache để tránh gọi LLM quá nhiều lần cho cùng một nội dung
#         self._summary_cache = {}

#     def summarize_step(self, checkpoint_data: Dict[str, Any]) -> str:
#         """Generate contextual summary using LLM"""
#         try:
#             # 1. Trích xuất thông tin từ checkpoint
#             channel_values = checkpoint_data.get("channel_values", {})
#             messages = channel_values.get("messages", [])

#             if not messages:
#                 return "🔄 Initial state"

#             # Lấy tin nhắn cuối cùng
#             last_message = messages[-1]
#             if not last_message:
#                 return "📭 Empty step"

#             # 2. Phân tích nội dung tin nhắn
#             message_type = (
#                 type(last_message).__name__
#                 if hasattr(last_message, "__class__")
#                 else "unknown"
#             )
#             content = getattr(last_message, "content", "") or ""
#             tool_calls = getattr(last_message, "tool_calls", [])

#             # Xử lý trường hợp message dạng dict (fallback)
#             if isinstance(last_message, dict):
#                 message_type = last_message.get("type", "unknown")
#                 content = last_message.get("content", "")
#                 tool_calls = last_message.get("tool_calls", [])

#             # 3. Kiểm tra Cache
#             # Tạo key đơn giản từ nội dung để tra cứu nhanh
#             cache_key = f"{message_type}:{str(content)[:50]}:{len(tool_calls)}"
#             if cache_key in self._summary_cache:
#                 return self._summary_cache[cache_key]

#             # 4. Chuẩn bị ngữ cảnh cho Prompt
#             context_parts = []
#             if content:
#                 context_parts.append(f"Content: {str(content)[:200]}")
#             if tool_calls:
#                 tool_info = []
#                 for tc in tool_calls[:2]:  # Chỉ lấy 2 tool đầu tiên để đỡ tốn token
#                     tool_name = tc.get("name", "unknown")
#                     tool_args = str(tc.get("args", {}))[:100]
#                     tool_info.append(f"{tool_name}({tool_args})")
#                 context_parts.append(f"Tool calls: {', '.join(tool_info)}")

#             context = "\n".join(context_parts) if context_parts else "No content"

# # LLM prompt for summarization (Spotify Edition)
#             prompt = f"""Summarize this conversation step in 2-5 words with a relevant emoji.

# Message type: {message_type}
# {context}

# Guidelines:
# - Use emojis: 👤 for user, 🤖 for AI, 🔧 for tools, 📊 for data, ✨ for results, 🎵 for music context.
# - Be concise and descriptive.
# - Focus on the action/intent.

# Examples:
# - "👤 Top songs query"
# - "🔧 Schema: top50_usa"
# - "📊 Artist aggregation"
# - "✨ Song list results"
# - "❌ Query validation error"

# Summary:"""



#             max_retries = 100
#             summary = "📝 Processing..."
#             # 6. Gọi LLM với cơ chế Key Rotation & Xử lý lỗi định dạng
#             for attempt in range(max_retries):
#                 try:
#                     # Lấy một LLM mới từ danh sách key
#                     current_llm = get_resilient_llm()
#                     response = current_llm.invoke(prompt)

#                     # XỬ LÝ LỖI LIST: Gemini Flash đôi khi trả về List thay vì String
#                     if isinstance(response.content, list):
#                         summary_text = " ".join([item.get("text", "") for item in response.content if isinstance(item, dict)])
#                     else:
#                         summary_text = str(response.content)

#                     summary = summary_text.strip()[:60]
#                     break
#                 except Exception as e:
#                     # print(f"⚠️ Key lỗi khi tóm tắt, đang thử key khác: {e}")
                    
#                     # # RETRY: Thử lại lần nữa với key tiếp theo
#                     # current_llm = get_resilient_llm()
#                     # response = current_llm.invoke(prompt)
                    
#                     # if isinstance(response.content, list):
#                     #     summary = " ".join([item.get("text", "") for item in response.content if isinstance(item, dict)]).strip()[:60]
#                     # else:
#                     #     summary = str(response.content).strip()[:60]

#                     error_msg = str(e)
#                     # Chỉ retry nếu là lỗi Key/Quota
#                     if any(err in error_msg for err in ["429", "403", "Quota", "API_KEY_INVALID", "Key not found"]):
#                         print(f"⚠️ Memory Summarizer: Key lỗi (Lần {attempt+1}). Đang đổi key...")
#                         print(f" api_key = {current_llm.google_api_key} ")
#                         print(f"🔍 DEBUG: Lỗi chi tiết: {error_msg} " )
#                         continue 
#                     else:
#                         # Lỗi khác thì bỏ qua việc tóm tắt để không làm chậm app
#                         print(f"⚠️ Lỗi tóm tắt bộ nhớ: {e}")
#                         return "📝 Step processed"


#             # 7. Lưu vào Cache và trả về
#             self._summary_cache[cache_key] = summary
            
#             # Giới hạn kích thước cache để không tốn RAM
#             if len(self._summary_cache) > 100:
#                 oldest_keys = list(self._summary_cache.keys())[:50]
#                 for key in oldest_keys:
#                     del self._summary_cache[key]

#             return summary

#         except Exception as e:
#             # Fallback cuối cùng nếu mọi thứ đều hỏng
#             error_msg = str(e)[:30]
#             return f"❓ Step (error: {error_msg}...)"

#     def put(
#         self,
#         config: RunnableConfig,
#         checkpoint: Dict[str, Any],
#         metadata: Dict[str, Any],
#         new_versions: Dict[str, Any],
#     ) -> RunnableConfig:
#         """Override put method to add LLM-generated step summary"""
#         try:
#             # Generate step summary using LLM
#             step_summary = self.summarize_step(checkpoint)

#             # Create enhanced metadata
#             enhanced_metadata = metadata.copy() if metadata else {}
#             enhanced_metadata["step_summary"] = step_summary
#             enhanced_metadata["step_timestamp"] = checkpoint.get("ts", "unknown")

#             # Add step number if available
#             messages = checkpoint.get("channel_values", {}).get("messages", [])
#             enhanced_metadata["step_number"] = len(messages)

#             # Call parent's put method
#             return super().put(config, checkpoint, enhanced_metadata, new_versions)

#         except Exception as e:
#             print(f"❌ Error adding LLM summary: {e}")
#             # Fallback to basic metadata
#             return super().put(config, checkpoint, metadata, new_versions)



