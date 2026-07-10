import streamlit as st
import pandas as pd
import datetime
import os
import time

def render_check_in(season_id: str, conn=None):
    st.title("⛳ FairwayIQ Tournament Center")
    st.subheader("Limuru Country Club - Live Scoring Dashboard")

    # --- STEP 1: PARSE THE USER'S CURRENT VIEW MODE FROM THE URL ---
    current_view = st.query_params.get("view", "standard")

    # --- STEP 2: CENTRAL FILE REFERENCE CONTEXT ---
    DATA_PATH = "data/live_leaderboard.csv"
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    try:
        df_scores = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        data = {
            'MemberID': ['M1001', 'M1002', 'M1003', 'M1004', 'M1005'],
            'PlayerName': ['John Mwangi', 'Alice Koech', 'David Ochieng', 'Martha Njeri', 'Peter Kamau'],
            'Course': ['Limuru Country Club'] * 5,
            'Handicap': [4, 10, 12, 2, 15],
            'Score': [74, 79, 82, 72, 85],
            'Competition': ['NCBA Golf Series'] * 5,
            'MarkerVerification': ['David Ochieng', 'John Mwangi', 'Alice Koech', 'Peter Kamau', 'Martha Njeri'],
            'PlayDate': [str(datetime.datetime.now())] * 5
        }
        df_scores = pd.DataFrame(data)
        df_scores.to_csv(DATA_PATH, index=False)

    # --- STEP 3: DATA MATRICES ALIGNMENT ---
    df_scores.columns = df_scores.columns.str.strip()

    score_col = next((c for c in ['Score', 'Gross_Score', 'Gross Score', 'score', 'gross_score'] if c in df_scores.columns), None)
    hcp_col = next((c for c in ['Handicap', 'handicap', 'HCP', 'hcp'] if c in df_scores.columns), None)
    name_col = next((c for c in ['PlayerName', 'Name', 'name', 'Player', 'player', 'Member_Name'] if c in df_scores.columns), None)

    if score_col and hcp_col:
        df_scores['Gross_Score'] = df_scores[score_col].astype(float)
        df_scores['Handicap'] = df_scores[hcp_col].astype(float)
        df_scores['Net_Score'] = df_scores['Gross_Score'] - df_scores['Handicap']
    else:
        df_scores['Gross_Score'] = 80
        df_scores['Handicap'] = 10
        df_scores['Net_Score'] = 70

    df_scores['Name'] = df_scores[name_col] if name_col else "Unknown Player"
    df_scores = df_scores.sort_values(by='Net_Score').reset_index(drop=True)

    # --- STEP 4: TOURNAMENT STATE MANAGEMENT ---
    if 'tournament_locked' not in st.session_state:
        st.session_state.tournament_locked = False
    if 'admin_verified' not in st.session_state:
        st.session_state.admin_verified = False
    if 'suspense_mode' not in st.session_state:
        st.session_state.suspense_mode = False

    # --- STEP 5: SECURE CONTROL DESK (Hidden for Spectators & TVs) ---
    if current_view == "standard":
        st.sidebar.header("🛠️ Tournament Control Desk")

        if not st.session_state.admin_verified:
            st.sidebar.write("🔒 Enter Official Credentials to unlock modifications.")
            official_pin = st.sidebar.text_input("Club Captain / Admin PIN:", type="password", key="t_ops_admin_pin")
            
            if st.sidebar.button("Verify Official Access", key="t_ops_verify_btn"):
                if official_pin == "1234":
                    st.session_state.admin_verified = True
                    st.sidebar.success("Access Granted!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid PIN. Action Blocked.")
        else:
            st.sidebar.success("🔑 Certified Official Mode Active")
            
            st.session_state.suspense_mode = st.sidebar.toggle(
                "🔒 Activate Final 3 Holes Suspense", 
                value=st.session_state.suspense_mode
            )
            if st.session_state.suspense_mode:
                st.sidebar.warning("Suspense Active: Standings are artificially frozen for non-admins!")
            
            st.sidebar.write("---")
            if not st.session_state.tournament_locked:
                if st.sidebar.button("🔒 Finalize Tournament & Lock Scores", type="primary", key="t_ops_lock_btn"):
                    st.session_state.tournament_locked = True
                    st.rerun()
            else:
                if st.sidebar.button("🔄 Re-open Live Scoring", key="t_ops_unlock_btn"):
                    st.session_state.tournament_locked = False
                    st.rerun()
                    
            if st.sidebar.button("🚪 Lock Control Desk", key="t_ops_logout_btn"):
                st.session_state.admin_verified = False
                st.rerun()

        st.sidebar.write("---")
        st.sidebar.subheader("📺 Quick View Links")
        if st.sidebar.button("Switch to Read-Only Spectator View", key="link_spec_btn"):
            st.query_params["view"] = "spectator"
            st.rerun()
        if st.sidebar.button("Switch to Clubhouse TV Screen View", key="link_tv_btn"):
            st.query_params["view"] = "tv"
            st.rerun()

    elif current_view in ["spectator", "tv"]:
        if st.sidebar.button("⬅️ Return to Main App", key="t_ops_return_btn"):
            st.query_params.clear()
            st.rerun()

    # --- FEATURE: SUSPENSE MODIFIER ---
    if st.session_state.suspense_mode and not st.session_state.admin_verified:
        df_display = df_scores.copy()
        df_display['Name'] = df_display['Name'] + " (Holes 16-18 Masked)"
    else:
        df_display = df_scores.copy()

    # =========================================================================
    # --- TV ENVIRONMENT VIEW LAYOUT BRANCH ---
    # =========================================================================
    if current_view == "tv":
        st.markdown("<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)
        st.title("🏆 FAIRWAYIQ CLUBHOUSE LIVE LEADERBOARD")
        st.subheader("Limuru Country Club — Dining Room Display")
        
        current_time_block = int(time.time())
        sponsor_index = (current_time_block // 10) % 3
        
        st.markdown("---")
        if sponsor_index == 0:
            st.markdown("<div style='background-color:#EAF2F8; padding:15px; border-radius:10px; text-align:center;'><h2>⚡ Official Connectivity Partner: <span style='color:#4CAF50;'>SAFARICOM</span></h2></div>", unsafe_allow_html=True)
        elif sponsor_index == 1:
            st.markdown("<div style='background-color:#FEF9E7; padding:15px; border-radius:10px; text-align:center;'><h2>🍻 Refreshments at the 19th Hole: <span style='color:#E67E22;'>EABL / TUSKER</span></h2></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color:#E8F8F5; padding:15px; border-radius:10px; text-align:center;'><h2>🏦 Premium Banking Partner: <span style='color:#117A65;'>NCBA BANK</span></h2></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.write("### Current Standings")
        st.dataframe(df_display[['Name', 'Gross_Score', 'Handicap', 'Net_Score']], use_container_width=True)
        
        time.sleep(10)
        st.rerun()

    # =========================================================================
    # --- STANDARD SPECTATOR ENVIRONMENT VIEW LAYOUT BRANCH ---
    # =========================================================================
    else:
        if current_view == "spectator":
            st.info("👁️ Viewing in READ-ONLY Spectator Mode. Score submission gates locked.")

        if not st.session_state.tournament_locked:
            if st.session_state.suspense_mode and not st.session_state.admin_verified:
                st.warning("⚠️ FINAL HOLE SUSPENSE ENGAGED: Live computations are locked for the final stretch drama.")
            else:
                st.success("🟢 TOURNAMENT ACTIVE: Scores are live-populating from member phones.")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Field Size", f"{len(df_display)} Players")
            
            if not df_display.empty:
                col2.metric("Current Leader Net", f"{int(df_display['Net_Score'].min())} Net")
                col3.metric("Average Net Score", f"{int(df_display['Net_Score'].mean())}")
            
            st.write("### Current Standings")
            st.dataframe(df_display[['Name', 'Gross_Score', 'Handicap', 'Net_Score']], use_container_width=True)

        else:
            st.balloons() 
            st.error("🏆 TOURNAMENT CONCLUDED - FINAL RESULTS LOCKED")
            
            winner = df_scores.iloc[0]
            second = df_scores.iloc[1] if len(df_scores) > 1 else None
            third = df_scores.iloc[2] if len(df_scores) > 2 else None
            
            st.markdown("## 👑 The Championship Podium")
            podium_col1, podium_col2, podium_col3 = st.columns(3)
            
            with podium_col2:
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
                
            with podium_col1:
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
                    
            with podium_col3:
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
            st.dataframe(df_scores[['Name', 'Gross_Score', 'Handicap', 'Net_Score']], use_container_width=True)
            # This block checks if the file is being run directly by Streamlit
if __name__ == "__main__":
    # 1. Provide a standalone page layout config
    try:
        st.set_page_config(page_title="FairwayIQ Independent Tournament Desk", layout="wide")
    except st.errors.StreamlitAPIException:
        # Failsafe if page config was somehow already set
        pass

    # 2. Fire the execution node independently with dummy parameter contexts
    render_check_in(season_id="standalone_test_season", conn=None)