import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FairwayIQ Player Portal", page_icon="⛳", layout="wide")

st.title("⛳ FairwayIQ Digital Scorecard & Live Database")
st.write("Welcome to the Limuru Country Club Scoring Portal. Please submit your round details below.")

# --- DATABASE ENGINE (Local Data Lake) ---
DB_FILE = "data/live_leaderboard.csv"
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=[
        "MemberID", "PlayerName", "Course", "Handicap", 
        "Score", "Competition", "MarkerVerification", "PlayDate"
    ])
    df_init.to_csv(DB_FILE, index=False)

# --- LIMURU COURSE PAR MAP ---
LIMURU_PARS = {
    1: 4, 2: 4, 3: 3, 4: 5, 5: 4, 6: 4, 7: 3, 8: 4, 9: 5,
    10: 4, 11: 4, 12: 3, 13: 5, 14: 4, 15: 4, 16: 3, 17: 4, 18: 5
}
TOTAL_COURSE_PAR = sum(LIMURU_PARS.values())

# --- IDENTITY & HOLE STATE ENGINE ---
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

# Upgraded: Tracking current active hole index and score registry
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1
if 'hole_scores' not in st.session_state:
    st.session_state.hole_scores = {h: LIMURU_PARS[h] for h in range(1, 19)}

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
    
    if player_type == "Club Member":
        input_id = st.number_input("Enter your Club Member ID:", min_value=1, max_value=9999, step=1)
        input_name = st.text_input("Enter Registered Full Name:")
        input_hcp = st.number_input("Verified Club Handicap:", min_value=0, max_value=54, value=12, step=1)
        comp_type = st.selectbox("Select Active Competition:", ["NCBA Golf Series", "Casual Round", "Club Monthly Mug", "Chairman's Prize", "Member-Guest"])
        
        if st.button("Verify & Unlock Scorecard", type="primary"):
            if input_name.strip():
                st.session_state.authorized = True
                st.session_state.auth_type = "Member"
                st.session_state.player_id = input_id
                st.session_state.player_name = input_name
                st.session_state.player_hcp = input_hcp
                st.session_state.home_club = "Limuru Country Club"
                st.session_state.competition = comp_type
                st.rerun()
            else:
                st.error("Please enter your full name to verify membership profile.")
                
    elif player_type == "Visiting Player":
        input_name = st.text_input("Visitor Full Name:")
        selected_club = st.selectbox("Select Your Home Club:", ["Muthaiga Golf Club", "Karen Country Club", "Sigona Golf Club", "Royal Nairobi Golf Club"])
        visitor_hcp = st.number_input("Official Handicap Index:", min_value=0, max_value=54, step=1)
        comp_type = st.selectbox("Select Active Competition:", ["NCBA Golf Series", "Casual Round", "Club Monthly Mug", "Chairman's Prize", "Member-Guest"])
        
        if st.button("Register Guest Competitor", type="primary"):
            if input_name.strip():
                st.session_state.authorized = True
                st.session_state.auth_type = "Visitor"
                st.session_state.player_id = 9000 + visitor_hcp
                st.session_state.player_name = input_name
                st.session_state.player_hcp = visitor_hcp
                st.session_state.home_club = selected_club
                st.session_state.competition = comp_type
                st.rerun()
            else:
                st.error("Please enter your name to register as a visiting competitor.")
                
    elif player_type == "Sponsor / Guest (Non-Playing)":
        st.info("👋 Welcome to the Tournament Event! Scorecard access is exclusively restricted to playing competitors. Please join us at the club lounge layout to view the real-time leaderboard displays!")

    elif player_type == "Club Management / Admin":
        st.subheader("🔑 Executive Portal Verification")
        admin_pin = st.text_input("Enter Management Credentials / PIN:", type="password")
        
        if st.button("Authenticate Admin Console", type="primary"):
            if admin_pin == "1234":
                st.session_state.authorized = True
                st.session_state.auth_type = "Admin"
                st.session_state.player_id = 0
                st.session_state.player_name = "System Administrator"
                st.session_state.home_club = "HQ Operations"
                st.rerun()
            else:
                st.error("❌ Unauthorized Pin Allocation. Management access blocked.")

# --- PHASE 2: INTERFACE ROUTING ---
else:
    st.markdown("---")
    st.success(f"🔓 **Verified Access Granted ({st.session_state.auth_type}):** Welcome, {st.session_state.player_name}")
    
    if st.button("🔄 Logout / Reset Pipeline"):
        st.session_state.authorized = False
        st.session_state.auth_type = None
        st.session_state.current_hole = 1
        st.session_state.hole_scores = {h: LIMURU_PARS[h] for h in range(1, 19)}
        st.rerun()

    # ROUTE A: ADMIN PANEL
    if st.session_state.auth_type == "Admin":
        st.header("📊 FairwayIQ Executive Dashboard")
        power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiYzMzYjA2ODEtYWUzNy00ZTYyLWI3MjMtZTM0Y2QzOWVhZWIwIiwidCI6ImNjZWM4MmJhLTA1OTctNDRjNy1hODM4LTEzNjIwY2MxZGJlYiJ9"
        st.components.v1.iframe(power_bi_url, height=700, scrolling=True)

    # ROUTE B: UPGRADED HOLE-BY-HOLE ENGINE
    else:
        current_h = st.session_state.current_hole
        
        # Live Math Processing Engine
        running_gross = sum(st.session_state.hole_scores.values())
        completed_holes = [h for h in range(1, 19) if h < current_h]
        par_completed = sum(LIMURU_PARS[h] for h in completed_holes)
        strokes_completed = sum(st.session_state.hole_scores[h] for h in completed_holes)
        relative_par = strokes_completed - par_completed

        # Dynamic Stats Top Bar
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Hole Timeline", f"{current_h if current_h <= 18 else 18} / 18")
        col_m2.metric("Running Gross", f"{running_gross} Strokes")
        
        if current_h == 1:
            score_fmt = "Even"
        else:
            score_fmt = f"+{relative_par}" if relative_par > 0 else ("Even" if relative_par == 0 else f"{relative_par}")
        col_m3.metric("To Par (Live)", score_fmt)
        col_m4.metric("Net Projected", f"{int(running_gross - st.session_state.player_hcp)}")

        st.markdown("---")

        # ENGINE STATE 1: GOLFER IS RUNNING THE FAIRWAYS (HOLES 1-18)
        if current_h <= 18:
            st.subheader(f"🏌️ Active Interface: Hole {current_h}")
            
            c_card1, c_card2, c_card3 = st.columns(3)
            c_card1.info(f"⛳ **Hole Par Allocation:** Par {LIMURU_PARS[current_h]}")
            c_card2.metric("Current Value Saved", f"{st.session_state.hole_scores[current_h]} Strokes")
            c_card3.warning(f"🏆 **Event Class:** {st.session_state.competition}")
            
            # Interactive Step Adjustments
            hcp_strokes = st.number_input(
                "Input Score for Current Hole (Gross Strokes):",
                min_value=1, max_value=15, 
                value=int(st.session_state.hole_scores[current_h]), 
                step=1, key=f"input_h_{current_h}"
            )
            st.session_state.hole_scores[current_h] = hcp_strokes

            # Control Row Execution
            st.write("")
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if current_h > 1:
                    if st.button("⬅️ Previous Hole Position", use_container_width=True):
                        st.session_state.current_hole -= 1
                        st.rerun()
            with b_col2:
                if current_h < 18:
                    if st.button("Save & Advance Hole ➡️", use_container_width=True):
                        st.session_state.current_hole += 1
                        st.rerun()
                else:
                    if st.button("🏁 Transition to 18th Hole Review", type="primary", use_container_width=True):
                        st.session_state.current_hole = 19
                        st.rerun()

        # ENGINE STATE 2: THE 18TH HOLE COMPLETED SCREEN (AUTO-CUMULATIVE SUBMISSION)
        else:
            st.balloons()
            st.success("🎉 **18th Hole Green Cleared! Automated Cumulative Score Registry Compiled.**")
            
            st.markdown("### 📋 Final Championship Card Matrix Review")
            
            # Form submission housing
            with st.form("database_submission_form"):
                col_review1, col_review2 = st.columns(2)
                
                with col_review1:
                    st.text_input("Competitor Profile Name:", value=st.session_state.player_name, disabled=True)
                    st.number_input("Final Consolidated Gross Score:", value=running_gross, disabled=True)
                    marker_verification = st.selectbox(
                        "🔒 Select Attesting Flight Competitor (Official Marker Signature):",
                        ["Choose official marker...", "John Mwangi", "Alice Koech", "David Ochieng", "Martha Njeri", "Peter Kamau"]
                    )
                
                with col_review2:
                    st.text_input("Home Course Context:", value=st.session_state.home_club, disabled=True)
                    st.number_input("System Verified Player Handicap Index:", value=st.session_state.player_hcp, disabled=True)
                    final_net_calc = running_gross - st.session_state.player_hcp
                    st.metric("Certified Net Finish Score", f"{int(final_net_calc)}")

                # Expandable hole grid verification display
                with st.expander("🔍 Audit Detailed 18-Hole Matrix Map"):
                    grid_cols = st.columns(6)
                    for h_idx in range(1, 19):
                        col_target = (h_idx - 1) % 6
                        with grid_cols[col_target]:
                            st.markdown(f"**H{h_idx}** `(Par {LIMURU_PARS[h_idx]})` \n### `{st.session_state.hole_scores[h_idx]}`")

                final_commit = st.form_submit_button("🚀 Secure Transmit to Live Leaderboard Desk", type="primary", use_container_width=True)

                if final_commit:
                    if marker_verification == "Choose official marker...":
                        st.error("⚠️ **R&A Verification Rule Violation:** Scorecard rejects entry. You must assign an attesting playing partner marker to authenticate the tournament record.")
                    else:
                        # Append directly into shared file infrastructure 
                        new_row_data = pd.DataFrame([{
                            "MemberID": st.session_state.player_id,
                            "PlayerName": st.session_state.player_name,
                            "Course": st.session_state.home_club,
                            "Handicap": st.session_state.player_hcp,
                            "Score": running_gross,
                            "Competition": st.session_state.competition,
                            "MarkerVerification": marker_verification,
                            "PlayDate": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                        }])
                        
                        new_row_data.to_csv(DB_FILE, mode='a', header=False, index=False)
                        
                        st.success(f"📦 Pipeline Synchronized! Scorecard locked and logged. Marker Signature Token generated: UUID-[{marker_verification.replace(' ', '_')}]")
                        st.caption(f"Network Status: Node Complete | Time Echo: {datetime.today().strftime('%H:%M:%S')}")

# --- PHASE 3: LIVE RE-RENDER VIEWPOOL ---
if st.session_state.authorized and st.session_state.auth_type != "Admin":
    st.markdown("---")
    st.subheader("🏆 Dynamic Club Field Standings")
    if os.path.exists(DB_FILE):
        try:
            df_view = pd.read_csv(DB_FILE)
            if not df_view.empty:
                st.dataframe(df_view.sort_values(by="Score", ascending=True), use_container_width=True)
        except:
            st.info("Leaderboard feed indexing.")