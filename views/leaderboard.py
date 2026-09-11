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
    return df.dropna(subset=["Score"])


def _podium_card(title, name, extra, bg, color):
    st.markdown(f"""
    <div style="background:{bg};border:1px solid #334155;border-radius:14px;padding:18px;min-height:130px;">
        <p style="margin:0;color:#94a3b8;font-size:12px;">{title}</p>
        <h3 style="margin:8px 0 4px 0;color:{color};">{name}</h3>
        <p style="margin:0;color:#cbd5e1;">{extra}</p>
    </div>
    """, unsafe_allow_html=True)


def render_tournament_monitor(DB_FILE, TOTAL_COURSE_PAR):
    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background:#111827;border:1px solid #1f2937;border-radius:14px;padding:10px;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1f2937;border-radius:16px;padding:16px 20px;margin-bottom:16px;">
        <h2 style="margin:0;color:#4ade80;">FairwayIQ Live Tournament Desk</h2>
        <p style="margin:6px 0 0 0;color:#94a3b8;">Format-safe podium · team filter · clubhouse F&B overlay</p>
    </div>
    """, unsafe_allow_html=True)

    df_leaderboard = _load_board(DB_FILE)
    if df_leaderboard.empty:
        st.info("No readable scores yet.")
        return

    df_leaderboard["Format"] = df_leaderboard["Format"].fillna("Full 18 Holes").astype(str)
    df_leaderboard["Team"] = df_leaderboard["Team"].fillna("Individual").astype(str)
    df_leaderboard["ParUsed"] = df_leaderboard["Format"].apply(lambda x: 36 if "Front 9" in str(x) else TOTAL_COURSE_PAR)
    df_leaderboard["NetScore"] = df_leaderboard["Score"] - df_leaderboard["Handicap"]
    df_leaderboard["ToPar"] = df_leaderboard["Score"] - df_leaderboard["ParUsed"]
    df_leaderboard["ToParDisplay"] = df_leaderboard["ToPar"].apply(
        lambda x: f"+{int(x)}" if x > 0 else ("Even" if x == 0 else str(int(x)))
    )

    formats = sorted(df_leaderboard["Format"].unique().tolist())
    teams = ["All"] + sorted(df_leaderboard["Team"].unique().tolist())
    default_format = "Full 18 Holes" if "Full 18 Holes" in formats else formats[0]
    f1, f2 = st.columns(2)
    with f1:
        chosen_format = st.selectbox("Show format", formats, index=formats.index(default_format))
    with f2:
        chosen_team = st.selectbox("Show team / flight", teams)

    view = df_leaderboard[df_leaderboard["Format"] == chosen_format]
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
    c1.metric("Field Size", f"{len(df_sorted)}")
    c2.metric("Best Gross", f"{int(view['Score'].min())}")
    c3.metric("Leader Net", f"{int(df_sorted['NetScore'].min())}")

    st.subheader("Championship Podium")
    hidden = st.session_state.get("suspense_mode", True)
    second = df_sorted.iloc[1] if len(df_sorted) > 1 else None
    champ = df_sorted.iloc[0] if len(df_sorted) > 0 else None
    third = df_sorted.iloc[2] if len(df_sorted) > 2 else None
    p1, p2, p3 = st.columns(3)
    with p1:
        _podium_card("2nd Place", "Hidden" if hidden or second is None else second["PlayerName"],
                     "" if hidden or second is None else f"Net {int(second['NetScore'])} · Gross {int(second['Score'])}",
                     "#1e293b", "#93c5fd")
    with p2:
        _podium_card("Champion", "Hidden" if hidden or champ is None else champ["PlayerName"],
                     "" if hidden or champ is None else f"Net {int(champ['NetScore'])} · Gross {int(champ['Score'])}",
                     "#052e16", "#4ade80")
    with p3:
        _podium_card("3rd Place", "Hidden" if hidden or third is None else third["PlayerName"],
                     "" if hidden or third is None else f"Net {int(third['NetScore'])} · Gross {int(third['Score'])}",
                     "#1c1917", "#fbbf24")

    st.subheader("Official Field Standings")
    df_display = df_sorted.copy()
    if blind_finish:
        st.info("Final 3 Holes Blind Filter Active.")
        df_display["Score"] = "Hidden"
        df_display["ToParDisplay"] = "Hidden"
        df_display["NetScore"] = "Locked"

    display_columns = {
        "PlayerName": "Player", "Course": "Club", "Handicap": "Hcp",
        "Score": "Gross", "ToParDisplay": "To Par", "NetScore": "Net",
        "Format": "Format", "Team": "Team", "Competition": "Event",
        "MarkerVerification": "Marker",
    }
    available = [c for c in display_columns if c in df_display.columns]
    st.dataframe(df_display[available].rename(columns=display_columns), use_container_width=True)

    with st.expander("Score correction / DQ"):
        target_player = st.selectbox("Player", df_sorted["PlayerName"].unique(), key="dq_player_select")
        action_type = st.radio("Action", ["Correct Score Value", "Issue Disqualification (DQ)"])
        if action_type == "Correct Score Value":
            new_gross = st.number_input("Corrected gross", min_value=18, max_value=150, value=72, step=1)
            if st.button("Overwrite Score"):
                full = _load_board(DB_FILE)
                full.loc[full["PlayerName"] == target_player, "Score"] = new_gross
                full.to_csv(DB_FILE, index=False)
                st.rerun()
        else:
            reason = st.text_input("Reason")
            if st.button("Remove from field"):
                full = _load_board(DB_FILE)
                full[full["PlayerName"] != target_player].to_csv(DB_FILE, index=False)
                st.warning(reason)
                st.rerun()

    st.subheader("Clubhouse F&B")
    if os.path.exists("data/pos_transactions.csv"):
        try:
            df_pos = pd.read_csv("data/pos_transactions.csv")
            df_pos.columns = df_pos.columns.str.strip()
            amount_col = "AmountKES" if "AmountKES" in df_pos.columns else ("Amount" if "Amount" in df_pos.columns else None)
            if amount_col:
                r1, r2 = st.columns(2)
                r1.metric("Bar revenue", f"KES {df_pos[amount_col].sum():,.0f}")
                r2.metric("Avg ticket", f"KES {df_pos[amount_col].mean():,.0f}")
        except Exception as e:
            st.caption(f"Waiting for POS... ({e})")
    else:
        st.info("No F&B transactions yet.")


def render_league_leaderboard(season_id: str, conn=None):
    st.title("Society League Management Standings")
    st.caption(f"Active league: {season_id.upper().replace('_', ' ')}")
    tab1, tab2 = st.tabs(["Season Points", "Live Tournament Desk"])
    with tab1:
        if conn is not None:
            df_standings = fetch_league_table(conn, season_id)
            if not df_standings.empty:
                st.dataframe(df_standings, use_container_width=True, hide_index=False)
            else:
                st.info("No league points yet.")
        else:
            st.error("No database connection.")
    with tab2:
        render_tournament_monitor("data/live_leaderboard.csv", TOTAL_COURSE_PAR=72)