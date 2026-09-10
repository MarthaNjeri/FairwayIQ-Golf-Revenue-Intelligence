import streamlit as st


def render_gate_checkin():
    st.markdown("### Tournament Gate Check-in")
    st.caption("Select your registration type to unlock your portal view.")

    reg_type = st.radio(
        "Select Registration Type:",
        [
            "Club Member",
            "Visiting Player",
            "Sponsor / Guest (Non-Playing)",
            "Club Management / Admin"
        ],
        horizontal=True,
        index=0
    )

    st.markdown("---")

    kenyan_clubs = [
        "Limuru Country Club", "Karen Country Club", "Muthaiga Golf Club",
        "Sigona Golf Club", "Windsor Golf Hotel & Country Club",
        "Vet Lab Sports Club", "Thika Sports Club", "Nyali Golf & Country Club",
        "Nyanza Golf Club", "Eldoret Golf Club", "Golf Park", "Other"
    ]
    regions = ["Nairobi Region", "Rift Valley Region", "Coast Region", "Western Region", "Other"]
    tee_sets = ["White", "Yellow", "Red", "Blue", "Championship"]
    competitions = [
        "Club Nite (Stableford)", "Monthly Mug", "Medal Round",
        "KAGC Event", "Corporate Day", "Casual Round", "Other"
    ]
    round_formats = ["Full 18 Holes", "Front 9 Only"]

    def save_player(player_id, full_name, handicap, home_club, playing_club,
                    tee_set, competition, round_format, partners, reg_label):
        st.session_state.authorized = True
        st.session_state.auth_type = "player"
        st.session_state.player_id = player_id
        st.session_state.player_name = full_name
        st.session_state.player_hcp = handicap
        st.session_state.home_club = home_club
        st.session_state.playing_club = playing_club
        st.session_state.selected_course = playing_club
        st.session_state.tee_set = tee_set
        st.session_state.selected_tee = tee_set
        st.session_state.competition = competition
        st.session_state.round_format = round_format
        st.session_state.round_variant = "Front 9 Only" if "Front 9" in str(round_format) else "Full 18 Holes"
        st.session_state.playing_partners = partners.strip() or "Individual"
        st.session_state.registration_type = reg_label
        st.session_state.scorecard_submitted = False
        st.session_state.current_hole = 1
        st.rerun()

    if reg_type == "Club Member":
        col1, col2 = st.columns(2)
        with col1:
            member_id = st.text_input("Enter your Club Member ID:")
            full_name = st.text_input("Enter Registered Full Name:")
            handicap = st.number_input("Verified Club Handicap:", min_value=0.0, max_value=54.0, value=18.0, step=0.1)
        with col2:
            home_club = st.selectbox("Select Club Home:", kenyan_clubs)
            playing_club = st.selectbox("Select Golf Club Playing Today:", kenyan_clubs)
            tee_set = st.selectbox("Select Tee Set Played:", tee_sets)
        competition = st.selectbox("Select Active Competition / Event:", competitions)
        round_format = st.selectbox("Select Planned Round Format:", round_formats)
        partners = st.text_input("Playing partners / team (optional)", placeholder="e.g. Flight A")

        if st.button("Unlock Scorecard Portal", type="primary", use_container_width=True):
            if member_id.strip() and full_name.strip():
                save_player(
                    member_id.strip(), full_name.strip(), handicap,
                    home_club, playing_club, tee_set, competition, round_format,
                    partners, "Club Member"
                )
            else:
                st.warning("Please fill in Member ID and Full Name.")

    elif reg_type == "Visiting Player":
        visitor_name = st.text_input("Visitor Full Name:")
        col1, col2 = st.columns(2)
        with col1:
            home_club = st.selectbox("Select Your Official Home Club:", kenyan_clubs)
            region = st.selectbox("Select Playing Club Region:", regions)
        with col2:
            playing_club = st.selectbox("Select Venue Playing Today:", kenyan_clubs)
            tee_set = st.selectbox("Select Tee Set Played:", tee_sets)
        handicap = st.number_input("Official Handicap Index:", min_value=0.0, max_value=54.0, value=18.0, step=0.1)
        competition = st.selectbox("Select Active Competition / Event:", competitions)
        round_format = st.selectbox("Select Planned Round Format:", round_formats)
        partners = st.text_input("Playing partners / team (optional)", placeholder="e.g. Flight A")

        if st.button("Register Guest Competitor", type="primary", use_container_width=True):
            if visitor_name.strip():
                save_player(
                    "VISITOR", visitor_name.strip(), handicap,
                    home_club, playing_club, tee_set, competition, round_format,
                    partners, "Visiting Player"
                )
            else:
                st.warning("Please enter the Visitor Full Name.")

    elif reg_type == "Sponsor / Guest (Non-Playing)":
        st.info("Welcome. Scorecard access is for playing competitors. View the live leaderboard in the lounge.")

    else:
        st.markdown("### Executive Portal Verification")
        admin_pin = st.text_input("Enter Management Credentials / PIN:", type="password")
        if st.button("Authenticate Admin Console", type="primary"):
            try:
                target_pin = st.secrets["admin"]["pin"]
            except Exception:
                target_pin = "1800"
            if admin_pin == target_pin:
                st.session_state.admin_authenticated = True
                st.session_state.auth_type = "admin"
                st.success("Admin access granted.")
                st.rerun()
            else:
                st.error("Invalid Management Credentials.")

    if st.session_state.get("authorized") and st.session_state.get("auth_type") == "player":
        st.markdown("---")
        st.success("Registration Successful!")
        st.markdown(f"""
        <div style="background-color:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:22px 24px;">
            <h4 style="margin-top:0;color:#166534;">Player Summary</h4>
            <p><strong>Name:</strong> {st.session_state.player_name}</p>
            <p><strong>Member / ID:</strong> {st.session_state.player_id}</p>
            <p><strong>Handicap:</strong> {st.session_state.get('player_hcp', 'N/A')}</p>
            <p><strong>Home Club:</strong> {st.session_state.get('home_club', 'N/A')}</p>
            <p><strong>Playing Today:</strong> {st.session_state.get('playing_club', 'N/A')}</p>
            <p><strong>Competition:</strong> {st.session_state.get('competition', 'N/A')}</p>
            <p><strong>Format:</strong> {st.session_state.get('round_variant', 'N/A')}</p>
            <p><strong>Team:</strong> {st.session_state.get('playing_partners', 'Individual')}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Continue to Digital Scorecard", type="primary", use_container_width=True):
            st.rerun()