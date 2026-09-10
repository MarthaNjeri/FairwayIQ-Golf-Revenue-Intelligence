import os
import pandas as pd
import streamlit as st
from core.scoring_engine import fetch_league_table


def _load_board(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        df.columns = df.columns.str.strip()
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    if df.shape[1] == 8 and df.columns[0] != "MemberID":
        df.columns = [
            "MemberID", "PlayerName", "Course", "Handicap", "Score",
            "Competition", "MarkerVerification", "PlayDate"
        ]
    if "Team" not in df.columns:
        df["Team"] = "Individual"
    if "Format" not in df.columns:
        df["Format"] = "Full 18 Holes"
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    df["Handicap"] = pd.to_numeric(df["Handicap"], errors="coerce")
    df = df.dropna(subset=["Score"])
    return df


def render_tournament_monitor(DB_FILE, TOTAL_COURSE_PAR):
    st.title("FairwayIQ Live Leaderboard Display")
    st.caption("Live field standings from submitted scorecards")

    df_leaderboard = _load_board(DB_FILE)
    if df_leaderboard.empty:
        st.info("Leaderboard file exists but has no readable scores yet.")
        return

    df_leaderboard["Format"] = df_leaderboard["Format"].fillna("Full 18 Holes").astype(str)
    df_leaderboard["Team"] = df_leaderboard["Team"].fillna("Individual").astype(str)
    df_leaderboard["ParUsed"] = df_leaderboard["Format"].apply(
        lambda x: 36 if "Front 9" in str(x) else TOTAL_COURSE_PAR
    )
    df_leaderboard["NetScore"] = df_leaderboard["Score"] - df_leaderboard["Handicap"]
    df_leaderboard["ToPar"] = df_leaderboard["Score"] - df_leaderboard["ParUsed"]
    df_leaderboard["ToParDisplay"] = df_leaderboard["ToPar"].apply(
        lambda x: f"+{int(x)}" if x > 0 else ("Even" if x == 0 else str(int(x)))
    )

    formats = ["All"] + sorted(df_leaderboard["Format"].unique().tolist())
    teams = ["All"] + sorted(df_leaderboard["Team"].unique().tolist())
    f1, f2 = st.columns(2)
    with f1:
        chosen_format = st.selectbox("Show format", formats)
    with f2:
        chosen_team = st.selectbox("Show team / flight", teams)

    view = df_leaderboard.copy()
    if chosen_format != "All":
        view = view[view["Format"] == chosen_format]
    if chosen_team != "All":
        view = view[view["Team"] == chosen_team]
    if view.empty:
        st.warning("No players in that filter.")
        return

    df_sorted = view.sort_values(by="NetScore", ascending=True).reset_index(drop=True)
    df_sorted.index += 1

    st.sidebar.markdown("---")
    st.sidebar.subheader("Captain's Desk Overrides")
    if st.sidebar.button("Reveal Podium Winners Now", type="primary"):
        st.session_state.suspense_mode = False
        st.balloons()
        st.rerun()
    blind_finish = st.sidebar.toggle("Enable Final 3 Holes Blind Filter", value=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Field Size", f"{len(df_sorted)} Players")
    c2.metric("Current Best Gross", f"{int(view['Score'].min())} Strokes")
    c3.metric("Current Best Net Leader", f"{int(df_sorted['NetScore'].min())} Net")

    st.markdown("---")
    st.subheader("Championship Podium Overview")
    if st.session_state.get("suspense_mode", True):
        st.warning("Suspense Mode Enabled: podium hidden.")
        a, b, c = st.columns(3)
        a.info("2nd Place\n\nHidden")
        b.success("Champion\n\nHidden")
        c.warning("3rd Place\n\nHidden")
    else:
        podium_cols = st.columns(3)
        if len(df_sorted) >= 2:
            with podium_cols[0]:
                st.info(
                    f"2nd Place\n\n### {df_sorted.iloc[1]['PlayerName']}\n"
                    f"Net: {int(df_sorted.iloc[1]['NetScore'])} | Gross: {int(df_sorted.iloc[1]['Score'])}"
                )
        if len(df_sorted) >= 1:
            with podium_cols[1]:
                st.success(
                    f"Champion\n\n## {df_sorted.iloc[0]['PlayerName']}\n"
                    f"Net: {int(df_sorted.iloc[0]['NetScore'])} | Gross: {int(df_sorted.iloc[0]['Score'])}"
                )
        if len(df_sorted) >= 3:
            with podium_cols[2]:
                st.warning(
                    f"3rd Place\n\n### {df_sorted.iloc[2]['PlayerName']}\n"
                    f"Net: {int(df_sorted.iloc[2]['NetScore'])} | Gross: {int(df_sorted.iloc[2]['Score'])}"
                )

    st.markdown("---")
    st.subheader("Official Field Standings Matrix")
    df_display = df_sorted.copy()
    if blind_finish:
        st.info("Final 3 Holes Blind Filter Active.")
        df_display["Score"] = "Hidden"
        df_display["ToParDisplay"] = "Hidden"
        df_display["NetScore"] = "Locked"

    display_columns = {
        "PlayerName": "Player Profile Name",
        "Course": "Representing Club",
        "Handicap": "Hcp",
        "Score": "Gross Strokes",
        "ToParDisplay": "To Par",
        "NetScore": "Certified Net",
        "Format": "Round Format",
        "Team": "Flight / Team",
        "Competition": "Tournament Division",
        "MarkerVerification": "Attesting Marker",
    }
    available = [c for c in display_columns.keys() if c in df_display.columns]
    st.dataframe(
        df_display[available].rename(columns=display_columns),
        use_container_width=True
    )

    st.markdown("---")
    with st.expander("Executive Disqualification & Score Correction Deck"):
        target_player = st.selectbox("Select Target Golfer Profile:", df_sorted["PlayerName"].unique(), key="dq_player_select")
        action_type = st.radio("Choose Intervention Action Type:", ["Correct Score Value", "Issue Disqualification (DQ)"])
        if action_type == "Correct Score Value":
            new_gross = st.number_input("Input Corrected Total Gross Strokes:", min_value=18, max_value=150, value=72, step=1)
            if st.button("Overwrite Score Parameter", type="secondary"):
                full = _load_board(DB_FILE)
                full.loc[full["PlayerName"] == target_player, "Score"] = new_gross
                full.to_csv(DB_FILE, index=False)
                st.success(f"Updated {target_player}.")
                st.rerun()
        elif action_type == "Issue Disqualification (DQ)":
            reason = st.text_input("State Official Penalty Infraction Reason:")
            if st.button("Strike Golfer From Field", type="primary"):
                full = _load_board(DB_FILE)
                full = full[full["PlayerName"] != target_player]
                full.to_csv(DB_FILE, index=False)
                st.warning(f"{target_player} removed. {reason}")
                st.rerun()

    st.markdown("---")
    st.subheader("Auxiliary Clubhouse F&B Spending Analytics")
    if os.path.exists("data/pos_transactions.csv"):
        try:
            df_pos = pd.read_csv("data/pos_transactions.csv")
            df_pos.columns = df_pos.columns.str.strip()
            amount_col = "AmountKES" if "AmountKES" in df_pos.columns else ("Amount" if "Amount" in df_pos.columns else None)
            if amount_col:
                r1, r2, r3 = st.columns(3)
                r1.metric("Total Clubhouse Bar Revenue", f"KES {df_pos[amount_col].sum():,.0f}")
                r2.metric("Average Ticket Value", f"KES {df_pos[amount_col].mean():,.0f}")
                item_col = "Item" if "Item" in df_pos.columns else None
                if item_col:
                    r3.metric("Highest Velocity Product", str(df_pos[item_col].mode()[0]))
        except Exception as e:
            st.caption(f"Waiting for POS stream... ({e})")
    else:
        st.info("No F&B transactions recorded yet.")


def render_league_leaderboard(season_id: str, conn=None):
    st.title("Society League Management Standings")
    st.caption(f"Active League Track Matrix: {season_id.upper().replace('_', ' ')}")
    tab1, tab2 = st.tabs(["Cumulative Season Points Table", "Active Tournament Monitor"])
    with tab1:
        st.subheader("Live Season Standings")
        if conn is not None:
            df_standings = fetch_league_table(conn, season_id)
            if not df_standings.empty:
                st.dataframe(df_standings, use_container_width=True, hide_index=False)
            else:
                st.info("No league points logged yet.")
        else:
            st.error("No database connection.")
    with tab2:
        render_tournament_monitor("data/live_leaderboard.csv", TOTAL_COURSE_PAR=72)