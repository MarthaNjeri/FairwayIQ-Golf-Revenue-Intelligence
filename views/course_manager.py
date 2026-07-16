import streamlit as st
import pandas as pd
from core.database import get_db_connection

def render_course_manager():
    st.title("⛳ Dynamic Course Layout Manager")
    st.subheader("Register Clubs & Configure 18-Hole Par/Stroke Indexes")

    tab1, tab2 = st.tabs(["📝 Add New Course", "🔍 View & Edit Course Layouts"])

    # ==========================================
    # TAB 1: ADD NEW COURSE
    # ==========================================
    with tab1:
        st.header("Create a New Club Layout")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            course_name = st.text_input("Golf Club Name", placeholder="e.g., Muthaiga Golf Club")
        with col_info2:
            location = st.text_input("Location / County", placeholder="e.g., Nairobi")

        col_tee1, col_tee2 = st.columns(2)
        with col_tee1:
            tee_color = st.selectbox("Select Tee Set", ["White", "Blue", "Red", "Yellow"])
        with col_tee2:
            st.info("💡 Pro Tip: Championship tees are typically Blue, Men's are White, and Ladies' are Red.")

        st.markdown("---")
        st.write("### 🎛️ Enter 18-Hole Layout Details")
        st.caption("Double-click on any cell to edit the Par (3, 4, or 5) and Stroke Index (1 to 18) for each hole.")

        # Initialize a default 18-hole dataframe for editing
        default_data = {
            "Hole": list(range(1, 19)),
            "Par": [4] * 18,
            "Stroke Index": list(range(1, 19))
        }
        df_template = pd.DataFrame(default_data)

        # Let the user interactively edit pars and indexes in a spreadsheet style
        edited_df = st.data_editor(
            df_template,
            key="course_editor_grid",
            num_rows="fixed",
            hide_index=True,
            column_config={
                "Hole": st.column_config.NumberColumn("Hole Number ⛳", disabled=True),
                "Par": st.column_config.NumberColumn("Hole Par (3-5)", min_value=3, max_value=5, required=True),
                "Stroke Index": st.column_config.NumberColumn("Stroke Index (1-18)", min_value=1, max_value=18, required=True)
            }
        )

        if st.button("Save Course & Layout Specs", type="primary"):
            if not course_name:
                st.error("Please enter a valid Golf Club Name.")
            elif len(set(edited_df["Stroke Index"])) != 18:
                # Golf rules requirement: Each stroke index from 1 to 18 must be uniquely allocated once
                st.error("❌ Invalid Stroke Indexes: You must allocate unique ratings from 1 to 18 without duplicates.")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    # 1. Insert global course profile
                    cursor.execute("""
                        INSERT INTO golf_courses (course_name, location)
                        VALUES (?, ?)
                    """, (course_name, location))
                    course_id = cursor.lastrowid

                    # 2. Insert individual hole specs
                    for _, row in edited_df.iterrows():
                        cursor.execute("""
                            INSERT INTO course_holes (course_id, tee_color, hole_number, par, stroke_index)
                            VALUES (?, ?, ?, ?, ?)
                        """, (course_id, tee_color, int(row['Hole']), int(row['Par']), int(row['Stroke Index'])))
                    
                    conn.commit()
                    st.success(f"🎉 Successfully created {course_name} ({tee_color} Tees) with custom Pars & Stroke Indexes!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"Failed to write layout specs to SQLite: {e}")
                finally:
                    conn.close()

    # ==========================================
    # TAB 2: VIEW & EDIT EXISTING COURSES
    # ==========================================
    with tab2:
        st.header("Registered Course Directory")
        
        conn = get_db_connection()
        courses_df = pd.read_sql_query("SELECT * FROM golf_courses", conn)
        
        if courses_df.empty:
            st.info("No courses are currently configured in the database.")
            conn.close()
        else:
            selected_course_name = st.selectbox("Select Club", courses_df['course_name'].unique())
            
            # Fetch tees available for selected course
            selected_course_id = int(courses_df.loc[courses_df['course_name'] == selected_course_name, 'course_id'].values[0])
            
            tees_df = pd.read_sql_query("""
                SELECT DISTINCT tee_color FROM course_holes WHERE course_id = ?
            """, conn, params=(selected_course_id,))
            
            if tees_df.empty:
                st.warning("No tee configurations found for this course.")
            else:
                selected_tee = st.selectbox("Select Tee Set Profile", tees_df['tee_color'])
                
                # Fetch complete dynamic hole configuration
                holes_layout_df = pd.read_sql_query("""
                    SELECT hole_number AS Hole, par AS Par, stroke_index AS [Stroke Index]
                    FROM course_holes
                    WHERE course_id = ? AND tee_color = ?
                    ORDER BY hole_number ASC
                """, conn, params=(selected_course_id, selected_tee))
                
                # Display dynamic metrics
                total_par = holes_layout_df['Par'].sum()
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric(label="Total Course Par", value=int(total_par))
                with col_metric2:
                    st.metric(label="Active Configuration Profile", value=f"{selected_course_name} ({selected_tee} Tees)")
                
                st.dataframe(holes_layout_df.T, use_container_width=True)
            
            conn.close()