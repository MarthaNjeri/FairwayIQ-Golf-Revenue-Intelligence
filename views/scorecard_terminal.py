import os
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from fpdf import FPDF

from core.database import get_db_connection, get_course_pars_and_si

KENYAN_GOLF_CLUBS = {
    "Nairobi Region": [
        "Golf Park", "Karen Country Club", "Kenya Airforce Golf Club", "Kenya Railway Golf Course",
        "Kiambu Golf Club", "Limuru Country Club", "Machakos Golf Club", "Muthaiga Golf Club",
        "Ndumberi Golf Club", "Royal Nairobi Golf Club", "Ruiru Sports Club", "Sigona Golf Club",
        "Thika Barracks Golf Club", "Thika Greens Golf Resort", "Thika Sports Club", "VetLab Sports Club",
        "Windsor Golf Hotel & Country Club", "Migaa Golf Club"
    ],
    "Mt. Kenya Region": ["Nanyuki Sports Club", "Nyahururu Country Club", "Nyeri Golf Club"],
    "Central Rift": [
        "Gilgil Country Club", "Great Rift Valley Golf Resort", "Naivasha Sports Club",
        "Nakuru Golf Club", "Njoro Country Club", "Mt. Kipipiri Golf Resort"
    ],
    "Coast": [
        "Leisure Lodge Golf Club", "Malindi Golf Club", "Mombasa Golf Club",
        "Nyali Golf & Country Club Ltd", "Vipingo Ridge"
    ],
    "Western": ["Kakamega Golf Club", "Kisii Golf Club", "Mumias Golf Club", "Nyanza Golf Club"],
    "North Rift": ["Eldoret Golf Club", "Kericho Golf Course", "Kitale Club", "Nandi Bears Golf Club"]
}
ALL_KENYAN_CLUBS_FLAT = sorted([club for region in KENYAN_GOLF_CLUBS.values() for club in region])
KENYAN_COMPETITIONS = [
    "Club Nite (Stableford)", "Club Monthly Mug",
    "NCBA Golf Series", "KCB Golf Series", "ABSA Golf Day", "ICEA Lion Golf Tournament",
    "Britam Golf Series", "CIC Golf Day", "Safaricom Golf Day",
    "Sigona Open (KAGC)", "Muthaiga Open (KAGC)", "Karen Open (KAGC)",
    "Nakuru Open (KAGC)", "Limuru Open (KAGC)", "Nyali Open (KAGC)",
    "Magical Kenya Open (DP World Tour)", "Casual Round", "Corporate Day"
]


def build_scorecard_pdf(player_name, handicap, course, tee, competition,
                        hole_scores, active_pars, round_variant, playing_partners="Individual"):
    active_limit = 9 if round_variant == "Front 9 Only" else 18
    playing_hcp = int(float(handicap or 0))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(10, 10, 190, 32, "F")
    pdf.set_text_color(74, 222, 128)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(14, 13)
    pdf.cell(180, 8, "FairwayIQ Official Scorecard")
    pdf.set_text_color(226, 232, 240)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(14, 22)
    pdf.cell(180, 6, f"{player_name}  |  HCP: {playing_hcp}  |  {course} ({tee})  |  {competition}")
    pdf.set_xy(14, 28)
    pdf.cell(180, 6, f"Team: {playing_partners}  |  Format: {round_variant}  |  {datetime.now().strftime('%d %b %Y')}")
    pdf.set_xy(10, 48)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    for w, label in [(18, "Hole"), (18, "Par"), (22, "Score"), (22, "+/-")]:
        pdf.cell(w, 8, label, border=0, fill=True)
    pdf.ln()
    total_score = 0
    total_par = 0
    pdf.set_font("Helvetica", "", 10)
    for h in range(1, active_limit + 1):
        par = int(active_pars.get(h, 4))
        score = int(hole_scores.get(h, par))
        diff = score - par
        pm = "E" if diff == 0 else (f"+{diff}" if diff > 0 else str(diff))
        if diff <= -1:
            pdf.set_fill_color(187, 247, 208)
            pdf.set_text_color(22, 101, 52)
        elif diff == 0:
            pdf.set_fill_color(248, 250, 252)
            pdf.set_text_color(15, 23, 42)
        elif diff == 1:
            pdf.set_fill_color(254, 249, 195)
            pdf.set_text_color(133, 77, 14)
        else:
            pdf.set_fill_color(254, 202, 202)
            pdf.set_text_color(153, 27, 27)
        pdf.set_x(10)
        pdf.cell(18, 8, str(h), border=1, fill=True)
        pdf.cell(18, 8, str(par), border=1, fill=True)
        pdf.cell(22, 8, str(score), border=1, fill=True)
        pdf.cell(22, 8, pm, border=1, fill=True)
        pdf.ln()
        total_score += score
        total_par += par
    pdf.set_x(10)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(18, 8, "TOT", border=0, fill=True)
    pdf.cell(18, 8, str(total_par), border=0, fill=True)
    pdf.cell(22, 8, str(total_score), border=0, fill=True)
    pdf.cell(22, 8, f"Net {int(total_score - playing_hcp)}", border=0, fill=True)
    out = BytesIO()
    pdf.output(out)
    return out.getvalue()


def render_master_scorecard(player_name, handicap, course, tee, competition,
                            hole_scores, active_pars, round_variant="Full 18 Holes",
                            playing_partners="Individual"):
    active_limit = 9 if round_variant == "Front 9 Only" else 18
    holes = list(range(1, active_limit + 1))
    front_holes = list(range(1, 10))
    back_holes = list(range(10, 19)) if active_limit == 18 else []
    front_score = sum(hole_scores.get(h, active_pars.get(h, 4)) for h in front_holes)
    back_score = sum(hole_scores.get(h, active_pars.get(h, 4)) for h in back_holes) if back_holes else 0
    total_score = front_score + back_score
    front_par = sum(active_pars.get(h, 4) for h in front_holes)
    back_par = sum(active_pars.get(h, 4) for h in back_holes) if back_holes else 0
    total_par = front_par + back_par
    playing_hcp = int(float(handicap or 0))
    st.markdown(f"""
    <div style="background:#0f172a; color:white; padding:16px 20px; border-radius:12px 12px 0 0;">
        <h3 style="margin:0 0 6px 0; color:#4ade80;">FairwayIQ Official Scorecard</h3>
        <p style="margin:0; font-size:0.95rem; color:#cbd5e1;">
            <strong>{player_name}</strong> | HCP: {playing_hcp} |
            {course} ({tee}) | {competition}<br>
            Team: {playing_partners or 'Individual'} | Format: {round_variant}<br>
            Date: {datetime.now().strftime('%d %b %Y')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    data = {"Hole": [], "Par": [], "Score": [], "+/-": []}
    for h in holes:
        par = active_pars.get(h, 4)
        score = hole_scores.get(h, par)
        diff = score - par
        data["Hole"].append(h)
        data["Par"].append(par)
        data["Score"].append(score)
        data["+/-"].append(f"+{diff}" if diff > 0 else ("E" if diff == 0 else str(diff)))
    if active_limit == 18:
        data["Hole"].extend(["OUT", "IN", "TOTAL"])
        data["Par"].extend([front_par, back_par, total_par])
        data["Score"].extend([front_score, back_score, total_score])
        front_diff = front_score - front_par
        back_diff = back_score - back_par
        total_diff = total_score - total_par
        data["+/-"].extend([
            f"+{front_diff}" if front_diff > 0 else ("E" if front_diff == 0 else str(front_diff)),
            f"+{back_diff}" if back_diff > 0 else ("E" if back_diff == 0 else str(back_diff)),
            f"+{total_diff}" if total_diff > 0 else ("E" if total_diff == 0 else str(total_diff))
        ])
    else:
        data["Hole"].extend(["OUT", "TOTAL"])
        data["Par"].extend([front_par, total_par])
        data["Score"].extend([front_score, total_score])
        front_diff = front_score - front_par
        total_diff = total_score - total_par
        data["+/-"].extend([
            f"+{front_diff}" if front_diff > 0 else ("E" if front_diff == 0 else str(front_diff)),
            f"+{total_diff}" if total_diff > 0 else ("E" if total_diff == 0 else str(total_diff))
        ])
    df = pd.DataFrame(data)

    def style_row(row):
        styles = [""] * len(row)
        if str(row["Hole"]) in ["OUT", "IN", "TOTAL"]:
            return ["background-color:#1e293b; color:white; font-weight:700;"] * len(row)
        try:
            hole_num = int(row["Hole"])
            par = active_pars.get(hole_num, 4)
            diff = int(row["Score"]) - par
            if diff <= -1:
                styles[2] = "background-color:#bbf7d0; color:#166534; font-weight:600;"
            elif diff == 0:
                styles[2] = "background-color:#f8fafc; color:#1e293b;"
            elif diff == 1:
                styles[2] = "background-color:#fef9c3; color:#854d0e;"
            else:
                styles[2] = "background-color:#fecaca; color:#991b1b; font-weight:600;"
        except Exception:
            pass
        return styles

    st.dataframe(df.style.apply(style_row, axis=1), use_container_width=True, hide_index=True, height=780)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Score", total_score)
    c2.metric("vs Par", f"+{total_diff}" if total_diff > 0 else total_diff)
    c3.metric("Net Score", int(total_score - playing_hcp))
    c4.metric("Holes Played", active_limit)
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in str(player_name))
    stamp = datetime.now().strftime("%Y%m%d")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Download Scorecard (PDF)",
            data=build_scorecard_pdf(
                player_name, handicap, course, tee, competition,
                hole_scores, active_pars, round_variant, playing_partners
            ),
            file_name=f"FairwayIQ_Scorecard_{safe_name}_{stamp}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with d2:
        st.download_button(
            "Download Scorecard (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"FairwayIQ_Scorecard_{safe_name}_{stamp}.csv",
            mime="text/csv",
            use_container_width=True
        )


def render_scorecard_input(DB_FILE, FALLBACK_PARS):
    st.title("FairwayIQ Digital Scorecard")
    conn = get_db_connection()
    try:
        courses_df = pd.read_sql_query("SELECT DISTINCT course_name FROM golf_courses", conn)
        course_options = courses_df["course_name"].tolist() if not courses_df.empty else ["Limuru Country Club"]
    except Exception:
        course_options = ["Limuru Country Club"]

    defaults = {
        "authorized": False, "auth_type": None, "player_name": "", "player_id": 1,
        "player_hcp": 12, "selected_course": course_options[0], "selected_tee": "White",
        "competition": "Casual Round", "current_hole": 1, "round_variant": "Full 18 Holes",
        "scorecard_submitted": False, "playing_partners": "Individual", "hole_times": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    try:
        raw_map = get_course_pars_and_si(st.session_state.selected_course, st.session_state.selected_tee)
        if raw_map:
            ACTIVE_PARS = {h: v[0] for h, v in raw_map.items()}
            ACTIVE_SI = {h: v[1] for h, v in raw_map.items()}
        else:
            ACTIVE_PARS = FALLBACK_PARS
            ACTIVE_SI = {h: h for h in range(1, 19)}
    except Exception:
        ACTIVE_PARS = FALLBACK_PARS
        ACTIVE_SI = {h: h for h in range(1, 19)}

    if "hole_scores" not in st.session_state or len(st.session_state.hole_scores) != 18:
        st.session_state.hole_scores = {h: ACTIVE_PARS.get(h, 4) for h in range(1, 19)}

    display_name = st.session_state.get("player_name") or "Guest Player"
    playing_hcp = int(float(st.session_state.get("player_hcp") or 12))
    partners = st.session_state.get("playing_partners") or "Individual"

    if not st.session_state.authorized:
        st.subheader("Tournament Gate Check-in")
        player_type = st.radio(
            "Select Registration Type:",
            ["Club Member", "Visiting Player", "Sponsor / Guest (Non-Playing)", "Club Management / Admin"],
            horizontal=True
        )
        if player_type == "Club Member":
            input_id = st.number_input("Enter your Club Member ID:", min_value=1, max_value=9999, step=1)
            input_name = st.text_input("Enter Registered Full Name:")
            input_hcp = st.number_input("Verified Club Handicap:", min_value=0, max_value=54, value=12, step=1)
            partners_in = st.text_input("Playing partners / team (optional)", placeholder="e.g. Flight A")
            c1, c2 = st.columns(2)
            with c1:
                region = st.selectbox("Select Club Region:", list(KENYAN_GOLF_CLUBS.keys()))
            with c2:
                reg_course = st.selectbox("Select Golf Club Playing Today:", KENYAN_GOLF_CLUBS[region])
            reg_tee = st.selectbox("Select Tee Set Played:", ["White", "Yellow", "Red", "Blue"])
            comp_type = st.selectbox("Select Active Competition / Event:", KENYAN_COMPETITIONS)
            variant = st.selectbox("Select Planned Round Format:", ["Full 18 Holes", "Front 9 Only"])
            if st.button("Verify & Unlock Scorecard", type="primary"):
                if input_name.strip():
                    st.session_state.authorized = True
                    st.session_state.auth_type = "player"
                    st.session_state.player_id = input_id
                    st.session_state.player_name = input_name.strip()
                    st.session_state.player_hcp = int(input_hcp)
                    st.session_state.playing_partners = partners_in.strip() or "Individual"
                    st.session_state.selected_course = reg_course
                    st.session_state.selected_tee = reg_tee
                    st.session_state.competition = comp_type
                    st.session_state.round_variant = variant
                    st.session_state.scorecard_submitted = False
                    st.session_state.current_hole = 1
                    st.session_state.hole_times = {}
                    st.session_state.hole_scores = {h: ACTIVE_PARS.get(h, 4) for h in range(1, 19)}
                    st.rerun()
                else:
                    st.error("Please enter your full name.")
        elif player_type == "Visiting Player":
            input_name = st.text_input("Visitor Full Name:")
            visitor_home = st.selectbox("Select Your Official Home Club:", ALL_KENYAN_CLUBS_FLAT)
            partners_in = st.text_input("Playing partners / team (optional)", placeholder="e.g. Flight A")
            c1, c2 = st.columns(2)
            with c1:
                region = st.selectbox("Select Playing Club Region:", list(KENYAN_GOLF_CLUBS.keys()))
            with c2:
                reg_course = st.selectbox("Select Venue Playing Today:", KENYAN_GOLF_CLUBS[region])
            reg_tee = st.selectbox("Select Tee Set Played:", ["White", "Yellow", "Red", "Blue"])
            visitor_hcp = st.number_input("Official Handicap Index:", min_value=0, max_value=54, value=12, step=1)
            comp_type = st.selectbox("Select Active Competition / Event:", KENYAN_COMPETITIONS)
            variant = st.selectbox("Select Planned Round Format:", ["Full 18 Holes", "Front 9 Only"])
            if st.button("Register Guest Competitor", type="primary"):
                if input_name.strip():
                    st.session_state.authorized = True
                    st.session_state.auth_type = "player"
                    st.session_state.player_id = 9000 + int(visitor_hcp)
                    st.session_state.player_name = f"{input_name.strip()} ({visitor_home})"
                    st.session_state.player_hcp = int(visitor_hcp)
                    st.session_state.playing_partners = partners_in.strip() or "Individual"
                    st.session_state.selected_course = reg_course
                    st.session_state.selected_tee = reg_tee
                    st.session_state.competition = comp_type
                    st.session_state.round_variant = variant
                    st.session_state.scorecard_submitted = False
                    st.session_state.hole_times = {}
                    st.rerun()
                else:
                    st.error("Please enter your name.")
        elif player_type == "Sponsor / Guest (Non-Playing)":
            st.info("Scorecard access is for playing competitors.")
        else:
            admin_pin = st.text_input("Enter Management PIN:", type="password")
            if st.button("Authenticate Admin Console", type="primary"):
                try:
                    target_pin = st.secrets["admin"]["pin"]
                except Exception:
                    target_pin = "1800"
                if admin_pin == target_pin:
                    st.session_state.authorized = True
                    st.session_state.auth_type = "Admin"
                    st.session_state.player_name = "System Administrator"
                    st.rerun()
                else:
                    st.error("Invalid PIN")
        conn.close()
        return

    if st.button("Logout / Reset"):
        st.session_state.authorized = False
        st.session_state.auth_type = None
        st.session_state.scorecard_submitted = False
        st.session_state.current_hole = 1
        st.session_state.hole_times = {}
        st.rerun()

    if st.session_state.auth_type == "Admin":
        st.header("FairwayIQ Executive Dashboard")
        st.info("Use the main Admin Console for full tools.")
        conn.close()
        return

    st.markdown(f"""
    <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:12px; padding:16px 20px; margin-bottom:20px;">
        <h3 style="margin:0 0 6px 0; color:#166534;">{display_name}</h3>
        <p style="margin:0; color:#374151;">
            <strong>HCP:</strong> {playing_hcp} |
            <strong>Playing:</strong> {st.session_state.selected_course} ({st.session_state.selected_tee}) |
            <strong>Event:</strong> {st.session_state.competition}<br>
            <strong>Team:</strong> {partners} | <strong>Format:</strong> {st.session_state.round_variant}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("scorecard_submitted"):
        st.success("Scorecard submitted to the live board.")
        st.subheader("Live Leaderboard")
        hist = pd.DataFrame()
        if os.path.exists(DB_FILE):
            try:
                hist = pd.read_csv(DB_FILE, engine="python", on_bad_lines="skip")
                hist.columns = hist.columns.str.strip()
                if hist.empty:
                    st.info("No scores yet.")
                else:
                    show = hist.sort_values(by="Score", ascending=True) if "Score" in hist.columns else hist
                    st.dataframe(show, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Could not load board: {e}")
        else:
            st.info("No leaderboard file yet.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Start New Round", type="primary", use_container_width=True):
                st.session_state.scorecard_submitted = False
                st.session_state.current_hole = 1
                st.session_state.hole_times = {}
                st.session_state.hole_scores = {h: ACTIVE_PARS.get(h, 4) for h in range(1, 19)}
                st.rerun()
        with c2:
            if st.button("Logout", use_container_width=True):
                st.session_state.authorized = False
                st.session_state.scorecard_submitted = False
                st.rerun()
        conn.close()
        return

    tab1, tab2 = st.tabs(["Live Scorecard", "Pre-Order to the Turn"])
    with tab1:
        current_h = st.session_state.current_hole
        front_only = st.session_state.round_variant == "Front 9 Only"
        active_limit = 9 if front_only else 18
        relevant = list(range(1, active_limit + 1))
        front_total = sum(st.session_state.hole_scores[h] for h in range(1, 10))
        back_total = sum(st.session_state.hole_scores[h] for h in range(10, 19)) if not front_only else 0
        gross = front_total + back_total
        front_par = sum(ACTIVE_PARS.get(h, 4) for h in range(1, 10))
        back_par = sum(ACTIVE_PARS.get(h, 4) for h in range(10, 19)) if not front_only else 0
        total_vs = gross - (front_par + back_par)
        hcp = playing_hcp / 2 if front_only else playing_hcp
        net = gross - hcp

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"<div style='background:#eff6ff;border:1px solid #93c5fd;border-radius:10px;padding:16px;text-align:center;'><h4 style='margin:0;color:#1e40af;'>FRONT 9</h4><p style='font-size:1.7rem;font-weight:700;margin:0;'>{front_total}</p></div>", unsafe_allow_html=True)
        with col_b:
            back_label = "Not played" if front_only else str(back_total)
            st.markdown(f"<div style='background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:16px;text-align:center;'><h4 style='margin:0;color:#92400e;'>BACK 9</h4><p style='font-size:1.7rem;font-weight:700;margin:0;'>{back_label}</p></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:18px;margin:16px 0;">
            <h4 style="margin:0 0 10px 0;color:#166534;">How did I do?</h4>
            <p>Gross: {gross} | Net: {int(net)} | vs Par: {"+" if total_vs > 0 else ""}{total_vs}</p>
        </div>
        """, unsafe_allow_html=True)

        def stamp_hole():
            if "hole_times" not in st.session_state:
                st.session_state.hole_times = {}
            st.session_state.hole_times[current_h] = datetime.now().strftime("%H:%M:%S")

        if current_h <= active_limit:
            st.subheader(f"Hole {current_h}")
            a, b, c = st.columns(3)
            a.info(f"Par {ACTIVE_PARS.get(current_h, 4)} | SI {ACTIVE_SI.get(current_h, current_h)}")
            b.metric("Your Score", st.session_state.hole_scores[current_h])
            keyed = st.session_state.get("hole_times", {}).get(current_h, "")
            c.caption(keyed if keyed else st.session_state.competition)
            score = st.number_input(
                "Enter Gross Strokes:", min_value=1, max_value=15,
                value=int(st.session_state.hole_scores[current_h]), key=f"score_{current_h}"
            )
            st.session_state.hole_scores[current_h] = score
            b1, b2, b3 = st.columns(3)
            with b1:
                if current_h > 1 and st.button("Previous", use_container_width=True):
                    st.session_state.current_hole -= 1
                    st.rerun()
            with b2:
                if current_h < active_limit:
                    if st.button("Save & Next", type="primary", use_container_width=True):
                        stamp_hole()
                        st.session_state.current_hole += 1
                        st.rerun()
                elif st.button("Finish Round", type="primary", use_container_width=True):
                    stamp_hole()
                    st.session_state.current_hole = 19
                    st.rerun()
            with b3:
                if current_h >= 9:
                    if st.button("Finish Front 9 / Go to Board", use_container_width=True):
                        stamp_hole()
                        st.session_state.round_variant = "Front 9 Only"
                        st.session_state.current_hole = 19
                        st.rerun()
        else:
            st.success(f"Round complete ({st.session_state.round_variant})")
            render_master_scorecard(
                display_name, playing_hcp, st.session_state.selected_course,
                st.session_state.selected_tee, st.session_state.competition,
                st.session_state.hole_scores, ACTIVE_PARS, st.session_state.round_variant,
                playing_partners=partners
            )
            markers = ["Choose marker...", "John Mwangi", "Alice Koech", "David Ochieng", "Martha Njeri", "Peter Kamau"]
            markers = [m for m in markers if m.lower() != display_name.lower()]
            with st.form("submit_form"):
                marker = st.selectbox("Select Official Marker:", markers)
                if st.form_submit_button("Submit to Live Leaderboard", type="primary", use_container_width=True):
                    if marker == "Choose marker...":
                        st.error("Please select a marker.")
                    else:
                        keyed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        play_day = datetime.now().strftime("%Y-%m-%d")
                        existing = pd.DataFrame()
                        if os.path.exists(DB_FILE):
                            try:
                                existing = pd.read_csv(DB_FILE, engine="python", on_bad_lines="skip")
                                existing.columns = existing.columns.str.strip()
                            except Exception:
                                existing = pd.DataFrame()
                        already = False
                        if not existing.empty and "MemberID" in existing.columns:
                            day_col = existing["PlayDate"].astype(str).str[:10] if "PlayDate" in existing.columns else ""
                            fmt_ok = existing["Format"].astype(str) == str(st.session_state.round_variant) if "Format" in existing.columns else True
                            already = (
                                (existing["MemberID"].astype(str) == str(st.session_state.player_id))
                                & (day_col == play_day)
                                & fmt_ok
                            ).any()
                        if already:
                            st.error("This player already posted a card today for this format. Double entry blocked.")
                        else:
                            new_row = pd.DataFrame([{
                                "MemberID": st.session_state.player_id,
                                "PlayerName": display_name,
                                "Course": st.session_state.selected_course,
                                "Handicap": hcp,
                                "Score": gross,
                                "Competition": st.session_state.competition,
                                "Team": partners,
                                "Format": st.session_state.round_variant,
                                "MarkerVerification": marker,
                                "PlayDate": keyed_at,
                                "KeyedAt": keyed_at
                            }])
                            os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)
                            if os.path.exists(DB_FILE):
                                new_row.to_csv(DB_FILE, mode="a", header=False, index=False)
                            else:
                                new_row.to_csv(DB_FILE, mode="w", header=True, index=False)
                            st.session_state.scorecard_submitted = True
                            st.rerun()

    with tab2:
        st.subheader("Pre-Order to the Turn")
        st.info("Order food while playing. It will be ready at the Halfway House.")

    conn.close()