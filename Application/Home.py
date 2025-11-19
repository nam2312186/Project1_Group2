import importlib.util
import sys, os
import streamlit as st
import pandas as pd
import pycountry
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
from pymongo import MongoClient

# =============================
# 🧩 Import động module By_Country (render quốc gia khác Mỹ)
# =============================
current_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.join(current_dir, "pages")

spec = importlib.util.spec_from_file_location(
    "by_country", os.path.join(pages_dir, "2_By_Country_2024.py")
)
module = importlib.util.module_from_spec(spec)
sys.modules["by_country"] = module
spec.loader.exec_module(module)
render_country_dashboard = module.render_country_dashboard

# =========================
# ⚙️ 1️⃣ Cấu hình giao diện
# =========================
st.set_page_config(page_title="🌍 Music Analytics Home", layout="wide")
st.title("🎵 Spotify 2024-2025 Dashboard ✨")


# =========================
# 🌐 2️⃣ Kết nối MongoDB
# =========================
uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["spotify_project"]

# =========================
# 📅 3️⃣ Nút chọn năm
# =========================
st.markdown("### 📆 Chọn năm dữ liệu")
year = st.radio("Chọn năm:", [2024, 2025], horizontal=True, label_visibility="collapsed")

# =========================
# 🗺️ 4️⃣ Lấy danh sách quốc gia có dữ liệu tự động
# =========================
def get_available_countries(year: int):
    """Trích từ MongoDB các collection tương ứng với năm"""
    all_collections = db.list_collection_names()
    available = {}

    if year == 2024:
        # Các collection top50_xxx
        for col in all_collections:
            if col.startswith("top50_"):
                # tách tên quốc gia
                country_code = col.replace("top50_", "")
                # chuẩn hoá lại tên (vì dùng cho display)
                display_name = country_code.replace("_", " ").title()
                # map các từ đặc biệt
                special = {
                    "Usa": "United States",
                    "Uk": "United Kingdom",
                    "South Korea": "South Korea",
                }
                display_name = special.get(display_name, display_name)
                available[display_name] = col
    else:
        # Năm 2025 chỉ có top100_usa_2025
        if "top100_usa_2025" in all_collections:
            available["United States"] = "top100_usa_2025"
    return available


available_countries = get_available_countries(year)

# 🌍 Tất cả quốc gia hiển thị (để hover đầy đủ)
all_countries = ["United States", "Argentina", "France","Italy","Japan","Mexico","South Korea","Spain","United Kingdom",
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
    "Congo (Brazzaville)", "Congo (Kinshasa)", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea",
    "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "Gabon",
    "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
    "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland",
    "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Jamaica", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
    "Marshall Islands", "Mauritania", "Mauritius", "Micronesia", "Moldova", "Monaco",
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria",
    "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama",
    "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
    "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia",
    "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
    "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore",
    "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa",
    "South Sudan", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland",
    "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo",
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
    "Uganda", "Ukraine", "United Arab Emirates", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe","Russian Federation"
]

def get_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        custom = {
            "South Korea": "KOR",
            "United States": "USA",
            "United Kingdom": "GBR",
            "Russia": "RUS",
            "Russian Federation": "RUS"
        }
        return custom.get(name, None)

# 🗺️ Tạo DataFrame cho bản đồ
df_map = pd.DataFrame({
    "country": all_countries,
    "iso_code": [get_iso3(c) for c in all_countries],
    "status": ["Has Data" if c in available_countries else "No Data" for c in all_countries]
})

# ======================================
#  Liên kết trang tổng quan toàn cầu
# ======================================
st.markdown("---")
st.page_link("pages/0_Global_Overview.py", label="🌍 Xem Tổng Quan Toàn Cầu")
st.markdown("🎧 Click vào quốc gia có màu xanh Spotify để xem phân tích chi tiết!")


# ======================================
# 5️⃣ Vẽ bản đồ tương tác
# ======================================
fig = go.Figure(
    data=go.Choropleth(
        locations=df_map["iso_code"],
        z=[1 if s == "Has Data" else 0 for s in df_map["status"]],
        text=df_map["country"],
        hoverinfo="text",
        colorscale=[[0, "#9A9494"], [1, "#1DB954"]],
        showscale=False
    )
)

fig.update_geos(
    showcountries=True,
    countrycolor="gray",
    showcoastlines=True,
    coastlinecolor="lightgray"
)
fig.update_layout(
    title=f"🌍 Countries with Spotify Data ({year})",
    margin=dict(l=0, r=0, t=50, b=0),
    height=550
)

selected_point = plotly_events(fig, click_event=True, hover_event=False)

# ======================================
# 6️⃣ Bắt sự kiện click (phân trang)
# ======================================
if selected_point:
    try:
        idx = selected_point[0]["pointNumber"]
        clicked_country = df_map.iloc[idx]["country"]

        if clicked_country == "United States" and year == 2025:
            st.success(" Đang mở dữ liệu Top 100 của năm 2025 ...")
            st.session_state["selected_country"] = clicked_country
            st.session_state["selected_year"] = 2025
            st.switch_page("pages/1_By_Country_2025.py")

        elif clicked_country in available_countries:
            st.session_state["selected_country"] = clicked_country
            st.session_state["selected_year"] = year
            st.success(f"🎵 Đang mở dashboard cho {clicked_country} ({year}) ...")
            st.switch_page("pages/2_By_Country_2024.py")

        else:
            st.warning(f"⚠️ {clicked_country} chưa có dữ liệu cho năm {year}!")
    except Exception as e:
        st.error(f"Lỗi xử lý click: {e}")


# ======================================
# 7️⃣ Nút phản hồi người dùng
# ======================================
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSckKNZyu6UUw7vSK3qvWbQT8cSoSXOi3ev7k6pcURneaUxpLQ/viewform"  # TODO: thay bằng link Google Form thật

st.markdown("---")
st.subheader("💌 Phản hồi về ứng dụng")
st.write("Nếu bạn có góp ý hoặc muốn đánh giá mức độ hài lòng, hãy bấm nút bên dưới:")

# Nếu Streamlit của bạn hỗ trợ link_button (phiên bản mới):
try:
    st.link_button("📝 Gửi phản hồi (Google Form)", FEEDBACK_URL)
except Exception:
    # Fallback dùng markdown nếu phiên bản Streamlit cũ
    st.markdown(f"[📝 Gửi phản hồi (Google Form)]({FEEDBACK_URL})")


st.subheader("😊 🤝 Cảm ơn bạn đã quan tâm đến Dashboard Spotify của chúng tôi! 🎵🌍")