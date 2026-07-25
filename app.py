import streamlit as st
import requests
import pandas as pd

# Page setup
st.set_page_config(page_title="DC Transit Dashboard", page_icon="🚇", layout="centered")

st.title("🚇 Brookland Transit Dashboard")

# Access API key securely from Streamlit secrets
if "wmata" in st.secrets and "api_key" in st.secrets["wmata"]:
    WMATA_API_KEY = st.secrets["wmata"]["api_key"]
else:
    st.error("WMATA API Key not found. Configure `.streamlit/secrets.toml` locally or set secrets on Streamlit Cloud.")
    st.stop()

HEADERS = {"api_key": WMATA_API_KEY}

# --- CONFIGURATION ---
TRAIN_STATION_CODE = "B05"  # Brookland-CUA

# Add future bus lines/stops directly to this dictionary
BUS_STOPS = {
    "C61 (Brookland Bus Bay B)": "1002960",
    "D74 (12th & Jackson St NE)": "1002032"  # Westbound stop
}

# --- API HELPERS ---
def fetch_train_predictions(station_code):
    """Fetch live rail arrivals for a given station code."""
    url = f"https://api.wmata.com/StationPrediction.svc/json/GetPrediction/{station_code}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("Trains", [])
    except requests.exceptions.RequestException:
        pass
    return []

def fetch_bus_predictions(stop_id):
    """Fetch live bus arrivals for a given stop ID."""
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
    st.caption(f"Last updated: {pd.Timestamp.now().strftime('%I:%M:%S %p')}")

    # 1. Train Arrivals
    st.header("🔴 Red Line Arrivals (Brookland-CUA)")
    trains = fetch_train_predictions(TRAIN_STATION_CODE)
    
    if trains:
        df_trains = pd.DataFrame(trains)
        # Filter for key columns
        df_trains = df_trains[["Line", "DestinationName", "Min"]]
        df_trains.columns = ["Line", "Destination", "Arriving In (Min)"]
        st.dataframe(df_trains, use_container_width=True, hide_index=True)
    else:
        st.info("No train prediction data currently available.")

    st.divider()

    # 2. Bus Arrivals
    st.header("🚌 Live Bus Arrivals")
    for label, stop_id in BUS_STOPS.items():
        st.subheader(label)
        buses = fetch_bus_predictions(stop_id)
        
        if buses:
            df_buses = pd.DataFrame(buses)
            df_buses = df_buses[["RouteID", "DirectionText", "Minutes"]]
            df_buses.columns = ["Route", "Direction", "Arriving In (Min)"]
            st.dataframe(df_buses, use_container_width=True, hide_index=True)
        else:
            st.write("No upcoming bus predictions for this stop.")

# Execute dashboard fragment
render_dashboard()
