import streamlit as st
import json
import pandas as pd
import os
import itertools

# Must be the first Streamlit command!
st.set_page_config(page_title="Laxra-Bet", layout="wide")

# Inject custom CSS for a frosty effect
st.markdown(
    """
    <style>
    /* Frosty effect for the main container */
    .reportview-container .main .block-container {
        background-color: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 2rem;
    }
    /* Frosty effect for the sidebar */
    .sidebar .sidebar-content {
        background-color: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 1rem;
    }
    /* Frosty effect for DataFrame display */
    .stDataFrame, .stDataTable {
        background-color: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(8px);
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Today Trend")
st.write("Bet Responsibly:")

# Define the path to your JSON file
json_file_path = "data.json"

if not os.path.exists(json_file_path):
    st.error(f"JSON file not found at path: {json_file_path}")
else:
    try:
        # Load JSON data
        with open(json_file_path, "r") as f:
            data = json.load(f)
        
        # Extract the "winning_trends" list if wrapped in a list with a dictionary
        if isinstance(data, list) and len(data) == 1 and "winning_trends" in data[0]:
            data = data[0]["winning_trends"]
        
        # Create a DataFrame from the JSON data
        df = pd.DataFrame(data)
        
        # Create "Trend Team" column by checking which team appears in Trend_Description
        def extract_trend_team(row):
            t1 = row["team_1"]
            t2 = row["team_2"]
            desc = row["trend_description"]
            if t1 in desc:
                return t1
            elif t2 in desc:
                return t2
            else:
                return ""
        df["Trend Team"] = df.apply(extract_trend_team, axis=1)
        
        # Rename columns as requested
        df.rename(columns={
            "team_1": "Home",
            "team_2": "Away",
            "game_date": "Date",
            "game_time": "Time",
            "probability": "Probability",
            "trend_description": "Trend_Description"
        }, inplace=True)
        
        # Convert "Date" from string to a date object
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        
        # Sidebar: Date selector (default to earliest available date)
        default_date = df["Date"].min() if not df.empty else pd.to_datetime("today").date()
        selected_date = st.sidebar.date_input("Select a date", value=default_date)
        
        # Filter DataFrame based on the selected date
        df_filtered = df[df["Date"] == selected_date]
        
        # Main page: display the filtered games table without index
        display_df = df_filtered[["Date", "Time", "Home", "Away", "Trend Team", "Probability", "Trend_Description"]].reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)
        
        # Sidebar: Bet of the day calculation and unified container display
        st.sidebar.markdown("### Bet of the day")
        bet_container = st.sidebar.container()
        valid_combos = []
        
        # Primary approach: Find a valid 3-game combination from games with odds in [1.2, 1.39]
        subset_3 = df_filtered[(df_filtered["Probability"] >= 1.2) & (df_filtered["Probability"] <= 1.39)]
        if len(subset_3) >= 3:
            for combo in itertools.combinations(subset_3.index, 3):
                odds = subset_3.loc[list(combo), "Probability"].tolist()
                product = 1
                for o in odds:
                    product *= o
                # Check if the product is within the desired range
                if product > 1.8 and product <= 2.1:
                    total = sum(odds)
                    valid_combos.append((combo, product, total))
        
        if valid_combos:
            # If we have a valid 3-game combo
            best_combo = min(valid_combos, key=lambda x: x[2])
            combo_indices = best_combo[0]
            bet_df = df_filtered.loc[list(combo_indices)].sort_values(by="Time")
            bet_container.write(f"Combined Odds: {best_combo[1]:.6f}")
            bet_display_df = bet_df[["Time", "Trend Team", "Probability"]].reset_index(drop=True)
            bet_container.dataframe(bet_display_df, use_container_width=True)
        else:
            # Fallback: single game with odds in [1.2, 1.6]
            subset_single = df_filtered[(df_filtered["Probability"] >= 1.2) & (df_filtered["Probability"] <= 1.6)]
            if not subset_single.empty:
                best_single = subset_single.sort_values(by="Probability").iloc[0]
                single_bet_df = pd.DataFrame({
                    "Time": [best_single["Time"]],
                    "Trend Team": [best_single["Trend Team"]],
                    "Probability": [best_single["Probability"]]
                })
                bet_container.write("Single Game Bet:")
                bet_container.dataframe(single_bet_df, use_container_width=True)
            else:
                bet_container.info("No valid Bet of the day found for the selected date.")
        
        # Soccer image
        bet_container.image("paris-2024-olympics-soccer.jpg", use_container_width=True)

        # Social icons with SVG links - replace placeholders with your actual links and filenames
        bet_container.markdown(
            """
            <div style="display: flex; gap: 10px; margin-top: 1rem;">
              <!-- Gmail -->
              <a href="mailto:someone@example.com" target="_blank">
                <img src="gmail.svg" alt="Gmail" style="width:50px;">
              </a>
              <!-- WhatsApp -->
              <a href="https://wa.me/1234567890" target="_blank">
                <img src="whatsapp.svg" alt="WhatsApp" style="width:50px;">
              </a>
              <!-- YouTube -->
              <a href="https://www.youtube.com/@WrestlingWarzone1" target="_blank">
                <img src="youtube.svg" alt="YouTube" style="width:50px;">
              </a>
              <!-- TikTok -->
              <a href="https://www.tiktok.com/@someusername" target="_blank">
                <img src="tiktok.svg" alt="TikTok" style="width:50px;">
              </a>
            </div>
            """,
            unsafe_allow_html=True
        )
            
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
