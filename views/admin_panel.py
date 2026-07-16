import streamlit as st
import pandas as pd
import sqlite3
from core.database import get_db_connection, generate_round_pairings, record_match_score

def render_admin_panel():
    st.title("🛡️ Kachumbari Admin Control Center")
    st.subheader("Manage Roster, Generate Pairings & Record Match Play Scores")

    # Hardcoded context for current active season
    SOCIETY_ID = "Kachumbari"
    SEASON_ID = "2026_S1"

    # Tab Layout
    tab1, tab2, tab3 = st.tabs(["👥 Player Check-In", "⛳ Generate Pairings", "📝 Enter Match Scores"])

    # ==========================================
    # TAB 1: PLAYER CHECK-IN
    # ==========================================
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
            # Display roster in an interactive table with checkboxes
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
                    # Capture checkbox states
                    updated_checkins[p_id] = st.checkbox("", value=bool(is_checked), key=f"check_{p_id}")

            # Save Check-In States Button
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

    # ==========================================
    # TAB 2: ROUND CREATION & MATCH GENERATION
    # ==========================================
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

        # Input fields for new round
        new_round_num = st.number_input("Round Number", min_value=1, max_value=20, value=1, step=1)
        round_date = st.date_input("Match Date")

        if st.button("Generate Match Pairings", type="primary"):
            if checked_in_count < 2:
                st.error("❌ Not enough players checked in to generate head-to-head matches.")
            else:
                # 1. Create the Round in database if it doesn't exist
                cursor.execute("""
                    INSERT INTO rounds (season_id, round_number, play_date)
                    VALUES (?, ?, ?)
                """, (SEASON_ID, new_round_num, str(round_date)))
                round_id = cursor.lastrowid
                conn.commit()

                # 2. Call our pairings generator
                result_message = generate_round_pairings(round_id, SOCIETY_ID, SEASON_ID)
                
                if "Error" in result_message:
                    st.error(result_message)
                else:
                    st.success(f"🏆 {result_message}")
                    conn.close()
                    st.rerun()
        conn.close()

    # ==========================================
    # TAB 3: SCORE ENTRY & 3-1-0 RECORDING
    # ==========================================
    with tab3:
        st.header("Manual Card Score Entry")
        st.write("Select a generated match to record total Net Scores from physical scorecards.")

        conn = get_db_connection()
        
        # Query matches that are scheduled
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
            # Formatting dropdown selection
            matches_df['display_text'] = matches_df.apply(
                lambda x: f"Rd {x['round_number']} | {x['p1_name']} vs {x['p2_name']} [{x['match_status']}]", axis=1
            )
            
            selected_match_text = st.selectbox("Select Match to Log", matches_df['display_text'])
            selected_match_id = matches_df.loc[matches_df['display_text'] == selected_match_text, 'match_id'].values[0]
            selected_row = matches_df.loc[matches_df['match_id'] == selected_match_id].iloc[0]

            st.write("---")
            st.subheader(f"Log Scores: **{selected_row['p1_name']}** vs **{selected_row['p2_name']}**")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p1_net = st.number_input(f"{selected_row['p1_name']} Net Score", min_value=50, max_value=120, value=72, key="p1_net")
            with col_p2:
                p2_net = st.number_input(f"{selected_row['p2_name']} Net Score", min_value=50, max_value=120, value=72, key="p2_net")

            if st.button("Submit Scorecard Results", type="primary"):
                result = record_match_score(selected_match_id, p1_net, p2_net)
                st.success(f"🎉 {result}")
                st.rerun()

# Run rendering directly if executed as main file for local test
if __name__ == "__main__":
    render_admin_panel()