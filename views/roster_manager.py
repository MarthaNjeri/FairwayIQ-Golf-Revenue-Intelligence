import streamlit as st
import pandas as pd
import sqlite3
from core.scoring_engine import seed_seasonal_roster

def render_roster_uploader(season_id: str, conn: sqlite3.Connection):
    st.subheader("👥 Seasonal Roster Initialization")
    st.markdown("Populate the current season's active player list using a flat file format or external sheet integration.")
    
    # 1. Provide an expected schema guideline to prevent formatting ingestion failures
    with st.expander("📊 View Expected Template Layout"):
        template_df = pd.DataFrame({
            "Player_Name": ["John Doe", "Jane Smith", "Alex Cooper"],
            "Handicap": [14.2, 8.5, 22.1]
        })
        st.dataframe(template_df, hide_index=True)
        st.caption("Ensure file headers match exactly: `Player_Name` and `Handicap`")

    # 2. Select Ingestion Switch Node
    upload_method = st.radio(
        "Choose Roster Ingestion Method:", 
        ["CSV File Upload", "Google Sheet Public LinkSync"],
        key="roster_upload_method_selector"
    )
    
    df_parsed = None

    # --- METHOD A: LOCAL CSV PIPELINE ---
    if upload_method == "CSV File Upload":
        uploaded_file = st.file_uploader("Upload Seasonal Player Sheet (.csv)", type=["csv"], key="roster_file_uploader_field")
        if uploaded_file is not None:
            try:
                df_parsed = pd.read_csv(uploaded_file)
                st.success("✅ File read successfully.")
            except Exception as e:
                st.error(f"Error parsing file: {e}")

    # --- METHOD B: GOOGLE SHEET INTEGRATION PIPELINE ---
    elif upload_method == "Google Sheet Public LinkSync":
        sheet_url = st.text_input("Paste Public Google Sheet URL:", placeholder="https://docs.google.com/spreadsheets/d/...", key="roster_gsheet_url_field")
        
        if sheet_url:
            # Transform standard share link into a direct clean CSV export format endpoint
            if "/edit" in sheet_url:
                csv_export_url = sheet_url.split("/edit")[0] + "/export?format=csv"
                try:
                    df_parsed = pd.read_csv(csv_export_url)
                    st.success("✅ Connected and synchronized with Google Sheets engine.")
                except Exception as e:
                    st.error(f"Failed to fetch remote spreadsheet data: Check link sharing permissions. ({e})")

    # 3. Action Execution Handler Block
    if df_parsed is not None:
        st.write("### Preview Parsed Player Ingestion List")
        st.dataframe(df_parsed, use_container_width=True, hide_index=True)
        
        # Verify row bounds match target client criteria (e.g. up to ~30 players per season)
        st.info(f"Roster count payload detected: **{len(df_parsed)}** players.")
        
        if st.button("🚀 Push to Active Season Roster Database", key="roster_submit_db_btn", type="primary"):
            success = seed_seasonal_roster(season_id, df_parsed, conn)
            if success:
                st.balloons()
                st.success("🎉 Roster successfully configured and deployed! These players are now live for match assignments and tournament check-in.")
                st.rerun()
            else:
                st.error("Engine failed to seed database. Verify your data headers match `Player_Name` and `Handicap` exactly.")

    # --- 4. LIVE AUDIT: SHOW CURRENT ACTIVE ROSTER FROM SQLITE ---
    st.markdown("---")
    st.subheader("📋 Currently Deployed Season Roster")
    if conn is not None:
        try:
            query = "SELECT player_name AS [Player Name], handicap AS [Handicap], checked_in AS [Status Flag] FROM seasonal_roster WHERE season_id = ?"
            df_current = pd.read_sql_query(query, conn, params=(season_id,))
            if not df_current.empty:
                # Map internal database flag variables to user-friendly text categories
                status_map = {0: "💤 Registered", 1: "🏌️ Checked-In", 2: "🏁 Round Finished"}
                df_current["Status Flag"] = df_current["Status Flag"].map(status_map)
                st.dataframe(df_current, use_container_width=True, hide_index=True)
            else:
                st.info("No players deployed for this season yet. Use the tool configuration workspace above to seed the initial roster.")
        except Exception as e:
            st.caption(f"Awaiting table initialization sync sequence... ({e})")