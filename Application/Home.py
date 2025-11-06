import streamlit as st
import pandas as pd
import pycountry
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="🌍 Music Analytics Home", layout="wide")
st.title("🌎 Spotify & Billboard Dashboard – Global Overview")
st.markdown("🎧 Click vào quốc gia có màu xanh Spotify để xem phân tích chi tiết!")

# =========================
# 1️⃣ Dữ liệu quốc gia có dashboard
# =========================
available_countries = {
    "United States": "1_United_States",
    "Argentina": "2_Argentina",
    "France": "3_France",
    "Italy": "4_Italy",
    "Japan": "5_Japan",
    "Mexico": "6_Mexico",
    "South Korea": "7_South_Korea",
    "Spain": "8_Spain",
    "United Kingdom": "9_United_Kingdom"
}

def get_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        return None

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

df_map = pd.DataFrame({
    "country": all_countries,
    "iso_code": [get_iso3(c) for c in all_countries],
    "status": ["Has Data" if c in available_countries else "No Data" for c in all_countries]
})

# ======================================
# 2️⃣ Vẽ bản đồ

# ======================================
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

fig = go.Figure(
    data=go.Choropleth(
        locations=df_map["iso_code"],
        z=[1 if s == "Has Data" else 0 for s in df_map["status"]],
        text=df_map["country"],
        hoverinfo="text",
        colorscale=[[0, "#f2f2f2"], [1, "#1DB954"]],
        showscale=False
    )
)

fig.update_geos(showcountries=True, countrycolor="gray", showcoastlines=True, coastlinecolor="lightgray")
fig.update_layout(
    title="🌍 Countries with Spotify/Billboard Data",
    margin=dict(l=0, r=0, t=50, b=0),
    height=550
)

# ======================================
# 3️⃣ Bắt sự kiện click bằng pointNumber
# ======================================
selected_point = plotly_events(fig, click_event=True, hover_event=False)

if selected_point:
    try:
        point_idx = selected_point[0]["pointNumber"]
        clicked_country = df_map.iloc[point_idx]["country"]
        if clicked_country in available_countries:
            st.success(f"🌎 Bạn đã chọn: {clicked_country}")
            st.switch_page(f"pages/{available_countries[clicked_country]}.py")
        else:
            st.warning(f"⚠️ {clicked_country} chưa có dữ liệu!")
    except Exception as e:
        st.error(f"Lỗi xử lý click: {e}")

# ======================================
# 4️⃣ Tổng quan worldwide
# ======================================
from pymongo import MongoClient
# -----------------------------
# 1️⃣ Cấu hình giao diện
# -----------------------------
st.set_page_config(page_title="world Dashboard", layout="wide")
st.title("Music Trends Dashboard – WORLD")
st.caption("Chọn nguồn dữ liệu để xem dashboard tương ứng")

# -----------------------------
# 2️⃣ Kết nối MongoDB Atlas
# -----------------------------
uri = "mongodb+srv://doanbk251:nhom210diem@cluster0.yly7ncp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["spotify_project"]

# -----------------------------
# 3️⃣ Tabs chọn nguồn dữ liệu
# -----------------------------
tab1, tab2 = st.tabs(["📊 album world(2024)", "🎧 Spotify Top 50 world (2024)"])

# ====================================================================
# TAB 1️⃣ — world (2024)
# ====================================================================
with tab1:
    collection_spotify = db["album_status_global_2"]

    @st.cache_data
    def load_spotify_data():
        data = list(collection_spotify.find({}, {"_id": 0}))
        return pd.DataFrame(data)

    df_spotify = load_spotify_data()

    st.header("🎧 Spotify Top 50 (2024)")
    st.write("Hiển thị dữ liệu Spotify 2024 cho Hoa Kỳ (đang cập nhật...)")

    if not df_spotify.empty:
        st.dataframe(df_spotify.head(20))
    else:
        st.warning("Chưa có dữ liệu Spotify Top 50 (2024) trong MongoDB.")

# ====================================================================
# TAB 2️⃣ — Spotify Top 50 world (2024)
# ====================================================================
with tab2:
    collection_spotify = db["top50_world"]

    @st.cache_data
    def load_spotify_data():
        data = list(collection_spotify.find({}, {"_id": 0}))
        return pd.DataFrame(data)

    df_spotify = load_spotify_data()

    st.header("🎧 Spotify Top 50 (2024)")
    st.write("Hiển thị dữ liệu Spotify 2024 cho Hoa Kỳ (đang cập nhật...)")

    if not df_spotify.empty:
        st.dataframe(df_spotify.head(20))
    else:
        st.warning("Chưa có dữ liệu Spotify Top 50 (2024) trong MongoDB.")


