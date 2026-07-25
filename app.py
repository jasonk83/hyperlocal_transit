import streamlit as st
import requests
import pandas as pd

# --- PAGE SETUP & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Transit Dash", page_icon="🚇", layout="centered")

# This custom CSS hides the Streamlit menus, header, and footer to maximize screen space.
# It also creates custom, large-text rows so it is readable from a distance on a phone screen.
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
    }
    .time-badge {
        font-weight: bold;
        color: #ff4b4b; /* Streamlit Red */
        float: right;
    }
    .route-badge {
        font-weight: bold;
        color: #1f77b4; /* Nice blue for bus routes */
    }
    </style>
""", unsafe_allow_html=True)

# Access API key securely from Streamlit secrets
if "wmata" in st.secrets and "api_key" in st.secrets["wmata"]:
    WMATA_API_KEY = st.secrets["wmata"]["api_key"]
else:
    st.error("API Key missing.")
    st.stop()

HEADERS = {"api_key": WMATA_API_KEY}

# --- CONFIGURATION ---
TRAIN_STATION_CODE = "B05"  # Brookland-CUA

# Abbreviated names for the phone screen
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

# --- AUTO-REFRESHING DASHBOARD FRAGMENT ---
@st.fragment(run_every="30s")
def render_dashboard():
    # Small timestamp at the top so you know the screen isn't frozen
    st.markdown(f"<div style='text-align: center; font-size: 0.8rem; color: gray;'>Updated: {pd.Timestamp.now().strftime('%I:%M:%S %p')}</div>", unsafe_allow_html=True)

    # 1. Train Arrivals
    st.subheader("🔴 Red Line")
    trains = fetch_train_predictions(TRAIN_STATION_CODE)
    
    if trains:
        # Limit to the next 4 trains to prevent vertical scrolling on small screens
        for t in trains[:4]:
            dest = t.get("DestinationName", "Unknown")
            mins = t.get("Min", "---")
            if mins.isdigit():
                mins = f"{mins} min"
            st.markdown(f"<div class='transit-row'>🚆 To {dest}: <span class='time-badge'>{mins}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='transit-row'>No trains currently available.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True) # Adds a little spacing

    # 2. Bus Arrivals
    for label, stop_id in BUS_STOPS.items():
        st.subheader(f"🚌 {label}")
        buses = fetch_bus_predictions(stop_id)
        
        if buses:
            # Limit to the next 3 buses per stop
            for b in buses[:3]:
                route = b.get("RouteID", "")
                dest = b.get("DirectionText", "Unknown")
                mins = str(b.get("Minutes", "---")) # Convert integer to string first
                if mins.isdigit():
                    mins = f"{mins} min"
                st.markdown(f"<div class='transit-row'><span class='route-badge'>{route}</span> to {dest}: <span class='time-badge'>{mins}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='transit-row'>No buses currently available.</div>", unsafe_allow_html=True)

# Execute dashboard fragment
render_dashboard()
