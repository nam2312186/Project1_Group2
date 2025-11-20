🎯 Mục tiêu:

Sau khi hoàn thành, bạn chỉ cần mở file .tex trong VS Code → nhấn Ctrl + Alt + B → ra ngay file .pdf.

⚙️ PHẦN 1: CÀI MIKTEX
🪜 Bước 1. Tải và cài MiKTeX

Truy cập: https://miktex.org/download

Tải bản Windows Installer (64-bit)

Cài đặt:

Install for: Only for me

Preferred paper: A4

Install missing packages on-the-fly: Yes

Sau khi cài, mở MiKTeX Console → vào tab Updates → nhấn Check for updates → Update now

🪜 Bước 2. Kiểm tra MiKTeX hoạt động

Mở Command Prompt (cmd) và chạy:

pdflatex --version
latexmk --version


Nếu thấy hiện phiên bản (giống như bạn có rồi), thì MiKTeX đã OK ✅
Ví dụ:

MiKTeX-pdfTeX 4.21 (MiKTeX 25.4)
Latexmk, John Collins, Version 4.87

🪜 Bước 3. Cài Strawberry Perl (bắt buộc cho latexmk)

Tải từ: https://strawberryperl.com

Cài bình thường (đường dẫn mặc định)

Sau khi cài, kiểm tra trong CMD:

perl --version


→ Nếu có kết quả là OK.

🪜 Bước 4. Kiểm tra biến PATH

Đảm bảo đường dẫn này nằm trong PATH:

C:\Users\<tên_user>\AppData\Local\Programs\MiKTeX\miktex\bin\x64


Nếu chưa có → thêm thủ công:

Mở Environment Variables → System variables → Path → Edit → New → dán đường dẫn trên.

Sau đó đóng và mở lại VS Code.

💻 PHẦN 2: CÀI ĐẶT TRÊN VS CODE
🪜 Bước 5. Cài extension LaTeX

Mở VS Code → vào Extensions (Ctrl + Shift + X) → tìm:

LaTeX Workshop


Cài extension có biểu tượng hình chữ “TeX” (của James Yu).

🪜 Bước 6. Tạo project thử nghiệm

Tạo thư mục mới (không dấu):

D:\LatexProjects\hello-latex\


Trong đó, tạo file mới main.tex với nội dung:

\documentclass[a4paper,12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[vietnam]{babel}

\begin{document}
Xin chào thế giới!  
Đây là thử nghiệm tiếng Việt với LaTeX trên VS Code.
\end{document}

🪜 Bước 7. Biên dịch thử

Trong VS Code:

Mở main.tex

Nhấn Ctrl + Alt + B (hoặc nhấn vào nút “▶ Build LaTeX project” trên thanh bên trái)

Sau vài giây → sẽ thấy file main.pdf được tạo ra.

Nếu không thấy, thử chạy thủ công trong terminal:

pdflatex main.tex

✨ PHẦN 3: NÂNG CẤP TRẢI NGHIỆM
🔹 Dùng XeLaTeX để hỗ trợ font Unicode (nên dùng nếu bạn gõ tiếng Việt nhiều)

Vào VS Code → Settings (Ctrl + ,) → gõ tìm:

latex-workshop.latex.tools


Thêm vào (hoặc mở settings.json) nội dung:

"latex-workshop.latex.tools": [
  {
    "name": "xelatex",
    "command": "xelatex",
    "args": [
      "-synctex=1",
      "-interaction=nonstopmode",
      "%DOCFILE%"
    ]
  }
],
"latex-workshop.latex.recipes": [
  {
    "name": "XeLaTeX",
    "tools": ["xelatex"]
  }
],
"latex-workshop.view.pdf.viewer": "tab"


Sau đó, trong main.tex, đổi sang:

\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\setmainfont{Times New Roman}
\usepackage[vietnamese]{babel}

\begin{document}
Xin chào, đây là văn bản tiếng Việt với XeLaTeX 😄
\end{document}


Nhấn lại Ctrl + Alt + B → ra PDF chuẩn, đẹp, không lỗi dấu ✅

🎁 Kết quả cuối cùng:

Sau khi hoàn tất:

Biên dịch được .tex trên VS Code bằng 1 phím (Ctrl + Alt + B)

Xem PDF trực tiếp trong VS Code (hoặc ngoài)

Gõ tiếng Việt, ký tự đặc biệt thoải mái (nếu dùng XeLaTeX)

Tự động build lại khi lưu file .tex
🎯 Mục tiêu:

Sau khi hoàn thành, bạn chỉ cần mở file .tex trong VS Code → nhấn Ctrl + Alt + B → ra ngay file .pdf.

⚙️ PHẦN 1: CÀI MIKTEX
🪜 Bước 1. Tải và cài MiKTeX

Truy cập: https://miktex.org/download

Tải bản Windows Installer (64-bit)

Cài đặt:

Install for: Only for me

Preferred paper: A4

Install missing packages on-the-fly: Yes

Sau khi cài, mở MiKTeX Console → vào tab Updates → nhấn Check for updates → Update now

🪜 Bước 2. Kiểm tra MiKTeX hoạt động

Mở Command Prompt (cmd) và chạy:

pdflatex --version
latexmk --version


Nếu thấy hiện phiên bản (giống như bạn có rồi), thì MiKTeX đã OK ✅
Ví dụ:

MiKTeX-pdfTeX 4.21 (MiKTeX 25.4)
Latexmk, John Collins, Version 4.87

🪜 Bước 3. Cài Strawberry Perl (bắt buộc cho latexmk)

Tải từ: https://strawberryperl.com

Cài bình thường (đường dẫn mặc định)

Sau khi cài, kiểm tra trong CMD:

perl --version


→ Nếu có kết quả là OK.

🪜 Bước 4. Kiểm tra biến PATH

Đảm bảo đường dẫn này nằm trong PATH:

C:\Users\<tên_user>\AppData\Local\Programs\MiKTeX\miktex\bin\x64


Nếu chưa có → thêm thủ công:

Mở Environment Variables → System variables → Path → Edit → New → dán đường dẫn trên.

Sau đó đóng và mở lại VS Code.

💻 PHẦN 2: CÀI ĐẶT TRÊN VS CODE
🪜 Bước 5. Cài extension LaTeX

Mở VS Code → vào Extensions (Ctrl + Shift + X) → tìm:

LaTeX Workshop


Cài extension có biểu tượng hình chữ “TeX” (của James Yu).

🪜 Bước 6. Tạo project thử nghiệm

Tạo thư mục mới (không dấu):

D:\LatexProjects\hello-latex\


Trong đó, tạo file mới main.tex với nội dung:

\documentclass[a4paper,12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[vietnam]{babel}

\begin{document}
Xin chào thế giới!  
Đây là thử nghiệm tiếng Việt với LaTeX trên VS Code.
\end{document}

🪜 Bước 7. Biên dịch thử

Trong VS Code:

Mở main.tex

Nhấn Ctrl + Alt + B (hoặc nhấn vào nút “▶ Build LaTeX project” trên thanh bên trái)

Sau vài giây → sẽ thấy file main.pdf được tạo ra.

Nếu không thấy, thử chạy thủ công trong terminal:

pdflatex main.tex

✨ PHẦN 3: NÂNG CẤP TRẢI NGHIỆM
🔹 Dùng XeLaTeX để hỗ trợ font Unicode (nên dùng nếu bạn gõ tiếng Việt nhiều)

Vào VS Code → Settings (Ctrl + ,) → gõ tìm:

latex-workshop.latex.tools


Thêm vào (hoặc mở settings.json) nội dung:

"latex-workshop.latex.tools": [
  {
    "name": "xelatex",
    "command": "xelatex",
    "args": [
      "-synctex=1",
      "-interaction=nonstopmode",
      "%DOCFILE%"
    ]
  }
],
"latex-workshop.latex.recipes": [
  {
    "name": "XeLaTeX",
    "tools": ["xelatex"]
  }
],
"latex-workshop.view.pdf.viewer": "tab"


Sau đó, trong main.tex, đổi sang:

\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\setmainfont{Times New Roman}
\usepackage[vietnamese]{babel}

\begin{document}
Xin chào, đây là văn bản tiếng Việt với XeLaTeX 😄
\end{document}


Nhấn lại Ctrl + Alt + B → ra PDF chuẩn, đẹp, không lỗi dấu ✅

🎁 Kết quả cuối cùng:

Sau khi hoàn tất:

Biên dịch được .tex trên VS Code bằng 1 phím (Ctrl + Alt + B)

Xem PDF trực tiếp trong VS Code (hoặc ngoài)

Gõ tiếng Việt, ký tự đặc biệt thoải mái (nếu dùng XeLaTeX)

Tự động build lại khi lưu file .tex
