import streamlit as st
import requests
import pandas as pd

# --- PAGE SETUP & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Transit Dash", page_icon="🚇", layout="centered")

# CSS hides menus and sets up the base row styling. 
# We removed the hardcoded badge color because it will be generated dynamically now.
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .transit-row {
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #333;
        padding-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .time-badge {
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 6px;
    }
    .route-badge {
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Access API key securely
if "wmata" in st.secrets and "api_key" in st.secrets["wmata"]:
    WMATA_API_KEY = st.secrets["wmata"]["api_key"]
else:
    st.error("API Key missing.")
    st.stop()

HEADERS = {"api_key": WMATA_API_KEY}

# --- CONFIGURATION ---
TRAIN_STATION_CODE = "B05"

BUS_STOPS = {
    "C61 (Brookland Bay B)": "1002960",
    "D74 (12th & Jackson)": "1002032"
}

# --- API HELPERS ---
def fetch_train_predictions(station_code):
    url = f"https://api.wmata.com/StationPrediction.svc/json/GetPrediction/{station_code}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("Trains", [])
    except requests.exceptions.RequestException:
        pass
    return []

def fetch_bus_predictions(stop_id):
    url = f"https://api.wmata.com/NextBusService.svc/json/jPredictions?StopID={stop_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("Predictions", [])
    except requests.exceptions.RequestException:
        pass
    return []

# --- DYNAMIC STYLING HELPER ---
def get_time_badge(mins_str):
    """Returns an HTML span with conditional formatting based on time."""
    # Handle WMATA's text-based arrivals for trains (ARR, BRD)
    if mins_str in ["ARR", "BRD"]:
        mins = 0
        display_text = mins_str
    else:
        try:
            mins = int(mins_str)
            display_text = f"{mins} min"
        except ValueError:
            # Fallback for unexpected strings (e.g., "DLY" for delayed)
            return f"<span class='time-badge' style='background-color: gray; color: white;'>{mins_str}</span>"

    # Apply conditional colors
    if mins <= 10:
        bg_color, text_color = "red", "white"
    elif 11 <= mins <= 15:
        bg_color, text_color = "yellow", "black"
    else:
        bg_color, text_color = "green", "white"

    return f"<span class='time-badge' style='background-color: {bg_color}; color: {text_color};'>{display_text}</span>"

# --- AUTO-REFRESHING DASHBOARD FRAGMENT ---
@st.fragment(run_every="30s")
def render_dashboard():
    st.markdown(f"<div style='text-align: center; font-size: 0.8rem; color: gray;'>Updated: {pd.Timestamp.now().strftime('%I:%M:%S %p')}</div>", unsafe_allow_html=True)

    # 1. Train Arrivals (Applies conditional formatting)
    st.subheader("🔴 Red Line")
    trains = fetch_train_predictions(TRAIN_STATION_CODE)
    
    if trains:
        for t in trains[:4]:
            dest = t.get("DestinationName", "Unknown")
            mins_str = str(t.get("Min", "---"))
            styled_badge = get_time_badge(mins_str)
            st.markdown(f"<div class='transit-row'><span>🚆 To {dest}</span> {styled_badge}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='transit-row'>No trains currently available.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Bus Arrivals
    for label, stop_id in BUS_STOPS.items():
        st.subheader(f"🚌 {label}")
        buses = fetch_bus_predictions(stop_id)
        
        if buses:
            for b in buses[:3]:
                route = b.get("RouteID", "")
                dest = b.get("DirectionText", "Unknown")
                mins_str = str(b.get("Minutes", "---"))
                
                # Apply conditional formatting ONLY if it is the C61 route
                if "C61" in label:
                    styled_badge = get_time_badge(mins_str)
                else:
                    # Neutral gray format for the D74
                    display_text = f"{mins_str} min" if mins_str.isdigit() else mins_str
                    styled_badge = f"<span class='time-badge' style='background-color: #444; color: white;'>{display_text}</span>"
                    
                st.markdown(f"<div class='transit-row'><span><span class='route-badge'>{route}</span> to {dest}</span> {styled_badge}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='transit-row'>No buses currently available.</div>", unsafe_allow_html=True)

render_dashboard()
