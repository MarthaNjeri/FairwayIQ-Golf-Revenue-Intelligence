import streamlit as st
import pandas as pd
import sqlite3
import os
from core.database import get_db_connection, generate_round_pairings, record_match_score

def render_admin_panel(admin_mode=None, DB_FILE=None):
    """
    Unified Administration Router. Integrates default roster & pairing setup with
    advanced Match Day overrides, podium winner calculations, and shootout play.
    """
    # If no specific mode is chosen, default to the main Kachumbari Roster & Score Control Center
    if admin_mode is None or admin_mode == "🏆 Tournament Leaderboard Monitor":
        render_kachumbari_core()
    elif admin_mode == "🛠️ Captain's Desk Overrides":
        render_captains_desk()
    elif admin_mode == "Review podium winners":
        render_podium_winners(DB_FILE)
    elif admin_mode == "enable final 3hole":
        render_final_3hole()


# =====================================================================
# CORE MODULE: KACHUMBARI ADMIN PAIRINGS & SCORE ENTRY
# =====================================================================
def render_kachumbari_core():
    st.title("🛡️ Kachumbari Admin Control Center")
    st.subheader("Manage Roster, Generate Pairings & Record Match Play Scores")

    # Hardcoded context for current active season
    SOCIETY_ID = "Kachumbari"
    SEASON_ID = "2026_S1"

    # Tab Layout
    tab1, tab2, tab3 = st.tabs(["👥 Player Check-In", "⛳ Generate Pairings", "📝 Enter Match Scores"])

    # --- TAB 1: PLAYER CHECK-IN ---
    with tab1:
        st.header("Daily Tournament Check-In")
        st.write("Toggle active players who are physically present at the course today.")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch current roster for this season
        cursor.execute("""
            SELECT player_id, player_name, handicap, checked_in 
            FROM seasonal_roster 
            WHERE society_id = ? AND season_id = ?
            ORDER BY player_name ASC
        """, (SOCIETY_ID, SEASON_ID))
        roster = cursor.fetchall()
        conn.close()

        if not roster:
            st.warning("⚠️ No players found in the roster for this season. Please seed or import players first.")
        else:
            updated_checkins = {}
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown("**Player Name**")
            with col2:
                st.markdown("**Handicap**")
            with col3:
                st.markdown("**Checked In?**")

            for row in roster:
                p_id, name, hcp, is_checked = row['player_id'], row['player_name'], row['handicap'], row['checked_in']
                
                with col1:
                    st.text(name)
                with col2:
                    st.text(f"{hcp:.1f}")
                with col3:
                    updated_checkins[p_id] = st.checkbox("", value=bool(is_checked), key=f"check_{p_id}")

            if st.button("Save Check-In Status", type="primary"):
                conn = get_db_connection()
                cursor = conn.cursor()
                for p_id, status in updated_checkins.items():
                    cursor.execute("""
                        UPDATE seasonal_roster 
                        SET checked_in = ? 
                        WHERE player_id = ?
                    """, (1 if status else 0, p_id))
                conn.commit()
                conn.close()
                st.success("✅ Roster check-ins updated successfully!")
                st.rerun()

    # --- TAB 2: ROUND CREATION & MATCH GENERATION ---
    with tab2:
        st.header("Match Pairings Generator")
        st.write("Create a new round and randomly generate head-to-head matches for checked-in players.")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count checked-in players
        cursor.execute("""
            SELECT COUNT(*) FROM seasonal_roster 
            WHERE society_id = ? AND season_id = ? AND checked_in = 1
        """, (SOCIETY_ID, SEASON_ID))
        checked_in_count = cursor.fetchone()[0]
        st.info(f"💡 Currently Checked In: **{checked_in_count} players**")

        new_round_num = st.number_input("Round Number", min_value=1, max_value=20, value=1, step=1)
        round_date = st.date_input("Match Date")

        if st.button("Generate Match Pairings", type="primary"):
            if checked_in_count < 2:
                st.error("❌ Not enough players checked in to generate head-to-head matches.")
            else:
                cursor.execute("""
                    INSERT INTO rounds (season_id, round_number, play_date)
                    VALUES (?, ?, ?)
                """, (SEASON_ID, new_round_num, str(round_date)))
                round_id = cursor.lastrowid
                conn.commit()

                result_message = generate_round_pairings(round_id, SOCIETY_ID, SEASON_ID)
                
                if "Error" in result_message:
                    st.error(result_message)
                else:
                    st.success(f"🏆 {result_message}")
                    conn.close()
                    st.rerun()
        conn.close()

    # --- TAB 3: SCORE ENTRY & 3-1-0 RECORDING ---
    with tab3:
        st.header("Manual Card Score Entry")
        st.write("Select a generated match to record total Net Scores from physical scorecards.")

        conn = get_db_connection()
        
        matches_df = pd.read_sql_query("""
            SELECT 
                m.match_id,
                r.round_number,
                p1.player_name AS p1_name,
                p2.player_name AS p2_name,
                m.match_status
            FROM matches m
            JOIN rounds r ON m.round_id = r.round_id
            JOIN seasonal_roster p1 ON m.player_1_id = p1.player_id
            JOIN seasonal_roster p2 ON m.player_2_id = p2.player_id
            WHERE r.season_id = ?
            ORDER BY r.round_number DESC, m.match_id ASC
        """, conn, params=(SEASON_ID,))
        conn.close()

        if matches_df.empty:
            st.info("No matches have been generated yet. Go to the 'Generate Pairings' tab first.")
        else:
            matches_df['display_text'] = matches_df.apply(
                lambda x: f"Rd {x['round_number']} | {x['p1_name']} vs {x['p2_name']} [{x['match_status']}]", axis=1
            )
            
            selected_match_text = st.selectbox("Select Match to Log", matches_df['display_text'])
            selected_match_id = matches_df.loc[matches_df['display_text'] == selected_match_text, 'match_id'].values[0]
            selected_row = matches_df.loc[matches_df['match_id'] == selected_match_id].iloc[0]

            st.write("---")
            st.subheader(f"Log Scores: {selected_row['p1_name']} vs {selected_row['p2_name']}")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p1_net = st.number_input(f"{selected_row['p1_name']} Net Score", min_value=50, max_value=120, value=72, key="p1_net")
            with col_p2:
                p2_net = st.number_input(f"{selected_row['p2_name']} Net Score", min_value=50, max_value=120, value=72, key="p2_net")

            if st.button("Submit Scorecard Results", type="primary"):
                result = record_match_score(selected_match_id, p1_net, p2_net)
                st.success(f"🎉 {result}")
                st.rerun()


# =====================================================================
# MODULE 1: CAPTAIN'S DESK OVERRIDES
# =====================================================================
def render_captains_desk():
    st.subheader("🛠️ Captain's Desk Overrides")
    st.write("Direct database controls to adjust active player profiles, playing handicaps, and round configurations.")

    conn = get_db_connection()
    cursor = conn.cursor()

    st.markdown("### 🏌️‍♂️ Live Handicap Adjustments")
    players = pd.read_sql_query("SELECT player_id, player_name, handicap FROM seasonal_roster ORDER BY player_name ASC", conn)
    
    if not players.empty:
        col1, col2 = st.columns(2)
        with col1:
            selected_player = st.selectbox("Select Player to Adjust", players['player_name'])
            player_data = players[players['player_name'] == selected_player].iloc[0]
        with col2:
            new_hcp = st.number_input("Assign New Playing Handicap", min_value=0.0, max_value=54.0, value=float(player_data['handicap']), step=0.5)
        
        if st.button("Apply Handicap Override", type="primary"):
            cursor.execute("UPDATE seasonal_roster SET handicap = ? WHERE player_id = ?", (new_hcp, player_data['player_id']))
            conn.commit()
            st.success(f"Successfully overrode {selected_player}'s handicap to {new_hcp}!")
            st.rerun()
    else:
        st.info("No active players in roster database to override.")

    st.markdown("---")

    st.markdown("### ⚔️ Match Status Control")
    matches = pd.read_sql_query("""
        SELECT m.match_id, r.player_name as p1, r2.player_name as p2, m.match_status 
        FROM matches m
        JOIN seasonal_roster r ON m.player_1_id = r.player_id
        JOIN seasonal_roster r2 ON m.player_2_id = r2.player_id
    """, conn)

    if not matches.empty:
        matches['Matchup'] = matches['p1'] + " vs " + matches['p2'] + " (" + matches['match_status'] + ")"
        selected_match_label = st.selectbox("Select Active Match to Override", matches['Matchup'])
        match_id = int(matches[matches['Matchup'] == selected_match_label].iloc[0]['match_id'])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            new_status = st.selectbox("Force Match Status", ["Scheduled", "Completed"])
        with col_m2:
            st.write("")
            st.write("")
            if st.button("Force Match Status Override"):
                cursor.execute("UPDATE matches SET match_status = ? WHERE match_id = ?", (new_status, match_id))
                conn.commit()
                st.success("Match status adjusted successfully!")
                st.rerun()
    else:
        st.info("No matchups found in the match engine.")

    conn.close()


# =====================================================================
# MODULE 2: REVIEW PODIUM WINNERS
# =====================================================================
def render_podium_winners(DB_FILE):
    st.subheader("🏆 Round Podium Winners")
    st.write("Dynamic calculation of today's tournament winners based on submitted scorecards.")

    if not DB_FILE or not os.path.exists(DB_FILE):
        st.warning("⚠️ No scorecard entries are available to calculate podium winners.")
        return

    try:
        df = pd.read_csv(DB_FILE)
        if df.empty:
            st.warning("No records found in the tournament scorecard database.")
            return

        df['Score'] = pd.to_numeric(df['Score'], errors='coerce')
        df['Handicap'] = pd.to_numeric(df['Handicap'], errors='coerce')
        df['NetScore'] = df['Score'] - df['Handicap']
        df = df.dropna(subset=['Score', 'NetScore'])

        best_gross_row = df.loc[df['Score'].idxmin()]
        best_net_row = df.loc[df['NetScore'].idxmin()]

        remaining_df = df[df['PlayerName'] != best_gross_row['PlayerName']]
        best_net_runner_up = remaining_df.loc[remaining_df['NetScore'].idxmin()] if not remaining_df.empty else None

        col_g, col_n, col_r = st.columns(3)
        
        with col_g:
            st.success("🥇 Best Gross Champion")
            st.subheader(best_gross_row['PlayerName'])
            st.metric(label="Gross Score", value=f"{int(best_gross_row['Score'])} Strokes")
            st.caption(f"Course Context: {best_gross_row['Course']}")

        with col_n:
            st.info("🥈 Best Net Winner")
            st.subheader(best_net_row['PlayerName'])
            st.metric(label="Net Score", value=f"{int(best_net_row['NetScore'])}")
            st.caption(f"Playing Handicap: {best_net_row['Handicap']}")

        with col_r:
            st.warning("🥉 Net Runner-Up")
            if best_net_runner_up is not None:
                st.subheader(best_net_runner_up['PlayerName'])
                st.metric(label="Net Score", value=f"{int(best_net_runner_up['NetScore'])}")
                st.caption(f"Playing Handicap: {best_net_runner_up['Handicap']}")
            else:
                st.write("No eligible runner-up available.")

    except Exception as e:
        st.error(f"Failed to calculate podium results: {e}")


# =====================================================================
# MODULE 3: ENABLE FINAL 3-HOLE SHOOTOUT
# =====================================================================
def render_final_3hole():
    st.subheader("🏁 Live 3-Hole Shootout Controller")
    st.write("Activate and manage a sudden-death playoff shootout across Holes 16, 17, and 18 for tied field leaders.")

    if 'shootout_active' not in st.session_state:
        st.session_state.shootout_active = False
    if 'shootout_players' not in st.session_state:
        st.session_state.shootout_players = []

    status_color = "🟢 Active" if st.session_state.shootout_active else "🔴 Dormant"
    st.info(f"Current Shootout Engine Status: **{status_color}**")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Initialize Shootout Bracket", use_container_width=True, type="primary"):
            st.session_state.shootout_active = True
            st.success("Playoff Shootout initialized! Holes 16, 17, and 18 locked for shootout tracking.")
    with col_btn2:
        if st.button("🛑 Terminate Shootout Bracket", use_container_width=True):
            st.session_state.shootout_active = False
            st.session_state.shootout_players = []
            st.warning("Shootout deactivated. Playoffs ended.")
            st.rerun()

    if st.session_state.shootout_active:
        st.markdown("---")
        st.write("### Playoff Contender Setup")
        
        conn = get_db_connection()
        all_players = pd.read_sql_query("SELECT player_name FROM seasonal_roster WHERE checked_in = 1", conn)
        conn.close()

        if not all_players.empty:
            selected_contenders = st.multiselect("Add Playoff Competitors", all_players['player_name'].unique())
            
            if st.button("Lock Shootout Roster"):
                st.session_state.shootout_players = selected_contenders
                st.success("Playoff competitors roster locked!")

        if st.session_state.shootout_players:
            st.write("### 🎛️ Dynamic Playoff Scoring Grid")
            shootout_scores = {}
            
            for player in st.session_state.shootout_players:
                st.write(f"**Competitor:** {player}")
                cols = st.columns(3)
                scores = []
                for idx, hole in enumerate([16, 17, 18]):
                    with cols[idx]:
                        score = st.number_input(f"Hole {hole} (Score)", min_value=1, max_value=10, value=4, key=f"playoff_{player}_{hole}")
                        scores.append(score)
                shootout_scores[player] = sum(scores)

            st.write("### 🥇 Live Shootout Leaderboard")
            sorted_shootout = sorted(shootout_scores.items(), key=lambda x: x[1])
            standings_df = pd.DataFrame(sorted_shootout, columns=["Player", "Consolidated Playoff Score"])
            st.dataframe(standings_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_admin_panel()