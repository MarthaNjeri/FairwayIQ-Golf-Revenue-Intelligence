import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import get_db_connection

def render_command_center():
    conn = get_db_connection()
    
    # Fetch metrics for KPIs and Queues
    try:
        failed_logins_df = pd.read_sql("SELECT COUNT(*) as cnt FROM access_audit_logs WHERE status = 'FAILED'", conn)
        failed_logins_count = failed_logins_df['cnt'].iloc[0] if not failed_logins_df.empty else 0
        
        roster_df = pd.read_sql("SELECT COUNT(*) as cnt, SUM(checked_in) as checked FROM seasonal_roster", conn)
        total_players = roster_df['cnt'].iloc[0] if not roster_df.empty else 0
        checked_players = roster_df['checked'].iloc[0] if not roster_df.empty else 0
        if checked_players is None: checked_players = 0

        matches_df = pd.read_sql("SELECT COUNT(*) as cnt, SUM(CASE WHEN match_status = 'Completed' THEN 1 ELSE 0 END) as completed FROM matches", conn)
        total_matches = matches_df['cnt'].iloc[0] if not matches_df.empty else 0
        completed_matches = matches_df['completed'].iloc[0] if not matches_df.empty else 0
        if completed_matches is None: completed_matches = 0
    except Exception:
        failed_logins_count, total_players, checked_players, total_matches, completed_matches = 0, 0, 0, 0, 0

    conn.close()

    # Calculate pending work queues count
    pending_matches = total_matches - completed_matches
    work_queues_count = (1 if failed_logins_count > 0 else 0) + (1 if pending_matches > 0 else 0) + (1 if checked_players < total_players else 0)
    
    # Formatted dynamic date
    current_date_str = datetime.datetime.now().strftime("%A, %d %B %Y")

    # Dynamic top banner styling matching ERP screenshot
    st.markdown(f"""
        <div style="
            background-color: #1e4275;
            border-radius: 16px;
            padding: 24px 32px;
            color: #ffffff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <div>
                <h1 style="margin: 0 0 6px 0; font-size: 1.85rem; font-weight: 700; color: #ffffff;">
                    Good day, Martha
                </h1>
                <p style="margin: 0; font-size: 0.92rem; color: #cbd5e1;">
                    No approvals waiting for you · 
                    <span style="
                        background-color: #3b82f6; 
                        color: #ffffff; 
                        padding: 2px 8px; 
                        border-radius: 12px; 
                        font-weight: 700; 
                        font-size: 0.85rem;
                        margin: 0 4px;
                    ">{work_queues_count}</span> 
                    work queues need attention.
                </p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-bottom: 4px;">
                    {current_date_str}
                </div>
                <div style="font-size: 0.8rem; letter-spacing: 0.5px; color: #94a3b8; text-transform: uppercase; font-weight: 600;">
                    LIMURU COUNTRY CLUB · administrator
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Layout Split: Left for "Waiting For You", Right for "Your Areas" KPIs
    col_queue, col_kpis = st.columns([1, 2])

    with col_queue:
        st.markdown("### 📥 WAITING FOR YOU")
        st.caption("Action queues requiring committee attention")
        
        with st.container(border=True):
            if failed_logins_count > 0:
                st.error(f"🔴 **{failed_logins_count} Failed PIN / Security Alerts** detected in audit logs.")
            else:
                st.success("🟢 No unauthorized access attempts recorded.")

            st.info(f"👥 **{checked_players} / {total_players} Players Checked In** for today's match day.")

            st.warning(f"⚠️ **{pending_matches} Match Play Duels** still pending scorecard submission.")

    with col_kpis:
        st.markdown("### 📊 YOUR AREAS")
        st.caption("Real-time summary of club pillars")

        # KPI Grid Cards
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            with st.container(border=True):
                st.metric("Tournament Status", f"{completed_matches}/{total_matches}", "Completed Matches")
        with kpi2:
            with st.container(border=True):
                st.metric("Active Roster", f"{checked_players} Checked In", f"Out of {total_players}")
        with kpi3:
            with st.container(border=True):
                st.metric("Security Status", f"{failed_logins_count} Alerts", "Audit Monitored", delta_color="inverse")

        kpi4, kpi5, kpi6 = st.columns(3)
        with kpi4:
            with st.container(border=True):
                st.metric("Course Setup", "Limuru (White)", "18 Holes Active")
        with kpi5:
            with st.container(border=True):
                st.metric("WHS Engine", "Active Brackets", "Simba & Chui Loaded")
        with kpi6:
            with st.container(border=True):
                st.metric("PWA Offline Sync", "Operational", "Last-Write-Wins Ready")

    st.markdown("---")

    # Visual Analytics at a Glance
    st.markdown("### 📈 VISUAL ANALYTICS & OPERATIONAL INSIGHTS")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Match Play Completion Progress")
        chart_data = pd.DataFrame({
            "Status": ["Completed", "Pending"],
            "Count": [completed_matches, max(0, total_matches - completed_matches)]
        })
        fig_match = px.pie(chart_data, names="Status", values="Count", hole=0.4, color_discrete_sequence=["#16a34a", "#ca8a04"])
        fig_match.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250)
        st.plotly_chart(fig_match, use_container_width=True)

    with chart_col2:
        st.subheader("Handicap Distribution Spread")
        conn = get_db_connection()
        hcp_df = pd.read_sql("SELECT handicap FROM seasonal_roster", conn)
        conn.close()
        
        if not hcp_df.empty:
            fig_hcp = px.histogram(hcp_df, x="handicap", nbins=10, color_discrete_sequence=["#1e4275"])
            fig_hcp.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250, xaxis_title="Handicap", yaxis_title="Player Count")
            st.plotly_chart(fig_hcp, use_container_width=True)
        else:
            st.info("No handicap data available.")