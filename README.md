## 💡 Lưu ý về Virtual Environment (venv)

- Thư mục `venv/` chứa môi trường ảo chỉ hoạt động trên chính máy đã tạo ra nó, 
  vì nó lưu đường dẫn tuyệt đối tới Python interpreter.  
- Khi **clone project từ GitHub**, thư mục `venv/` nếu có sẵn thường **không chạy được trên máy khác**.  

👉 Best practice:
1.  Khi clone project, xóa thư mục venv nếu có
2. Hãy tạo môi trường ảo mới:
   ```bash
   python -m venv venv
3. Kích hoạt môi trường:

Windows:
```bash
venv\Scripts\activate
```
Linux/macOS:
```bash
source venv/bin/activate
```

4. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```