import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FairwayIQ Score Entry", page_icon="⛳", layout="wide")

st.title("⛳ FairwayIQ Digital Scorecard & Live Database")
st.write("Welcome to the Limuru Country Club Scoring Portal. Please submit your round details below.")

# --- DATABASE ENGINE (Local Data Lake) ---
DB_FILE = "data/live_leaderboard.csv"
# Ensure data folder exists
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["MemberID", "PlayerName", "Course", "Score", "Competition", "PlayDate"])
    df_init.to_csv(DB_FILE, index=False)

# --- IDENTITY STATE ENGINE ---
if 'authorized' not in st.session_state:
    st.session_state.authorized = False
if 'auth_type' not in st.session_state:
    st.session_state.auth_type = None
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'player_id' not in st.session_state:
    st.session_state.player_id = 1
if 'home_club' not in st.session_state:
    st.session_state.home_club = "Limuru Country Club"

# --- PHASE 1: THE TOURNAMENT GATEKEEPER ---
if not st.session_state.authorized:
    st.markdown("---")
    st.subheader("🔒 Tournament Gate Check-in")
    st.write("Please select your registration type as designated at the entrance gate to unlock your portal view.")
    
    player_type = st.radio(
        "Select Registration Type:", 
        ["Club Member", "Visiting Player", "Sponsor / Guest (Non-Playing)", "Club Management / Admin"],
        horizontal=True
    )
    
    # 1. CLUB MEMBER LOGIC
    if player_type == "Club Member":
        input_id = st.number_input("Enter your Club Member ID:", min_value=1, max_value=9999, step=1)
        input_name = st.text_input("Enter Registered Full Name:")
        
        if st.button("Verify & Unlock Scorecard", type="primary"):
            if input_name.strip():
                st.session_state.authorized = True
                st.session_state.auth_type = "Member"
                st.session_state.player_id = input_id
                st.session_state.player_name = input_name
                st.session_state.home_club = "Limuru Country Club"
                st.rerun()
            else:
                st.error("Please enter your full name to verify membership profile.")
                
    # 2. VISITING PLAYER LOGIC
    elif player_type == "Visiting Player":
        input_name = st.text_input("Visitor Full Name:")
        selected_club = st.selectbox("Select Your Home Club:", ["Muthaiga Golf Club", "Karen Country Club", "Sigona Golf Club", "Royal Nairobi Golf Club"])
        visitor_hcp = st.number_input("Official Handicap Index:", min_value=0, max_value=54, step=1)
        
        if st.button("Register Guest Competitor", type="primary"):
            if input_name.strip():
                st.session_state.authorized = True
                st.session_state.auth_type = "Visitor"
                st.session_state.player_id = 9000 + visitor_hcp
                st.session_state.player_name = f"{input_name} ({selected_club})"
                st.session_state.home_club = selected_club
                st.rerun()
            else:
                st.error("Please enter your name to register as a visiting competitor.")
                
    # 3. SPONSOR / CORPORATE GUEST LOGIC
    elif player_type == "Sponsor / Guest (Non-Playing)":
        st.info("👋 Welcome to the NCBA Tournament Event! Scorecard access is exclusively restricted to playing competitors. Please join us at the club lounge layout to view the real-time leaderboard displays!")

    # 4. EXECUTIVE CLUB MANAGEMENT GATEWAY
    elif player_type == "Club Management / Admin":
        st.subheader("🔑 Executive Portal Verification")
        admin_pin = st.text_input("Enter Management Credentials / PIN:", type="password")
        
        if st.button("Authenticate Admin Console", type="primary"):
            if admin_pin == "1234": # Change this to your preferred pass-code
                st.session_state.authorized = True
                st.session_state.auth_type = "Admin"
                st.session_state.player_id = 0
                st.session_state.player_name = "System Administrator"
                st.session_state.home_club = "HQ Operations"
                st.rerun()
            else:
                st.error("❌ Unauthorized Pin Allocation. Management access blocked.")

# --- PHASE 2: INTERFACE ROUTING BASED ON ROLE ---
else:
    st.markdown("---")
    st.success(f"🔓 **Verified Access Granted ({st.session_state.auth_type}):** Welcome, {st.session_state.player_name}")
    
    if st.button("🔄 Logout / Switch Player Accounts"):
        st.session_state.authorized = False
        st.session_state.auth_type = None
        st.rerun()

    # ROUTE A: IF LOGGED IN USER IS MANAGEMENT, RENDER POWER BI BI ENGINE ONLY
    if st.session_state.auth_type == "Admin":
        st.markdown("---")
        st.header("📊 FairwayIQ Executive Revenue & Churn Dashboard")
        st.caption("🔒 Secured Executive Level View | Authorized Personnel Only")
        
        power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiYzMzYjA2ODEtYWUzNy00ZTYyLWI3MjMtZTM0Y2QzOWVhZWIwIiwidCI6ImNjZWM4MmJhLTA1OTctNDRjNy1hODM4LTEzNjIwY2MxZGJlYiJ9"
        st.components.v1.iframe(power_bi_url, height=700, scrolling=True)

    # ROUTE B: IF LOGGED IN USER IS A PLAYER, RENDER STANDARD PLAYER SCORECARD ENTRY
    else:
        with st.form("scorecard_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                member_id = st.number_input("Member ID / Visitor Code:", value=st.session_state.player_id, disabled=True)
                player_name = st.text_input("Player Full Name:", value=st.session_state.player_name, disabled=True)
            
            with col2:
                home_club = st.text_input("Playing Course / Home Club:", value=st.session_state.home_club, disabled=True)
                score = st.number_input("Gross Score Played:", min_value=50, max_value=150, step=1)
                
            competition = st.selectbox("Competition Type:", ["NCBA Golf Series", "Casual Round", "Club Monthly Mug", "Chairman's Prize", "Member-Guest"])
            submit_button = st.form_submit_button("Submit & Generate Scorecard")

        if submit_button:
            new_round = pd.DataFrame([{
                "MemberID": member_id,
                "PlayerName": player_name,
                "Course": home_club,
                "Score": score,
                "Competition": competition,
                "PlayDate": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            new_round.to_csv(DB_FILE, mode='a', header=False, index=False)
            
            st.success(f"🎉 Round successfully logged to the Live Leaderboard Database!")
            st.markdown("---")
            st.subheader("📋 FAIRWAYIQ – SUBMITTED MEMBER SCORECARD")
            
            with st.container():
                st.write(f"**Player Name:** {player_name} | **ID Code:** {member_id}")
                st.write(f"**Course/Club:** {home_club} | **Date:** {datetime.today().strftime('%d %B %Y')}")
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

# --- PHASE 3: LIVE CLUB LEADERBOARD VIEW (VISIBLE TO AUTHORIZED PLAYERS & MANAGEMENT) ---
if st.session_state.authorized:
    st.markdown("---")
    st.subheader("🏆 Live Club Field Leaderboard")
    st.write("This table reads dynamically from the backend database server.")

    if os.path.exists(DB_FILE):
        df_leaderboard = pd.read_csv(DB_FILE)
        if not df_leaderboard.empty:
            st.dataframe(df_leaderboard.sort_values(by="Score", ascending=True), use_container_width=True)
        else:
            st.info("No rounds submitted today yet. Be the first to post a score!")
    else:
        st.info("No rounds submitted today yet. Be the first to post a score!")