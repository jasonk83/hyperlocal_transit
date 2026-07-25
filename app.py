import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
# To add more bus lines in the future, just add them to this dictionary.
# Format: "Display Name": "WMATA_Stop_ID"
BUS_STOPS = {
    "C61 (Brookland Bus Bay B)": "1002960",
    "D74 (12th & Jackson St NE)": "1002032" # Westbound stop ID
}

# Brookland-CUA Station Code
TRAIN_STATION_CODE = "B05"

# Setup page config
st.set_page_config(page_title="DC Transit Dashboard", layout="centered")
st.title("🚇 Brookland Transit Dashboard")

# Securely grab the API key from Streamlit secrets
try:
    WMATA_API_KEY = st.secrets["wmata"]["api_key"]
except KeyError:
    st.error("API Key not found! Please set up your `.streamlit/secrets.toml` file.")
    st.stop()

HEADERS = {"api_key": WMATA_API_KEY}

# --- DATA FETCHING FUNCTIONS ---
def get_train_predictions(station_code):
    """Fetch live rail predictions for a specific station."""
    url = f"https://api.wmata.com/StationPrediction.svc/json/GetPrediction/{station_code}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("Trains", [])
    return []

def get_bus_predictions(stop_id):
    """Fetch live bus predictions for a specific stop ID."""
    url = f"https://api.wmata.com/NextBusService.svc/json/jPredictions?StopID={stop_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("Predictions", [])
    return []

# --- AUTO-REFRESHING UI FRAGMENT ---
# This decorator tells Streamlit to run this specific function every 30 seconds
@st.fragment(run_every="30s")
def display_live_transit_data():
    
    st.write(f"*(Last updated: {pd.Timestamp.now().strftime('%I:%M:%S %p')})*")

    # 1. Display Metro Rail Arrivals
    st.header("🔴 Red Line Arrivals (Brookland-CUA)")
    trains = get_train_predictions(TRAIN_STATION_CODE)
    
    if trains:
        # Convert to pandas dataframe for a clean table
        df_trains = pd.DataFrame(trains)
        # Keep only the columns we care about and rename them for the UI
        df_trains = df_trains[['Line', 'Destination', 'Min']]
        df_trains.columns = ["Line", "Destination", "Arriving In (min)"]
        st.dataframe(df_trains, use_container_width=True, hide_index=True)
    else:
        st.info("No train predictions available right now.")

    st.divider()

    # 2. Display Bus Arrivals
    st.header("🚌 Live Bus Arrivals")
    
    # Loop through our configured stops and display each
    for name, stop_id in BUS_STOPS.items():
        st.subheader(name)
        buses = get_bus_predictions(stop_id)
        
        if buses:
            df_buses = pd.DataFrame(buses)
            # RouteID is the bus line (e.g., C61), DirectionText is the destination
            df_buses = df_buses[['RouteID', 'DirectionText', 'Minutes']]
            df_buses.columns = ["Route", "Direction", "Arriving In (min)"]
            st.dataframe(df_buses, use_container_width=True, hide_index=True)
        else:
            st.write("No upcoming buses for this stop.")

# Run the live data function
display_live_transit_data()
