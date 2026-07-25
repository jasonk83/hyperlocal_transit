import streamlit as st
import requests
import pandas as pd

# --- PAGE SETUP & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Transit Dash", page_icon="🚇", layout="centered")

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
    .car-count {
        font-size: 0.9rem;
        color: gray;
        margin-left: 5px;
    }
    .update-text {
        font-size: 0.8rem; 
        color: gray;
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
def get_time_badge(mins):
    """Returns an HTML span with conditional formatting based on numeric minutes."""
    if mins == 10:
        bg_color, text_color = "red", "white"
    elif 11 <= mins <= 15:
        bg_color, text_color = "yellow", "black"
    else: 
        bg_color, text_color = "green", "white"

    return f"<span class='time-badge' style='background-color: {bg_color}; color: {text_color};'>{mins} min</span>"

# --- AUTO-REFRESHING DASHBOARD FRAGMENT ---
@st.fragment(run_every="30s")
def render_dashboard():
    
    # UI Layout: Put the timestamp and the update button side-by-side
    col1, col2 = st.columns([2, 1], vertical_alignment="center")
    with col1:
        # Force the timestamp to calculate in Eastern Time
        current_time = pd.Timestamp.now(tz="America/New_York").strftime('%I:%M:%S %p')
        st.markdown(f"<div class='update-text'>Updated: {current_time}</div>", unsafe_allow_html=True)
    with col2:
        # Tapping this triggers the fragment to re-run instantly
        st.button("↻ Update", use_container_width=True)

    # 1. Train Arrivals
    st.subheader("🔴 Red Line")
    trains = fetch_train_predictions(TRAIN_STATION_CODE)
    
    valid_trains_north = []
    valid_trains_south = []
    
    for t in trains:
        mins_str = str(t.get("Min", ""))
        group = str(t.get("Group", ""))
        
        if mins_str.isdigit():
            mins = int(mins_str)
            if mins >= 10:
                if group == "1":
                    valid_trains_north.append((t, mins))
                elif group == "2":
                    valid_trains_south.append((t, mins))

    # Take exactly 2 from each direction
    display_trains = valid_trains_south[:2] + valid_trains_north[:2]
    
    # Sort them chronologically
    display_trains = sorted(display_trains, key=lambda x: x[1])

    if display_trains:
        for t, mins in display_trains:
            dest = t.get("DestinationName", "Unknown")
            cars = str(t.get("Car", ""))
            
            car_html = f"<span class='car-count'>({cars} cars)</span>" if cars.isdigit() else ""
            
            styled_badge = get_time_badge(mins)
            st.markdown(f"<div class='transit-row'><span>🚆 To {dest} {car_html}</span> {styled_badge}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='transit-row'>No trains outside walking window.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Bus Arrivals
    for label, stop_id in BUS_STOPS.items():
        st.subheader(f"🚌 {label}")
        buses = fetch_bus_predictions(stop_id)
        
        if buses:
            valid_buses = []
            for b in buses:
                mins_str = str(b.get("Minutes", ""))
                if mins_str.isdigit():
                    mins = int(mins_str)
                    
                    if "C61" in label:
                        if mins >= 10:
                            valid_buses.append((b, mins))
                    else:
                        valid_buses.append((b, mins))

            if valid_buses:
                for b, mins in valid_buses[:3]:
                    route = b.get("RouteID", "")
                    dest = b.get("DirectionText", "Unknown")
                    
                    if "C61" in label:
                        styled_badge = get_time_badge(mins)
                    else:
                        styled_badge = f"<span class='time-badge' style='background-color: #444; color: white;'>{mins} min</span>"
                        
                    st.markdown(f"<div class='transit-row'><span><span class='route-badge'>{route}</span> to {dest}</span> {styled_badge}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='transit-row'>No buses outside walking window.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='transit-row'>No upcoming bus predictions.</div>", unsafe_allow_html=True)

render_dashboard()
