import streamlit as st
import pandas as pd
import os
from core.database import init_db, get_db_connection

# 1. CONFIGURE GLOBAL WORKSPACE
st.set_page_config(page_title="FairwayIQ Master Hub", page_icon="⛳", layout="wide")

# --- CENTRAL STORAGE CONTEXT ---
# Run relational database engine table initialization on startup
init_db()
conn = get_db_connection()

# Retain flat-file legacy contexts as fallback references for cross-compatibility
DB_FILE = "data/live_leaderboard.csv"
POS_FILE = "data/pos_transactions.csv"

# Shared course reference configuration constants
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
    st.session_state.home_club = "Thika Sports Club"
if 'competition' not in st.session_state:
    st.session_state.competition = "Casual Round"
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1
if 'hole_scores' not in st.session_state:
    st.session_state.hole_scores = {h: LIMURU_PARS[h] for h in range(1, 19)}

# Administrative persistent authentication state
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False
# Master Control: Toggles whether the champion podium remains blank until the round finishes
if 'suspense_mode' not in st.session_state:
    st.session_state.suspense_mode = True

# --- LINK ROUTER & CENTRAL SELECTION HUB ---
query_params = st.query_params
app_mode = None

if "view" in query_params:
    url_view = query_params["view"]
    if url_view == "player":
        app_mode = "🏌️ Player Scorecard Portal"
    elif url_view == "pos":
        app_mode = "🍔 Clubhouse F&B Terminal"
    elif url_view == "monitor":
        app_mode = "🏆 Tournament Leaderboard Monitor"
    else:
        app_mode = "🏌️ Player Scorecard Portal"
else:
    st.sidebar.title("🏁 FairwayIQ Gateway")
    user_role = st.sidebar.radio("Select Portal Role:", ["🏌️ Golfer / Caddie Terminal", "🛡️ Tournament Administration"])
    st.sidebar.markdown("---")

    if user_role == "🏌️ Golfer / Caddie Terminal":
        app_mode = "🏌️ Player Scorecard Portal"
        st.sidebar.success("Player Mode Active")
    else:
        # Secure the administrative side behind a quick entry PIN
        admin_pin = st.sidebar.text_input("Enter Admin Operational PIN:", type="password")
        if admin_pin == "1800":  # Clean numerical code for the society committee
            st.session_state.admin_authenticated = True
            
            # Global Control Switches inside the admin menu sidebar
            st.sidebar.subheader("🎛️ Live Field Controls")
            st.session_state.suspense_mode = st.sidebar.toggle(
                "🔒 Enable Suspense Mode", 
                value=st.session_state.suspense_mode,
                help="When enabled, hides the top 3 podium names from players until the tournament finishes."
            )
            st.sidebar.markdown("---")
            
            app_mode = st.sidebar.selectbox(
                "Select Admin Console:",
                [
                    "🏆 Tournament Leaderboard Monitor",
                    "👥 Society Roster Manager",
                    "🍔 Clubhouse F&B Terminal"
                ]
            )
        elif admin_pin != "":
            st.sidebar.error("❌ Invalid Administrative PIN.")
            app_mode = "🏌️ Player Scorecard Portal"

# 🚦 CLEAN MODULE EXECUTION MATRIX via Import
if app_mode == "🏌️ Player Scorecard Portal":
    from views.scorecard_terminal import render_scorecard_input
    render_scorecard_input(DB_FILE, LIMURU_PARS)

elif app_mode == "🍔 Clubhouse F&B Terminal":
    from views.fandb_terminal import render_fb_pos
    render_fb_pos(POS_FILE, DB_FILE)

elif app_mode == "🏆 Tournament Leaderboard Monitor":
    # Passing 'conn' for live SQL points and passing down the global suspense toggle state
    from views.leaderboard import render_league_leaderboard
    render_league_leaderboard(season_id="season_2026_01", conn=conn)

elif app_mode == "👥 Society Roster Manager":
    from views.roster_manager import render_roster_uploader
    # Passing the live connection object straight into your SQLite data tier pipeline
    render_roster_uploader(season_id="season_2026_01", conn=conn)