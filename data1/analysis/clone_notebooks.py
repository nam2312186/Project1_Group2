import nbformat
import os

# Template gốc (đặt trong đúng folder region, vd: analysis/europe/EDA_france.ipynb)
template_file = "analysis/europe/EDA_france.ipynb"

# Danh sách quốc gia cần clone
countries = [
     "usa", "italy", "spain", "uk", "japan", "south_korea", "argentina", "world" , "mexico"
]

# Lấy region từ đường dẫn template (analysis/<region>/EDA_xxx.ipynb)
region = os.path.basename(os.path.dirname(template_file))

# Tạo thư mục analysis nếu chưa có
os.makedirs("analysis", exist_ok=True)

# Đọc notebook gốc
with open(template_file, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

# Clone cho từng quốc gia
for country in countries:
    nb_copy = nbformat.from_dict(nb)
    
    # Thay thế tên trong cell
    for cell in nb_copy.cells:
        if cell.cell_type in ["markdown", "code"]:
            cell.source = cell.source.replace("France", country.capitalize())
            cell.source = cell.source.replace("france", country)  # lowercase
    
    # Nếu là "world" thì cho vào analysis/world/
    target_region = "world" if country == "world" else region
    out_dir = os.path.join("analysis", target_region)
    os.makedirs(out_dir, exist_ok=True)
    
    out_file = os.path.join(out_dir, f"EDA_{country}.ipynb")
    with open(out_file, "w", encoding="utf-8") as f:
        nbformat.write(nb_copy, f)
    
    print(f" Created {out_file}")
