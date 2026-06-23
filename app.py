import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. CONFIGURE WORKSPACE
st.set_page_config(page_title="FairwayIQ Master Hub", page_icon="⛳", layout="wide")

# --- DATABASE LOGIC ENGINE ---
DB_FILE = "data/live_leaderboard.csv"
POS_FILE = "data/pos_transactions.csv"
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

# Course Data
LIMURU_PARS = {
    1: 4, 2: 4, 3: 3, 4: 5, 5: 4, 6: 4, 7: 3, 8: 4, 9: 5,
    10: 4, 11: 4, 12: 3, 13: 5, 14: 4, 15: 4, 16: 3, 17: 4, 18: 5
}
TOTAL_COURSE_PAR = sum(LIMURU_PARS.values())

# --- IDENTITY STATE ENGINE ---
if 'authorized' not in st.session_state:
    st.session_state.authorized = False
if 'auth_type' not in st.session_state:
    st.session_state.auth_type = None
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'player_id' not in st.session_state:
    st.session_state.player_id = 1
if 'player_hcp' not in st.session_state:
    st.session_state.player_hcp = 10
if 'home_club' not in st.session_state:
    st.session_state.home_club = "Limuru Country Club"
if 'competition' not in st.session_state:
    st.session_state.competition = "Casual Round"
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1
if 'hole_scores' not in st.session_state:
    st.session_state.hole_scores = {h: LIMURU_PARS[h] for h in range(1, 19)}

# --- MASTER NAVIGATION ---
st.sidebar.title("🏁 FairwayIQ Workspace")
app_mode = st.sidebar.selectbox(
    "Select Interface Console:",
    ["🏌️ Player Scorecard Portal", "🍔 Clubhouse F&B Terminal", "🏆 Tournament Leaderboard Monitor"]
)
st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# 🏌️ MODULE 1: PLAYER SCORECARD PORTAL
# -----------------------------------------------------------------------------
if app_mode == "🏌️ Player Scorecard Portal":
    st.title("⛳ FairwayIQ Digital Scorecard")
    
    if not st.session_state.authorized:
        st.subheader("🔒 Tournament Gate Check-in")
        player_type = st.radio("Select Registration Type:", ["Club Member", "Visiting Player", "Club Management / Admin"], horizontal=True)
        
        if player_type == "Club Member":
            input_id = st.number_input("Enter your Club Member ID:", min_value=1, max_value=9999, step=1)
            input_name = st.text_input("Enter Registered Full Name:")
            input_hcp = st.number_input("Verified Club Handicap:", min_value=0, max_value=54, value=12, step=1)
            comp_type = st.selectbox("Select Active Competition:", ["NCBA Golf Series", "Casual Round", "Club Monthly Mug", "Chairman's Prize"])
            
            if st.button("Verify & Unlock Scorecard", type="primary"):
                if input_name.strip():
                    st.session_state.authorized = True
                    st.session_state.auth_type = "Member"
                    st.session_state.player_id = input_id
                    st.session_state.player_name = input_name
                    st.session_state.player_hcp = input_hcp
                    st.session_state.competition = comp_type
                    st.rerun()
                else:
                    st.error("Please enter your name.")
                    
        elif player_type == "Club Management / Admin":
            admin_pin = st.text_input("Enter Admin PIN:", type="password")
            if st.button("Authenticate Admin Console"):
                if admin_pin == "1234":
                    st.session_state.authorized = True
                    st.session_state.auth_type = "Admin"
                    st.rerun()
                else:
                    st.error("Invalid Pin.")
    else:
        # LOGGED IN SCORECARD ENTRY INTERFACE
        if st.session_state.auth_type == "Admin":
            st.header("📊 Power BI Executive Panel")
            power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiYzMzYjA2ODEtYWUzNy00ZTYyLWI3MjMtZTM0Y2QzOWVhZWIwIiwidCI6ImNjZWM4MmJhLTA1OTctNDRjNy1hODM4LTEzNjIwY2MxZGJlYiJ9"
            st.components.v1.iframe(power_bi_url, height=700, scrolling=True)
        else:
            current_h = st.session_state.current_hole
            running_gross = sum(st.session_state.hole_scores.values())
            
            st.success(f"Logged in as: {st.session_state.player_name}")
            
            # Action button to reset player account
            if st.button("🔄 Switch Player Accounts"):
                st.session_state.authorized = False
                st.session_state.current_hole = 1
                st.session_state.hole_scores = {h: LIMURU_PARS[h] for h in range(1, 19)}
                st.rerun()

            st.markdown("---")
            
            # HOLE STEPPER
            if current_h <= 18:
                st.subheader(f"🏌️ Active Hole Input: Hole {current_h} (Par {LIMURU_PARS[current_h]})")
                
                hcp_strokes = st.number_input(
                    "Input Gross Strokes:", min_value=1, max_value=15, 
                    value=int(st.session_state.hole_scores[current_h]), step=1, key=f"hub_h_{current_h}"
                )
                st.session_state.hole_scores[current_h] = hcp_strokes
                
                col_nav1, col_nav2 = st.columns(2)
                with col_nav1:
                    if current_h > 1:
                        if st.button("⬅️ Previous Hole", key="prev_btn"):
                            st.session_state.current_hole -= 1
                            st.rerun()
                with col_nav2:
                    if current_h < 18:
                        if st.button("Save & Advance ➡️", key="next_btn"):
                            st.session_state.current_hole += 1
                            st.rerun()
                    else:
                        if st.button("🏁 Review Summary", type="primary", key="finish_btn"):
                            st.session_state.current_hole = 19
                            st.rerun()
            else:
                # 18th hole completed view
                st.subheader("📋 Final Scorecard Submission Form")
                st.metric("Total Gross Score", f"{running_gross} Strokes")
                
                marker_verification = st.selectbox("Select Flight Marker:", ["Choose marker...", "John Mwangi", "Alice Koech", "Martha Njeri"])
                
                if st.button("🚀 Secure Submit to Leaderboard", type="primary"):
                    if marker_verification == "Choose marker...":
                        st.error("Marker required.")
                    else:
                        new_row = pd.DataFrame([{
                            "MemberID": st.session_state.player_id, "PlayerName": st.session_state.player_name,
                            "Course": st.session_state.home_club, "Handicap": st.session_state.player_hcp,
                            "Score": running_gross, "Competition": st.session_state.competition,
                            "MarkerVerification": marker_verification, "PlayDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }])
                        new_row.to_csv(DB_FILE, mode='a', header=False, index=False)
                        st.success("Round logged! Resetting scorecard tracker...")
                        st.session_state.current_hole = 1
                        st.session_state.hole_scores = {h: LIMURU_PARS[h] for h in range(1, 19)}
                        st.rerun()

# -----------------------------------------------------------------------------
# 🍔 MODULE 2: CLUBHOUSE F&B TERMINAL
# -----------------------------------------------------------------------------
elif app_mode == "🍔 Clubhouse F&B Terminal":
    st.title("🍔 FairwayIQ Clubhouse F&B Terminal")
    
    if not os.path.exists(POS_FILE):
        pd.DataFrame(columns=["TransactionID", "MemberID", "PlayerName", "PointOfSale", "AmountKES", "Timestamp"]).to_csv(POS_FILE, index=False)
        
    st.subheader("🛒 Log New Purchase")
    if os.path.exists(DB_FILE):
        df_players = pd.read_csv(DB_FILE)
        if not df_players.empty:
            player_list = [f"{row['PlayerName']} ({row['MemberID']})" for _, row in df_players.iterrows()]
            selected_player = st.selectbox("Select Player at Register:", player_list, key="fb_player_select")
            
            pos_location = st.selectbox("Point of Sale:", ["Main Bar", "Halfway House", "Restaurant"], key="fb_pos_loc")
            spend_amount = st.number_input("Amount (KES):", min_value=10, max_value=50000, value=1000, key="fb_spend_amt")
            
            if st.button("Confirm Folio Sale", type="primary", key="fb_post_btn"):
                txn_id = f"TXN-{int(datetime.timestamp(datetime.now()))}"
                p_name = selected_player.split(" (")[0]
                p_id = selected_player.split(" (")[1].replace(")", "")
                
                new_txn = pd.DataFrame([{
                    "TransactionID": txn_id, "MemberID": p_id, "PlayerName": p_name,
                    "PointOfSale": pos_location, "AmountKES": spend_amount, "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }])
                new_txn.to_csv(POS_FILE, mode='a', header=False, index=False)
                st.success(f"Posted KES {spend_amount:,} to student/member account!")
                st.rerun()
        else:
            st.info("No active players synced in live pool database yet.")
            
    # Show active revenue logs below
    st.markdown("---")
    st.subheader("📊 Live Auxiliary Sales Dashboard")
    if os.path.exists(POS_FILE):
        df_pos = pd.read_csv(POS_FILE)
        if not df_pos.empty:
            st.metric("Total Revenue Pool (KES)", f"KES {df_pos['AmountKES'].sum():,}")
            st.dataframe(df_pos.sort_values(by="Timestamp", ascending=False), use_container_width=True)

# -----------------------------------------------------------------------------
# 🏆 MODULE 3: TOURNAMENT LEADERBOARD MONITOR
# -----------------------------------------------------------------------------
elif app_mode == "🏆 Tournament Leaderboard Monitor":
    st.title("🏆 FairwayIQ Live Leaderboard display")
    st.write("Reading real-time stream parameters from local engine nodes...")
    
    if os.path.exists(DB_FILE):
        df_leaderboard = pd.read_csv(DB_FILE)
        if not df_leaderboard.empty:
            st.dataframe(df_leaderboard.sort_values(by="Score", ascending=True), use_container_width=True)
        else:
            st.info("Leaderboard file exists but is empty. Awaiting first finalized score data card.")
    else:
        st.info("Awaiting initial player synchronization data.")