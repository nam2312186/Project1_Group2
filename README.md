## 💡 Lưu ý về Virtual Environment (venv)

- Thư mục `venv/` chứa môi trường ảo chỉ hoạt động trên chính máy đã tạo ra nó, 
  vì nó lưu đường dẫn tuyệt đối tới Python interpreter.  
- Khi **clone project từ GitHub**, thư mục `venv/` nếu có sẵn thường **không chạy được trên máy khác**.  

👉 Best practice:
1.  Khi clone project, xóa thư mục venv có sẵn 
2. Hãy tạo môi trường ảo mới:
   ```bash
   python -m venv venv
3. Kích hoạt môi trường:

Windows:

venv\Scripts\activate

Linux/macOS:

source venv/bin/activate


4. Cài đặt dependencies:

pip install -r requirements.txt