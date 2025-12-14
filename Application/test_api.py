import google.generativeai as genai

# Thay key đang bị lỗi vào đây
genai.configure(api_key='AIzaSyBYex4q5e9JVYwAVyzqSDnd0-EFrXRgpns')

print("Danh sách các model khả dụng:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)