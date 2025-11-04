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
    "Japan": "2_Japan",
    "France": "3_France",
    "South Korea": "4_South_Korea",
    "World": "5_World"
}

def get_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        return None

all_countries = ["United States", "Japan", "France", "South Korea", "World",
                 "Brazil", "Germany", "China", "India", "Canada"]

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
