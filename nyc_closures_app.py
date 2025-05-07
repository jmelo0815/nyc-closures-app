
# paste your Streamlit code here below this line

import streamlit as st
import pandas as pd
import requests
import folium
from folium import Popup
from streamlit_folium import st_folium
from datetime import datetime

# Set up the page configuration
st.set_page_config(page_title="NYC Street Closures Map", layout="wide")
st.title("NYC Street Closures Due to Construction")

# Fetch live data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_closure_data():
    url = 'https://data.cityofnewyork.us/resource/i6b5-j7bu.json?$limit=5000'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    df = df[df['the_geom'].notna()]  # Drop rows with missing geometry
    df['work_start_date'] = pd.to_datetime(df['work_start_date'], errors='coerce')
    df['work_end_date'] = pd.to_datetime(df['work_end_date'], errors='coerce')
    return df

df = fetch_closure_data()

# Extract line segments from GeoJSON
@st.cache_data
def extract_lines(geom):
    try:
        return [[(lat, lon) for lon, lat in line] for line in geom['coordinates']]
    except Exception:
        return []

df['lines'] = df['the_geom'].apply(extract_lines)

# Create map centered on NYC
nyc_center = [40.7128, -74.0060]
fmap = folium.Map(location=nyc_center, zoom_start=12)

# Add closures to the map
for _, row in df.iterrows():
    popup_html = f"""
    <b>Street:</b> {row.get('onstreetname', 'N/A')}<br>
    <b>From:</b> {row.get('fromstreetname', 'N/A')}<br>
    <b>To:</b> {row.get('tostreetname', 'N/A')}<br>
    <b>Purpose:</b> {row.get('purpose', 'N/A')}<br>
    <b>Start:</b> {row.get('work_start_date', '')}<br>
    <b>End:</b> {row.get('work_end_date', '')}<br>
    <b>Segment ID:</b> {row.get('segmentid', 'N/A')}<br>
    <b>Unique ID:</b> {row.get('uniqueid', 'N/A')}
    """
    for segment in row['lines']:
        folium.PolyLine(
            locations=segment,
            color='red',
            weight=3,
            popup=Popup(popup_html, max_width=300),
            tooltip=row.get('onstreetname', 'Street Closure')
        ).add_to(fmap)

# Display map in Streamlit
st_folium(fmap, width=1300, height=650)
