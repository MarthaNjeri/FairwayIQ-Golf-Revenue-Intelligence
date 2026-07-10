import streamlit as st
import pandas as pd
import os
from core.scoring_engine import fetch_league_table

def render_tournament_monitor(DB_FILE, TOTAL_COURSE_PAR):
    st.title("🏆 FairwayIQ Live Leaderboard Display")
    st.caption("⚡ Reading real-time stream parameters from local engine nodes...")
    
    # Check if the tournament database layout file exists
    if os.path.exists(DB_FILE):
        try:
            df_leaderboard = pd.read_csv(DB_FILE)
            # Ensure headers match schema expectations cleanly
            if df_leaderboard.shape[1] == 8 and df_leaderboard.columns[0] != "MemberID":
                df_leaderboard.columns = ["MemberID", "PlayerName", "Course", "Handicap", "Score", "Competition", "MarkerVerification", "PlayDate"]
        except Exception:
            df_leaderboard = pd.DataFrame()

        if not df_leaderboard.empty:
            # Calculate standard tournament scoring rules metrics
            df_leaderboard["NetScore"] = df_leaderboard["Score"] - df_leaderboard["Handicap"]
            df_leaderboard["ToPar"] = df_leaderboard["Score"] - TOTAL_COURSE_PAR
            df_leaderboard["ToParDisplay"] = df_leaderboard["ToPar"].apply(lambda x: f"+{int(x)}" if x > 0 else ("Even" if x == 0 else f"{int(x)}"))
            
            df_sorted = df_leaderboard.sort_values(by="NetScore", ascending=True).reset_index(drop=True)
            df_sorted.index += 1
            
            # KPI Metrics Block
            col_t1, col_t2, col_t3 = st.columns(3)
            col_t1.metric("Total Field Size", f"{len(df_sorted)} Players")
            col_t2.metric("Current Best Gross", f"{int(df_leaderboard['Score'].min())} Strokes")
            col_t3.metric("Current Best Net Leader", f"{int(df_sorted['NetScore'].min())} Net")
            
            st.markdown("---")
            st.subheader("👑 Championship Podium Overview")
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
            
            display_columns = {
                "PlayerName": "Player Profile Name", "Course": "Representing Club",
                "Handicap": "Hcp", "Score": "Gross Strokes", "ToParDisplay": "To Par",
                "NetScore": "Certified Net", "Competition": "Tournament Division", "MarkerVerification": "Attesting Marker"
            }
            
            st.dataframe(df_sorted[list(display_columns.keys())].rename(columns=display_columns), use_container_width=True)
        else:
            st.info("Leaderboard database file exists but is empty. Awaiting first finalized scorecard transmission.")
    else:
        st.info("Awaiting initial player synchronization data pipeline.")


def render_league_leaderboard(season_id: str, conn=None):
    """
    SaaS Adaptive Society Engine: 
    Calculates table points dynamically using live relational database calculations.
    """
    st.title("🏆 Society League Management Standings")
    st.caption(f"Active League Track Matrix: {season_id.upper().replace('_', ' ')}")
    
    # Create tab structure to separate individual tournament view from season table standings
    tab1, tab2 = st.tabs(["📊 Cumulative Season Points Table", "🏌️ Active Tournament Monitor"])
    
    with tab1:
        st.subheader("🏆 Live Season Standings (3-1-0 Point Engine)")
        
        if conn is not None:
            # 🔥 LIVE DB INJECTION: Fetching calculations optimized on the SQL engine layer
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
                st.info("League standings are currently clear. Deployed players have not logged finalized scorecards into the relational ledger yet.")
        else:
            st.error("❌ No active database pipeline connection detected.")
        
    with tab2:
        # Re-route cleanly directly to the native flat-file tournament monitor engine logic
        render_tournament_monitor("data/live_leaderboard.csv", TOTAL_COURSE_PAR=72)