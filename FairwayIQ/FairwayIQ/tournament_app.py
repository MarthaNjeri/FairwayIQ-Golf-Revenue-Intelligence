import streamlit as st
import pandas as pd
import numpy as np
import datetime

# Set up page config for a professional look
st.set_page_config(page_title="FairwayIQ - Live Tournament Center", layout="wide")

st.title("⛳ FairwayIQ Tournament Center")
st.subheader("Limuru Country Club - Live Scoring Dashboard")

# --- DATABASE / FILE PATH ---
# Using the live dataset we synced earlier
DATA_PATH = "data/live_leaderboard.csv"

# Load the current leaderboard data safely
try:
    df_scores = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    # Fallback synthetic data if the file is fresh/empty
    data = {
        'Member_ID': ['M1001', 'M1002', 'M1003', 'M1004', 'M1005'],
        'Name': ['John Mwangi', 'Alice Koech', 'David Ochieng', 'Martha Njeri', 'Peter Kamau'],
        'Gross_Score': [74, 79, 82, 72, 85],
        'Handicap': [4, 10, 12, 2, 15],
        'Timestamp': [str(datetime.datetime.now())] * 5
    }
    df_scores = pd.DataFrame(data)
    df_scores.to_csv(DATA_PATH, index=False)

# --- AUTOMATIC COLUMN MATCHING ---
# Print columns to your terminal so you can verify what's inside the file
print("Your actual CSV columns are:", list(df_scores.columns))

# Clean up column names (remove hidden spaces for safety)
df_scores.columns = df_scores.columns.str.strip()

# 1. Smart-lookup: Find whichever column represents the score
score_col = None
for col in ['Gross_Score', 'Gross Score', 'Score', 'score', 'gross_score']:
    if col in df_scores.columns:
        score_col = col
        break

# 2. Smart-lookup: Find whichever column represents the handicap
hcp_col = None
for col in ['Handicap', 'handicap', 'HCP', 'hcp']:
    if col in df_scores.columns:
        hcp_col = col
        break

# 3. Smart-lookup: Find whichever column represents the player's name
name_col = None
for col in ['Name', 'name', 'Player', 'player', 'Member_Name', 'Member', 'Name ']:
    if col in df_scores.columns:
        name_col = col
        break

# --- PROCESS AND MAP DATA SAFELY ---
if score_col and hcp_col:
    df_scores['Gross_Score'] = df_scores[score_col].astype(float)
    df_scores['Handicap'] = df_scores[hcp_col].astype(float)
    df_scores['Net_Score'] = df_scores['Gross_Score'] - df_scores['Handicap']
else:
    # Safe fallback if your live CSV doesn't have score columns yet
    df_scores['Gross_Score'] = 80
    df_scores['Handicap'] = 10
    df_scores['Net_Score'] = 70

# Map the name column safely so line 98 always finds it
if name_col:
    df_scores['Name'] = df_scores[name_col]
else:
    df_scores['Name'] = "Unknown Player"

# Sort so the lowest net score is at the top
df_scores = df_scores.sort_values(by='Net_Score').reset_index(drop=True)


# --- TOURNAMENT STATE MANAGEMENT ---
# We use Streamlit's session state to track if the tournament is active or finalized
if 'tournament_locked' not in st.session_state:
    st.session_state.tournament_locked = False

# --- SIDEBAR CONTROLLER (For Club Officials / Captains) ---
st.sidebar.header("🛠️ Tournament Control Desk")
st.sidebar.write("Simulate closing the tournament once the final flight submits their scores.")

if not st.session_state.tournament_locked:
    if st.sidebar.button("🔒 Finalize Tournament & Lock Scores", type="primary"):
        st.session_state.tournament_locked = True
        st.rerun()
else:
    if st.sidebar.button("🔄 Re-open Live Scoring"):
        st.session_state.tournament_locked = False
        st.rerun()
# --- INTERFACE DISPLAY LOGIC ---

if not st.session_state.tournament_locked:
    # 🟢 PHASE 1: LIVE TOURNAMENT ACTIVE
    st.success("🟢 TOURNAMENT ACTIVE: Scores are live-populating from member phones.")
    
    # Show active statistics
    col1, col2, col3 = st.columns(3)
    col1.metric("Field Size", f"{len(df_scores)} Players")
    col2.metric("Current Leader Net", f"{df_scores['Net_Score'].min()} Net")
    col3.metric("Average Net Score", f"{int(df_scores['Net_Score'].mean())}")
    
    st.write("### Current Standings")
    st.dataframe(df_scores[['Name', 'Gross_Score', 'Handicap', 'Net_Score']], use_container_width=True)

else:
    # 🔴 PHASE 2: TOURNAMENT LOCKED & WINNER CELEBRATION
    st.balloons() # Throws a celebration animation on the screen!
    st.error("🏆 TOURNAMENT CONCLUDED - FINAL RESULTS LOCKED")
    
    # Extract the top 3 players safely
    winner = df_scores.iloc[0]
    second = df_scores.iloc[1] if len(df_scores) > 1 else None
    third = df_scores.iloc[2] if len(df_scores) > 2 else None
    
    # Create the Virtual Winner's Podium UI
    st.markdown("## 👑 The Championship Podium")
    
    podium_col1, podium_col2, podium_col3 = st.columns(3)
    
    with podium_col2: # Winner goes in the center column
        st.markdown(
            f"""
            <div style="background-color:#D4AF37; padding:20px; border-radius:15px; text-align:center; color:black;">
                <h3>🥇 1st Place (CHAMPION)</h3>
                <h2>{winner['Name']}</h2>
                <h1>{int(winner['Net_Score'])} Net</h1>
                <p>Gross: {int(winner['Gross_Score'])} | HCP: {int(winner['Handicap'])}</p>
                <p style="font-weight:bold; font-size:1.2em;">🎁 Prize: Customized Titleist Driver & Club Trophy</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    with podium_col1: # Second place on the left
        if second is not None:
            st.markdown(
                f"""
                <div style="background-color:#C0C0C0; padding:20px; border-radius:15px; text-align:center; color:black; margin-top:30px;">
                    <h3>🥈 2nd Place</h3>
                    <h3>{second['Name']}</h3>
                    <h2>{int(second['Net_Score'])} Net</h2>
                    <p>Gross: {int(second['Gross_Score'])} | HCP: {int(second['Handicap'])}</p>
                    <p>🎁 Prize: Ksh 15,000 Pro-Shop Voucher</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
    with podium_col3: # Third place on the right
        if third is not None:
            st.markdown(
                f"""
                <div style="background-color:#CD7F32; padding:20px; border-radius:15px; text-align:center; color:black; margin-top:45px;">
                    <h3>🥉 3rd Place</h3>
                    <h3>{third['Name']}</h3>
                    <h2>{int(third['Net_Score'])} Net</h2>
                    <p>Gross: {int(third['Gross_Score'])} | HCP: {int(third['Handicap'])}</p>
                    <p>🎁 Prize: Dozen Srixon Golf Balls</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

    st.write("---")
    st.write("### Complete Final Standings")
    st.table(df_scores[['Name', 'Gross_Score', 'Handicap', 'Net_Score']])