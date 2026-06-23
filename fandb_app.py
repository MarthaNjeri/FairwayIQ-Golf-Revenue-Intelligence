import streamlit as st
import pandas as pd
from datetime import datetime
import os

# CONFIGURED FOR IFRAME INTEGRATION: Centered layout prevents double scrollbars in hub.py
st.set_page_config(page_title="FairwayIQ F&B Terminal", page_icon="🍔", layout="centered")

st.title("🍔 FairwayIQ Clubhouse F&B Terminal")
st.caption("Live Event Hospitality Billing & Inventory Sync Engine")

POS_FILE = "data/pos_transactions.csv"
LEADERBOARD_FILE = "data/live_leaderboard.csv"

# --- DATABASE SCHEMA ENGINE ---
# Ensures all reporting dimensions are ready for your Power BI data modeling layers
if not os.path.exists(POS_FILE):
    pd.DataFrame(columns=[
        "TransactionID", "MemberID", "PlayerName", 
        "PointOfSale", "AmountKES", "PlayDate", "PlayTime"
    ]).to_csv(POS_FILE, index=False)

# 1. LIVE EXTRACTION: Fetch active players currently checked in
st.subheader("🛒 Log New Member Purchase")
if os.path.exists(LEADERBOARD_FILE):
    try:
        df_players = pd.read_csv(LEADERBOARD_FILE)
        if not df_players.empty:
            # Create a clean data mapping of all verified players in the field
            player_mapping = {f"{row['PlayerName']} (ID: {row['MemberID']})": row for _, row in df_players.iterrows()}
            selected_player_label = st.selectbox("Select Active Player at Counter:", list(player_mapping.keys()))
            
            # --- METADATA LINKAGE BRIDGE ---
            # Extract player profiles established at the gate/scorecard portal
            player_data = player_mapping[selected_player_label]
            target_id = player_data['MemberID']
            target_name = player_data['PlayerName']
            target_hcp = player_data.get('Handicap', 'N/A')
            target_comp = player_data.get('Competition', 'Active Event')
            
            # Display informational profile context box to the server/cashier
            st.info(f"📋 **Verified Player Profile:** {target_name} | **Hcp:** {target_hcp} | **Active Field:** {target_comp}")
            
            col1, col2 = st.columns(2)
            with col1:
                pos_location = st.selectbox("Clubhouse Terminal Point:", ["Main Restaurant", "Halfway House", "Terrace Bar", "Pro Shop"])
            with col2:
                spend_amount = st.number_input("Transaction Amount (KES):", min_value=10, max_value=100000, value=1500, step=50)
                
            if st.button("Confirm & Post to Member Folio", type="primary"):
                txn_id = f"TXN-{int(datetime.timestamp(datetime.now()))}"
                
                now = datetime.now()
                current_date = now.strftime('%Y-%m-%d')
                current_time = now.strftime('%H:%M:%S')

                new_txn = pd.DataFrame([{
                    "TransactionID": txn_id,
                    "MemberID": target_id,
                    "PlayerName": target_name,
                    "PointOfSale": pos_location,
                    "AmountKES": spend_amount,
                    "PlayDate": current_date,
                    "PlayTime": current_time
                }])
                
                new_txn.to_csv(POS_FILE, mode='a', header=False, index=False)
                st.success(f"🎉 Posted KES {spend_amount:,} to {target_name}'s live event profile!")
                st.rerun()
        else:
            st.info("Waiting for active players to check in at the gate scorecard portal.")
    except Exception as e:
        st.info("Syncing with tournament database context...")
else:
    st.info("No active tournament database detected yet.")

# 2. EXECUTIVE INSIGHT: Live Kitchen & Bar Revenue Stream
st.markdown("---")
st.subheader("📈 Live Tournament Auxiliary Revenue Log")

if os.path.exists(POS_FILE):
    try:
        df_pos = pd.read_csv(POS_FILE)
        if not df_pos.empty:
            c1, c2 = st.columns(2)
            c1.metric("Total Tournament Spend (Auxiliary)", f"KES {df_pos['AmountKES'].sum():,}")
            c2.metric("Total Sales Volume", f"{len(df_pos)} Receipts")
            
            # Show the structured logs ordered by date and time
            st.dataframe(df_pos.sort_values(by=["PlayDate", "PlayTime"], ascending=False), use_container_width=True)
    except:
        st.info("Awaiting initial terminal data log.")