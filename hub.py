import streamlit as st

st.set_page_config(page_title="FairwayIQ Launchpad", page_icon="⛳", layout="centered")

st.title("🦅 FairwayIQ Operations Master Launchpad")
st.markdown("### **Limuru Country Club — Core Infrastructure Gateway**")
st.write("Select a dedicated operations portal below to open its fully isolated environment.")

st.markdown("---")

# Layout as 3 premium dashboard cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🏌️‍♂️\n**Player Portal**")
    st.caption("Hole-by-hole live score entry and player peer-verification framework.")
    # Points directly to your isolated scorecard port
    st.link_button("Open Scorecard", "http://localhost:8501", type="primary", use_container_width=True)

with col2:
    st.markdown("### 🍔\n**Clubhouse F&B**")
    st.caption("Point-of-sale terminal for hospitality billing and event consumption tracking.")
    # Points directly to your isolated F&B port
    st.link_button("Open F&B Terminal", "http://localhost:8505", type="primary", use_container_width=True)

with col3:
    st.markdown("### 🏆\n**Leaderboard**")
    st.caption("Live spectator leaderboard, championship podium display, and sponsor engine.")
    # Points directly to your isolated tournament port
    st.link_button("Open TV Display", "http://localhost:8503", type="primary", use_container_width=True)

st.markdown("---")
st.caption("🔒 FairwayIQ System Node: Active | Multi-Port Isolation Engine Running smoothly.")