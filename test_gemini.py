import os
import google.generativeai as genai

print("google-generativeai:", genai.__version__)

try:
    import google.ai.generativelanguage as gl
    print("google-ai-generativelanguage:", gl.__version__)
except Exception as e:
    print("Lỗi import google.ai.generativelanguage:", e)

API_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_KEY_HERE"

genai.configure(api_key=API_KEY)

print("\n=== DANH SÁCH MODEL CÓ SẴN ===")
for m in genai.list_models():
    # Chỉ in những model hỗ trợ generateContent
    if "generateContent" in getattr(m, "supported_generation_methods", []):
        print("-", m.name)
