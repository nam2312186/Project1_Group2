import os
import nbformat
import base64

# Thư mục chứa notebook
root_dir = "analysis"

# Thư mục output
base_out_dir = os.path.join("reports", "figure", "analysis")

# Duyệt toàn bộ notebook
for region, _, files in os.walk(root_dir):
    for file in sorted(files):  # sort để ổn định
        if file.endswith(".ipynb"):
            nb_path = os.path.join(region, file)
            print(f"🔍 Đang xử lý {nb_path}...")

            with open(nb_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)

            # Lấy tên country (EDA_usa.ipynb -> usa)
            base_name = os.path.splitext(file)[0]

            img_index = 0
            for cell in nb.cells:
                if "outputs" in cell:
                    for output in cell["outputs"]:
                        if output.get("data") and "image/png" in output["data"]:
                            img_data = base64.b64decode(output["data"]["image/png"])

                            # Folder theo index (0,1,2,...)
                            folder_name = str(img_index)
                            out_dir = os.path.join(base_out_dir, folder_name)
                            os.makedirs(out_dir, exist_ok=True)

                            # Tên file giữ theo notebook (vd: EDA_usa.png)
                            filename = f"{base_name}.png"
                            out_path = os.path.join(out_dir, filename)

                            with open(out_path, "wb") as img_file:
                                img_file.write(img_data)

                            print(f"   ➜ {filename} → folder {folder_name}")

                            img_index += 1
