import os
import time
import pandas as pd
import streamlit as st

DATA_PATH = "data/live_leaderboard.csv"
LEADERBOARD_COLS = [
    "MemberID", "PlayerName", "Course", "Handicap", "Score",
    "Competition", "Team", "Format", "MarkerVerification", "PlayDate"
]


def _get_admin_pin():
    try:
        return st.secrets["admin"]["pin"]
    except Exception:
        return "1800"


def _load_scores():
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=LEADERBOARD_COLS)

    try:
        df = pd.read_csv(DATA_PATH, engine="python", on_bad_lines="skip")
        df.columns = df.columns.str.strip()
    except Exception:
        return pd.DataFrame(columns=LEADERBOARD_COLS)

    if "Team" not in df.columns:
        df["Team"] = "Individual"
    if "Format" not in df.columns:
        df["Format"] = "Full 18 Holes"
    if "MarkerVerification" not in df.columns:
        df["MarkerVerification"] = ""
    if "PlayDate" not in df.columns:
        df["PlayDate"] = ""
    return df


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    score_col = next((c for c in ["Score", "Gross_Score", "Gross Score", "score"] if c in df.columns), None)
    hcp_col = next((c for c in ["Handicap", "handicap", "HCP", "hcp"] if c in df.columns), None)
    name_col = next((c for c in ["PlayerName", "Name", "Player", "player"] if c in df.columns), None)

    out = df.copy()
    out["Gross_Score"] = pd.to_numeric(out[score_col], errors="coerce") if score_col else 80
    out["Handicap"] = pd.to_numeric(out[hcp_col], errors="coerce") if hcp_col else 10
    out["Gross_Score"] = out["Gross_Score"].fillna(80)
    out["Handicap"] = out["Handicap"].fillna(10)
    out["Net_Score"] = out["Gross_Score"] - out["Handicap"]
    out["Name"] = out[name_col] if name_col else "Unknown Player"
    out["Format"] = out["Format"] if "Format" in out.columns else "Full 18 Holes"
    out["Team"] = out["Team"] if "Team" in out.columns else "Individual"
    out = out.sort_values(by="Net_Score").reset_index(drop=True)
    out["Position"] = out.index + 1
    return out


def render_check_in(season_id: str, conn=None):
    st.title("FairwayIQ Tournament Center")
    st.caption("Live scoring, spectator view, and clubhouse TV leaderboard")

    current_view = st.query_params.get("view", "standard")
    df_raw = _load_scores()
    df_scores = _normalize(df_raw)

    if "tournament_locked" not in st.session_state:
        st.session_state.tournament_locked = False
    if "admin_verified" not in st.session_state:
        st.session_state.admin_verified = False
    if "suspense_mode" not in st.session_state:
        st.session_state.suspense_mode = False

    if current_view == "standard":
        st.sidebar.header("Tournament Control Desk")
        if not st.session_state.admin_verified:
            official_pin = st.sidebar.text_input("Admin PIN:", type="password", key="t_ops_admin_pin")
            if st.sidebar.button("Verify Official Access", key="t_ops_verify_btn"):
                if official_pin == _get_admin_pin():
                    st.session_state.admin_verified = True
                    st.rerun()
                else:
                    st.sidebar.error("Invalid PIN")
        else:
            st.sidebar.success("Certified Official Mode Active")
            st.session_state.suspense_mode = st.sidebar.toggle(
                "Final 3 Holes Suspense",
                value=st.session_state.suspense_mode
            )
            if not st.session_state.tournament_locked:
                if st.sidebar.button("Finalize Tournament & Lock Scores", type="primary"):
                    st.session_state.tournament_locked = True
                    st.rerun()
            else:
                if st.sidebar.button("Re-open Live Scoring"):
                    st.session_state.tournament_locked = False
                    st.rerun()
            if st.sidebar.button("Lock Control Desk"):
                st.session_state.admin_verified = False
                st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.subheader("Quick Views")
        if st.sidebar.button("Spectator View"):
            st.query_params["view"] = "spectator"
            st.rerun()
        if st.sidebar.button("Clubhouse TV View"):
            st.query_params["view"] = "tv"
            st.rerun()
    else:
        if st.sidebar.button("Return to Main App"):
            st.query_params.clear()
            st.rerun()

    df_display = df_scores.copy()
    if st.session_state.suspense_mode and not st.session_state.admin_verified and not df_display.empty:
        df_display.loc[df_display.index < 3, "Name"] = "Leader (Hidden)"

    show_cols = [c for c in [
        "Position", "Name", "Gross_Score", "Handicap", "Net_Score",
        "Format", "Team", "Course", "Competition"
    ] if c in df_display.columns]

    if current_view == "tv":
        st.title("FAIRWAYIQ LIVE LEADERBOARD")
        st.subheader("Limuru Country Club — Clubhouse Display")
        sponsors = [
            ("SAFARICOM", "#EAF2F8", "#16a34a"),
            ("EABL / TUSKER", "#FEF9E7", "#E67E22"),
            ("NCBA BANK", "#E8F8F5", "#117A65"),
        ]
        name, bg, color = sponsors[int(time.time() // 8) % 3]
        st.markdown(
            f"<div style='background:{bg};padding:14px;border-radius:10px;text-align:center;'>"
            f"<h3>Official Partner: <span style='color:{color};'>{name}</span></h3></div>",
            unsafe_allow_html=True
        )
        if df_display.empty:
            st.info("Waiting for live scores...")
        else:
            st.dataframe(df_display[show_cols], use_container_width=True, hide_index=True)
        st.caption("Auto-refreshing clubhouse view")
        time.sleep(3)
        st.rerun()
        return

    if current_view == "spectator":
        st.info("Read-only Spectator Mode")

    if df_display.empty:
        st.warning("No scores submitted yet. Players should complete Gate Check-in and submit a scorecard.")
        return

    formats = ["All"] + sorted(df_display["Format"].dropna().astype(str).unique().tolist())
    chosen = st.selectbox("Show format", formats)
    view_df = df_display if chosen == "All" else df_display[df_display["Format"].astype(str) == chosen]
    view_df = view_df.sort_values("Net_Score").reset_index(drop=True)
    view_df["Position"] = view_df.index + 1

    if not st.session_state.tournament_locked:
        if st.session_state.suspense_mode and not st.session_state.admin_verified:
            st.warning("Suspense Mode: top positions are hidden.")
        else:
            st.success("Tournament Active — live scores updating")

        c1, c2, c3 = st.columns(3)
        c1.metric("Field Size", f"{len(view_df)}")
        c2.metric("Leader Net", f"{int(view_df['Net_Score'].min())}" if not view_df.empty else "-")
        c3.metric("Average Net", f"{int(view_df['Net_Score'].mean())}" if not view_df.empty else "-")

        st.subheader("Current Standings")
        st.dataframe(view_df[show_cols], use_container_width=True, hide_index=True)
    else:
        st.success("Tournament Concluded — Results Locked")
        if view_df.empty:
            st.info("No players in this format.")
            return

        winner = view_df.iloc[0]
        second = view_df.iloc[1] if len(view_df) > 1 else None
        third = view_df.iloc[2] if len(view_df) > 2 else None

        st.markdown("## Championship Podium")
        p1, p2, p3 = st.columns(3)
        with p2:
            st.markdown(f"""
            <div style="background:#D4AF37;padding:20px;border-radius:15px;text-align:center;">
                <h3>1st Place</h3>
                <h2>{winner['Name']}</h2>
                <h1>{int(winner['Net_Score'])} Net</h1>
                <p>Gross {int(winner['Gross_Score'])} | HCP {int(winner['Handicap'])}</p>
            </div>
            """, unsafe_allow_html=True)
        with p1:
            if second is not None:
                st.markdown(f"""
                <div style="background:#C0C0C0;padding:20px;border-radius:15px;text-align:center;margin-top:30px;">
                    <h3>2nd Place</h3>
                    <h3>{second['Name']}</h3>
                    <h2>{int(second['Net_Score'])} Net</h2>
                </div>
                """, unsafe_allow_html=True)
        with p3:
            if third is not None:
                st.markdown(f"""
                <div style="background:#CD7F32;padding:20px;border-radius:15px;text-align:center;margin-top:45px;">
                    <h3>3rd Place</h3>
                    <h3>{third['Name']}</h3>
                    <h2>{int(third['Net_Score'])} Net</h2>
                </div>
                """, unsafe_allow_html=True)

        st.subheader("Final Standings")
        st.dataframe(view_df[show_cols], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    try:
        st.set_page_config(page_title="FairwayIQ Tournament Desk", layout="wide")
    except Exception:
        pass
    render_check_in(season_id="2026_S1", conn=None)