import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
from core.scoring_engine import seed_seasonal_roster


def render_roster_uploader(season_id: str, conn: sqlite3.Connection):
    st.subheader("👥 Seasonal Roster & LCC Member Lifecycle Manager")
    st.markdown(
        "Manage Limuru Country Club member rosters, track lifecycle statuses "
        "(**Active**, **Dormant**, **Newly Joined**), and ingest bulk CSV/Excel exports."
    )

    # Ensure schema extension for member statuses exists
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE seasonal_roster ADD COLUMN member_status TEXT DEFAULT 'Active'")
            cursor.execute("ALTER TABLE seasonal_roster ADD COLUMN member_id TEXT")
            conn.commit()
        except Exception:
            pass  # Columns already exist

    # 1. Expected Template Layout Guide
    with st.expander("📊 View Expected Template & Column Mapping Layout"):
        template_df = pd.DataFrame({
            "Member_ID": ["LCC-101", "LCC-102", "LCC-103", "GUEST-901"],
            "Player_Name": ["Martha Njeri", "John Kamau", "Grace Wambui", "Alex Cooper"],
            "Handicap": [12.0, 18.4, 8.2, 24.0],
            "Member_Status": ["Active", "Dormant", "Newly Joined", "Active"]
        })
        st.dataframe(template_df, hide_index=True)
        st.caption("Flexible Headers Supported: `Member_ID`, `Player_Name` / `Name`, `Handicap` / `Hcp`, `Member_Status` / `Status`")

    # 2. Ingestion Source Switcher
    upload_method = st.radio(
        "Choose Roster Ingestion Method:",
        ["CSV / Excel File Upload", "Google Sheet Public LinkSync"],
        key="roster_upload_method_selector"
    )

    df_parsed = None

    # --- METHOD A: LOCAL FILE PIPELINE (CSV & EXCEL) ---
    if upload_method == "CSV / Excel File Upload":
        uploaded_file = st.file_uploader("Upload LCC Member Roster (.csv, .xlsx)", type=["csv", "xlsx", "xls"], key="roster_file_uploader_field")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_parsed = pd.read_csv(uploaded_file)
                else:
                    df_parsed = pd.read_excel(uploaded_file)
                st.success("✅ Member file parsed successfully.")
            except Exception as e:
                st.error(f"Error parsing file: {e}")

    # --- METHOD B: GOOGLE SHEET INTEGRATION PIPELINE ---
    elif upload_method == "Google Sheet Public LinkSync":
        sheet_url = st.text_input("Paste Public Google Sheet URL:", placeholder="https://docs.google.com/spreadsheets/d/...", key="roster_gsheet_url_field")

        if sheet_url:
            if "/edit" in sheet_url:
                csv_export_url = sheet_url.split("/edit")[0] + "/export?format=csv"
                try:
                    df_parsed = pd.read_csv(csv_export_url)
                    st.success("✅ Connected and synchronized with Google Sheets engine.")
                except Exception as e:
                    st.error(f"Failed to fetch remote spreadsheet data: Check link permissions. ({e})")

    # 3. Standardization & Preview Handler
    if df_parsed is not None:
        # Standardize column headers to lowercase strip
        df_parsed.columns = df_parsed.columns.str.strip().str.title()

        # Rename common aliases
        column_mapping = {
            "Name": "Player_Name",
            "Full_Name": "Player_Name",
            "Full Name": "Player_Name",
            "Hcp": "Handicap",
            "Handicap_Index": "Handicap",
            "Handicap Index": "Handicap",
            "Id": "Member_ID",
            "Member Id": "Member_ID",
            "Status": "Member_Status"
        }
        df_parsed = df_parsed.rename(columns=column_mapping)

        if "Player_Name" not in df_parsed.columns:
            st.error("Missing required column: `Player_Name` (or `Name`)")
            return

        if "Handicap" not in df_parsed.columns:
            df_parsed["Handicap"] = 28.0

        if "Member_Status" not in df_parsed.columns:
            df_parsed["Member_Status"] = "Active"

        if "Member_ID" not in df_parsed.columns:
            df_parsed["Member_ID"] = [f"LCC-{i+1001}" for i in range(len(df_parsed))]

        st.write("### Preview Parsed Member Roster Payload")
        st.dataframe(df_parsed[["Member_ID", "Player_Name", "Handicap", "Member_Status"]], use_container_width=True, hide_index=True)

        active_cnt = len(df_parsed[df_parsed["Member_Status"].str.lower() == "active"])
        dormant_cnt = len(df_parsed[df_parsed["Member_Status"].str.lower() == "dormant"])
        new_cnt = len(df_parsed[df_parsed["Member_Status"].str.lower().isin(["newly joined", "new"])])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Ingested", len(df_parsed))
        m2.metric("🟢 Active Members", active_cnt)
        m3.metric("💤 Dormant Members", dormant_cnt)
        m4.metric("✨ Newly Joined", new_cnt)

        if st.button("🚀 Push to Active Season Roster Database", key="roster_submit_db_btn", type="primary"):
            success = seed_seasonal_roster(season_id, df_parsed, conn)
            if success:
                st.balloons()
                st.success("🎉 Member database successfully updated! Active members are ready for tournament pairings and F&B billing.")
                st.rerun()
            else:
                st.error("Engine failed to seed database. Verify structure.")

    # 4. Live Member Directory & Interactive Status Editor
    st.markdown("---")
    st.subheader("📋 Currently Deployed LCC Member Roster")
    if conn is not None:
        try:
            query = """
                SELECT 
                    member_id AS [Member ID], 
                    player_name AS [Player Name], 
                    handicap AS [Handicap], 
                    COALESCE(member_status, 'Active') AS [Member Status],
                    checked_in AS [Check-In Status] 
                FROM seasonal_roster 
                WHERE season_id = ?
            """
            df_current = pd.read_sql_query(query, conn, params=(season_id,))
            if not df_current.empty:
                status_map = {0: "💤 Registered", 1: "🏌️ Checked-In", 2: "🏁 Round Finished"}
                df_current["Check-In Status"] = df_current["Check-In Status"].map(status_map)

                # Visual status badges
                def highlight_status(val):
                    if val == "Active":
                        return "color: #15803d; font-weight: bold;"
                    elif val == "Dormant":
                        return "color: #b91c1c; font-style: italic;"
                    elif "New" in str(val):
                        return "color: #1d4ed8; font-weight: bold;"
                    return ""

                st.dataframe(
                    df_current.style.map(highlight_status, subset=["Member Status"]),
                    use_container_width=True,
                    hide_index=True
                )

                # Single Member Quick Administrative Status Override
                st.markdown("#### 🛠️ Quick Administrative Status Override")
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    target_member_name = st.selectbox("Select Member to Update:", df_current["Player Name"].tolist())
                with col_m2:
                    new_status = st.selectbox("Assign New Status:", ["Active", "Dormant", "Newly Joined", "Suspended"])
                with col_m3:
                    st.write(" ")
                    st.write(" ")
                    if st.button("Update Member Status"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE seasonal_roster SET member_status = ? WHERE player_name = ? AND season_id = ?",
                            (new_status, target_member_name, season_id)
                        )
                        conn.commit()
                        st.success(f"Updated **{target_member_name}** to **{new_status}**!")
                        st.rerun()

            else:
                st.info("No members deployed for this season yet. Upload an LCC member file above to initialize.")
        except Exception as e:
            st.caption(f"Awaiting table sync sequence... ({e})")