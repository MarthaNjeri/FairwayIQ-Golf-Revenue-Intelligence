import streamlit as st
import pandas as pd
import os
import sqlite3
from core.scoring_engine import fetch_league_table

def render_tournament_monitor(DB_FILE, TOTAL_COURSE_PAR):
    st.title("🏆 FairwayIQ Live Leaderboard Display")
    st.caption("⚡ Reading real-time stream parameters from local engine nodes...")
    
    # Check if the tournament database layout file exists
    if os.path.exists(DB_FILE):
        try:
            df_leaderboard = pd.read_csv(DB_FILE)
            if df_leaderboard.shape[1] == 8 and df_leaderboard.columns[0] != "MemberID":
                df_leaderboard.columns = ["MemberID", "PlayerName", "Course", "Handicap", "Score", "Competition", "MarkerVerification", "PlayDate"]
        except Exception:
            df_leaderboard = pd.DataFrame()

        if not df_leaderboard.empty:
            # Core Math Calculations Engine
            df_leaderboard["NetScore"] = df_leaderboard["Score"] - df_leaderboard["Handicap"]
            df_leaderboard["ToPar"] = df_leaderboard["Score"] - TOTAL_COURSE_PAR
            df_leaderboard["ToParDisplay"] = df_leaderboard["ToPar"].apply(lambda x: f"+{int(x)}" if x > 0 else ("Even" if x == 0 else f"{int(x)}"))
            
            df_sorted = df_leaderboard.sort_values(by="NetScore", ascending=True).reset_index(drop=True)
            df_sorted.index += 1
            
            # --- FEATURE 1: LIVE ADMINISTRATIVE INTERACTIVE PANEL ---
            st.sidebar.markdown("---")
            st.sidebar.subheader("🛠️ Captain's Desk Overrides")
            
            # In-view quick toggle for immediate podium announcement
            reveal_podium = st.sidebar.button("🎉 Reveal Podium Winners Now", type="primary")
            if reveal_podium:
                st.session_state.suspense_mode = False
                st.balloons()
                st.rerun()

            # Toggle for Final 3 Holes Blind Strategy
            blind_finish = st.sidebar.toggle("⛳ Enable 'Final 3 Holes' Blind Filter", value=False,
                                            help="Intentionally masks hole tracking indicators to preserve back-9 tension.")

            # KPI Metrics Display Block
            col_t1, col_t2, col_t3 = st.columns(3)
            col_t1.metric("Total Field Size", f"{len(df_sorted)} Players")
            col_t2.metric("Current Best Gross", f"{int(df_leaderboard['Score'].min())} Strokes")
            col_t3.metric("Current Best Net Leader", f"{int(df_sorted['NetScore'].min())} Net")
            
            st.markdown("---")
            st.subheader("👑 Championship Podium Overview")
            
            # Evaluate Suspense Guard
            if st.session_state.get("suspense_mode", True):
                st.warning("🔒 **Suspense Mode Enabled:** The Championship Podium positions are hidden from public broadcast feeds.")
                pod_col1, pod_col2, pod_col3 = st.columns(3)
                with pod_col1: st.info("🥈 **2nd Place Finish**\n\n### 🔒 *Hidden*")
                with pod_col2: st.success("👑 **Tournament Champion**\n\n### 🔒 *Hidden*")
                with pod_col3: st.warning("🥉 **3rd Place Finish**\n\n### 🔒 *Hidden*")
            else:
                podium_cols = st.columns(3)
                if len(df_sorted) >= 2:
                    with podium_cols[0]:
                        st.info(f"🥈 **2nd Place Finish**\n\n### {df_sorted.iloc[1]['PlayerName']}\n"
                                f"**Net:** {int(df_sorted.iloc[1]['NetScore'])} | **Gross:** {int(df_sorted.iloc[1]['Score'])} ({df_sorted.iloc[1]['ToParDisplay']})")
                if len(df_sorted) >= 1:
                    with podium_cols[1]:
                        st.success(f"👑 **Tournament Champion**\n\n## {df_sorted.iloc[0]['PlayerName']}\n"
                                   f"**Net:** {int(df_sorted.iloc[0]['NetScore'])} | **Gross:** {int(df_sorted.iloc[0]['Score'])} ({df_sorted.iloc[0]['ToParDisplay']})")
                if len(df_sorted) >= 3:
                    with podium_cols[2]:
                        st.warning(f"🥉 **3rd Place Finish**\n\n### {df_sorted.iloc[2]['PlayerName']}\n"
                                   f"**Net:** {int(df_sorted.iloc[2]['NetScore'])} | **Gross:** {int(df_sorted.iloc[2]['Score'])} ({df_sorted.iloc[2]['ToParDisplay']})")
            
            st.markdown("---")
            st.subheader("📋 Official Field Standings Matrix")
            
            # Apply Feature 2: Blind final holes masking logic if toggled active
            df_display = df_sorted.copy()
            if blind_finish:
                st.info("👁️ *Final 3 Holes Blind Filter Active:* Field standings scoring parameters are locked to pre-16th hole baselines.")
                # Mask specific column fields for visualization security
                df_display["Score"] = "🔒 Hidden"
                df_display["ToParDisplay"] = "🔒"
                df_display["NetScore"] = "🔒 Locked"

            display_columns = {
                "PlayerName": "Player Profile Name", "Course": "Representing Club",
                "Handicap": "Hcp", "Score": "Gross Strokes", "ToParDisplay": "To Par",
                "NetScore": "Certified Net", "Competition": "Tournament Division", "MarkerVerification": "Attesting Marker"
            }
            st.dataframe(df_display[list(display_columns.keys())].rename(columns=display_columns), use_container_width=True)

            # --- FEATURE 3: DISQUALIFICATION & SCORE OVERRIDE ENGINE ---
            st.markdown("---")
            with st.expander("🚨 Executive Disqualification & Score Correction Deck"):
                st.write("Modify field parameters instantly to correct entry errors or handle R&A rule infractions.")
                
                target_player = st.selectbox("Select Target Golfer Profile:", df_sorted["PlayerName"].unique(), key="dq_player_select")
                action_type = st.radio("Choose Intervention Action Type:", ["Correct Score Value", "Issue Disqualification (DQ)"])
                
                if action_type == "Correct Score Value":
                    new_gross = st.number_input("Input Corrected Total Gross Strokes:", min_value=40, max_value=150, value=72, step=1)
                    if st.button("💾 Overwrite Score Parameter", type="secondary"):
                        # Execute vector override mutation on the running data frame instance
                        df_leaderboard.loc[df_leaderboard["PlayerName"] == target_player, "Score"] = new_gross
                        df_leaderboard.to_csv(DB_FILE, index=False)
                        st.success(f"Successfully modified {target_player}'s gross total score parameter layout.")
                        st.rerun()
                        
                elif action_type == "Issue Disqualification (DQ)":
                    reason = st.text_input("State Official Penalty Infraction Reason:", placeholder="e.g., Unsigned card / Incorrect handicap rule verification")
                    if st.button("🔴 Strike Golfer From Field", type="primary"):
                        # Strip row out of active data lake tracking index
                        df_filtered = df_leaderboard[df_leaderboard["PlayerName"] != target_player]
                        df_filtered.to_csv(DB_FILE, index=False)
                        st.warning(f"Golfer {target_player} has been officially disqualified from this round fixture. Reason: {reason if reason else 'Not Specified'}")
                        st.rerun()

            # --- EXTENSION: 19th HOLE AUXILIARY REVENUE TRACKER ---
            st.markdown("---")
            st.subheader("🍔 Auxiliary Clubhouse F&B Spending Analytics")
            st.caption("Real-time revenue conversion metrics linking field finishers to hospitality bars.")
            
            if os.path.exists("data/pos_transactions.csv"):
                try:
                    df_pos = pd.read_csv("data/pos_transactions.csv")
                    # Clean column names for processing safety
                    df_pos.columns = df_pos.columns.str.strip()
                    
                    # Unify spend metrics
                    total_fb_revenue = df_pos["Amount"].sum() if "Amount" in df_pos.columns else 0.0
                    avg_spend_per_chit = df_pos["Amount"].mean() if "Amount" in df_pos.columns else 0.0
                    
                    rev_col1, rev_col2, rev_col3 = st.columns(3)
                    rev_col1.metric("Total Clubhouse Bar Revenue", f"KES {total_fb_revenue:,.2f} 💸")
                    rev_col2.metric("Average Ticket Value", f"KES {avg_spend_per_chit:,.2f}")
                    
                    if not df_pos.empty and "Item" in df_pos.columns:
                        rev_col3.metric("Highest Velocity Product", str(df_pos["Item"].mode()[0]))
                        
                        st.markdown("#### Recent 19th Hole Bar Orders")
                        st.dataframe(
                            df_pos.tail(5)[["MemberID", "Item", "Amount", "Timestamp"]].rename(
                                columns={"MemberID": "Golfer ID", "Item": "Ordered Item", "Amount": "Bill (KES)"}
                            ),
                            use_container_width=True,
                            hide_index=True
                        )
                except Exception as e:
                    st.caption(f"Waiting for live point-of-sale stream inputs... ({e})")
            else:
                st.info("No active F&B transactions recorded for today's fixture yet.")

        else:
            st.info("Leaderboard database file exists but is empty. Awaiting first finalized scorecard transmission.")
    else:
        st.info("Awaiting initial player synchronization data pipeline.")


def render_league_leaderboard(season_id: str, conn=None):
    """SaaS Adaptive Society Engine: Calculates table points dynamically using live database connections."""
    st.title("🏆 Society League Management Standings")
    st.caption(f"Active League Track Matrix: {season_id.upper().replace('_', ' ')}")
    
    tab1, tab2 = st.tabs(["📊 Cumulative Season Points Table", "🏌️ Active Tournament Monitor"])
    
    with tab1:
        st.subheader("🏆 Live Season Standings (3-1-0 Point Engine)")
        if conn is not None:
            df_standings = fetch_league_table(conn, season_id)
            if not df_standings.empty:
                st.dataframe(
                    df_standings,
                    column_config={
                        "Golfer": st.column_config.TextColumn("Player Name"),
                        "RoundsPlayed": st.column_config.NumberColumn("Played"),
                        "Wins": st.column_config.NumberColumn("W"),
                        "Draws": st.column_config.NumberColumn("D"),
                        "Losses": st.column_config.NumberColumn("L"),
                        "TotalPoints": st.column_config.NumberColumn("Total Points", format="%d 🎯")
                    },
                    use_container_width=True,
                    hide_index=False
                )
            else:
                st.info("League standings are currently clear. Deployed players have not logged finalized scorecards yet.")
        else:
            st.error("❌ No active database pipeline connection detected.")
        
    with tab2:
        render_tournament_monitor("data/live_leaderboard.csv", TOTAL_COURSE_PAR=72)