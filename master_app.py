import streamlit as st

# 1. SETUP THE MASTER PORTAL CONFIGURATION
st.set_page_config(page_title="FairwayIQ Master Workspace", page_icon="⛳", layout="wide")

# 2. CREATE THE MASTER DROPDOWN SELECTOR IN THE SIDEBAR
st.sidebar.title("🏁 FairwayIQ Hub")
app_choice = st.sidebar.selectbox(
    "Switch App Environment:",
    ["🏌️ Player Scorecard Portal", "🍔 Clubhouse fandb Terminal", "🏆 Tournament Leaderboard Monitor"]
)
st.sidebar.markdown("---")
st.sidebar.caption("⚡ Centralized Enterprise Routing Engine")

# 3. DYNAMIC CLONED EXECUTION PIPELINE
# This reads your standalone files and executes them exactly as they are written.

if app_choice == "🏌️ Player Scorecard Portal":
    try:
        with open("scorecard_app.py", "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, globals())
    except FileNotFoundError:
        st.error("❌ 'scorecard_app.py' not found in this folder path.")

elif app_choice == "🍔 Clubhouse fandb Terminal":
    try:
        with open("fandb_app.py", "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, globals())
    except FileNotFoundError:
        st.error("❌ 'fandb_app.py' file not found in this folder path.")

elif app_choice == "🏆 Tournament Leaderboard Monitor":
    try:
        with open("tournament_app.py", "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, globals())
    except FileNotFoundError:
        st.error("❌ 'tournament_app.py' not found in this folder path.")