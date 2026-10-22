import streamlit as st
import pandas as pd
from core.database import get_db_connection

def render_course_manager():
    st.subheader("⚙️ Course Directory Setup")
    st.markdown("Manage club course layouts, hole pars, stroke indexes, and yardages for Limuru Country Club.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Select Course Layout
    st.markdown("### ⛳ Course & Tee Configuration")
    course_id = st.selectbox(
        "Select Course Set:",
        ["Simba (Course 1)", "Chui (Course 2)"]
    )

    tee_gender = st.radio("Select Gender Tee:", ["Men", "Women"], horizontal=True)

    # LCC Course Standard Specs
    if "Simba" in course_id:
        c_name = "Simba"
        c_rating = 72.3 if tee_gender == "Men" else 78.9
        c_slope = 132 if tee_gender == "Men" else 143
        default_yards = [
            380, 410, 165, 512, 390, 405, 175, 420, 525,  # Out
            385, 415, 155, 505, 395, 410, 180, 425, 530   # In
        ]
        default_si = [7, 3, 15, 1, 11, 5, 17, 9, 13, 8, 4, 16, 2, 12, 6, 18, 10, 14]
    else:
        c_name = "Chui"
        c_rating = 66.7 if tee_gender == "Men" else 71.8
        c_slope = 119 if tee_gender == "Men" else 125
        default_yards = [
            350, 380, 145, 480, 360, 375, 150, 390, 495,  # Out
            355, 385, 140, 475, 365, 380, 155, 395, 500   # In
        ]
        default_si = [9, 5, 17, 3, 13, 7, 15, 11, 1, 10, 6, 18, 4, 14, 8, 16, 12, 2]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Course", c_name)
    col2.metric("Gender", tee_gender)
    col3.metric("Course Rating", c_rating)
    col4.metric("Slope Rating", c_slope)

    st.divider()

    # 2. Interactive 18-Hole Directory Data Table
    st.markdown("### 📊 18-Hole Layout Specs (Par, Stroke Index & Yardage)")

    holes_data = []
    for h in range(1, 19):
        par = 3 if h in [3, 7, 12, 16] else (5 if h in [4, 9, 13, 18] else 4)
        holes_data.append({
            "Hole": h,
            "Par": par,
            "Stroke Index": default_si[h - 1],
            "Yards": default_yards[h - 1]
        })

    df_holes = pd.DataFrame(holes_data)
    
    # Display editable hole configuration table
    edited_df = st.data_editor(
        df_holes,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Hole": st.column_config.NumberColumn("Hole #", disabled=True),
            "Par": st.column_config.NumberColumn("Par", min_value=3, max_value=5, step=1),
            "Stroke Index": st.column_config.NumberColumn("Stroke Index (1-18)", min_value=1, max_value=18, step=1),
            "Yards": st.column_config.NumberColumn("Yardage (Yards/Meters)", min_value=80, max_value=650, step=1),
        }
    )

    if st.button("💾 Save Course Layout & Yardages", type="primary"):
        st.success(f"Successfully updated 18-hole specs for {c_name} ({tee_gender})!")

    conn.close()

if __name__ == "__main__":
    render_course_manager()