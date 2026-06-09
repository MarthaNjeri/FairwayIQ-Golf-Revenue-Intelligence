import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FairwayIQ Score Entry", page_icon="⛳")

st.title("⛳ FairwayIQ Digital Scorecard & Live Database")
st.write("Welcome to the Limuru Country Club Scoring Portal. Please submit your round details below.")

# --- DATABASE ENGINE (Local Data Lake) ---
DB_FILE = "data/live_leaderboard.csv"
# If the database file doesn't exist yet, create it with headers
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["MemberID", "PlayerName", "Course", "Score", "Competition", "PlayDate"])
    df_init.to_csv(DB_FILE, index=False)

# --- STEP 1: PLAYER INPUT FORM ---
with st.form("scorecard_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        member_id = st.number_input("Enter Member ID:", min_value=1, max_value=9999, step=1)
        player_name = st.text_input("Player Full Name:")
    
    with col2:
        home_club = st.selectbox("Select Club Course:", ["Limuru Country Club", "Karen Country Club", "Muthaiga Golf Club"])
        score = st.number_input("Gross Score Played:", min_value=50, max_value=150, step=1)
        
    competition = st.selectbox("Competition Type:", ["Casual Round", "Club Monthly Mug", "Chairman's Prize", "Member-Guest"])
    submit_button = st.form_submit_button("Submit & Generate Scorecard")

# --- STEP 2: REAL-TIME DATABASE SUBMISSION ---
if submit_button:
    # Build the record block
    new_round = pd.DataFrame([{
        "MemberID": member_id,
        "PlayerName": player_name,
        "Course": home_club,
        "Score": score,
        "Competition": competition,
        "PlayDate": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    }])
    
    # Append the new round row directly into the database file
    new_round.to_csv(DB_FILE, mode='a', header=False, index=False)
    
    st.success(f"🎉 Round successfully logged to the Live Leaderboard Database!")
    st.markdown("---")
    st.subheader("📋 FAIRWAYIQ – SUBMITTED MEMBER SCORECARD")
    
    # Display printable visual card
    with st.container():
        st.write(f"**Player Name:** {player_name} | **Member ID:** {member_id}")
        st.write(f"**Course:** {home_club} | **Date:** {datetime.today().strftime('%d %B %Y')}")
        st.write(f"**Competition:** {competition}")
        
        st.markdown("### **Performance Summary**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Gross Score", f"{score}")
        c2.metric("Course Par", "72")
        
        if score <= 72:
            c3.metric("Status", "Under/At Par 👑")
        elif score <= 85:
            c3.metric("Status", "Above Average 👍")
        else:
            c3.metric("Status", "Action Needed 📈")
            
        st.caption("System Status: Database Synced Connected")

# --- STEP 3: LIVE CLUB LEADERBOARD VIEW ---
st.markdown("---")
st.subheader("🏆 Live Club Field Leaderboard")
st.write("This table reads dynamically from the backend database server.")

# Load and show current submissions sorted by lowest score
df_leaderboard = pd.read_csv(DB_FILE)
if not df_leaderboard.empty:
    st.dataframe(df_leaderboard.sort_values(by="Score", ascending=True), use_container_width=True)
else:
    st.info("No rounds submitted today yet. Be the first to post a score!")