import streamlit as st
from core.handicap_engine import get_lcc_course_options, calculate_player_course_handicap, validate_player_eligibility

def render():
    st.subheader("⛳ LCC Course Handicap Conversion & Eligibility Desk")
    st.markdown("Use this official World Handicap System (WHS) module to calculate course handicaps and verify tournament eligibility for Limuru Country Club configurations.")

    # 1. Course / Tee Configuration Selector
    course_options = get_lcc_course_options()
    selected_course_key = st.selectbox(
        "Select Course & Tee Configuration", 
        list(course_options.keys())
    )
    
    config = course_options[selected_course_key]
    
    # Display Course Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Course", config["course_name"])
    col2.metric("Gender", config["gender"])
    col3.metric("Course Rating", config["rating"])
    col4.metric("Slope Rating", config["slope"])
    
    st.divider()

    # 2. Player Input Section
    st.markdown("### Player Details & Handicap Lookup")
    col_a, col_b = st.columns(2)
    
    with col_a:
        player_id = st.text_input("Player ID / Membership No.", value="LCC-001")
        player_name = st.text_input("Golfer Name", value="Jane Doe")
        
    with col_b:
        handicap_index = st.number_input(
            "Handicap Index", 
            min_value=-5.0, 
            max_value=54.0, 
            value=12.4, 
            step=0.1,
            help="Enter the player's official WHS Handicap Index (ranges from -5.0 to 54.0)."
        )

    if st.button("Calculate Course Handicap & Verify Eligibility", type="primary"):
        # Run Calculations
        course_handicap = calculate_player_course_handicap(selected_course_key, handicap_index)
        eligibility = validate_player_eligibility(player_id, handicap_index)
        
        st.divider()
        
        # Results Section
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.markdown("#### 🎯 Conversion Result")
            if course_handicap is not None:
                st.success(f"**Course Handicap: {course_handicap}**")
                st.caption(f"Based on Handicap Index {handicap_index} for {selected_course_key}.")
            else:
                st.error("Could not find a matching bracket for this Handicap Index.")
                
        with res_col2:
            st.markdown("#### 🛡️ Eligibility Check")
            if eligibility["is_eligible"]:
                st.success(f"Status: **Eligible** ({eligibility['membership_status']})")
                st.info(eligibility["status_message"])
            else:
                st.warning(f"Status: **Requires Review**")
                st.error(eligibility["status_message"])

if __name__ == "__main__":
    render()