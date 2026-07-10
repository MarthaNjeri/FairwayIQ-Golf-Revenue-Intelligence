import streamlit as st
import pandas as pd
from datetime import datetime
import os

def render_fb_pos(POS_FILE, LEADERBOARD_FILE):
    st.title("🍔 FairwayIQ Clubhouse F&B Terminal")
    st.caption("Live Event Hospitality Billing & Inventory Sync Engine")

    STANDARD_GATE_FEE = 2000  # Baseline prepaid credit initialized at gate check-in

    # --- COMMERCIAL CLUBHOUSE POS MENU MATRIX ---
    MENU_ITEMS = {
        "⌨️ Manual Custom Amount": 0,
        "🍺 Tusker / White Cap Lager": 400,
        "🥪 Club Sandwich & French Fries": 850,
        "🥟 Halfway House Samosas (Pair)": 300,
        "☕  Premium House Coffee": 350,
        "🥩 19th Hole Mixed Grill Platter": 2200,
        "💧 Mayer's Mineral Water (500ml)": 150
    }

    # --- DATABASE SCHEMA ENGINE ---
    if not os.path.exists(POS_FILE):
        pd.DataFrame(columns=[
            "TransactionID", "MemberID", "PlayerName", 
            "PointOfSale", "AmountKES", "PlayDate", "PlayTime", "BillingType"
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
                player_data = player_mapping[selected_player_label]
                target_id = player_data['MemberID']
                target_name = player_data['PlayerName']
                target_hcp = player_data.get('Handicap', 'N/A')
                target_comp = player_data.get('Competition', 'Active Event')
                
                # --- REAL-TIME LEDGER BALANCE CALCULATION ---
                previous_spend = 0
                if os.path.exists(POS_FILE):
                    df_pos_calc = pd.read_csv(POS_FILE)
                    if not df_pos_calc.empty:
                        # Sum all previous spending rows logged under this player's MemberID
                        previous_spend = df_pos_calc[df_pos_calc['MemberID'] == target_id]['AmountKES'].sum()
                
                # Calculate remaining balance relative to their gate entry fee baseline footprint
                current_net_folio = STANDARD_GATE_FEE - previous_spend
                
                # Display informational profile context box to the server/cashier
                st.info(f"📋 **Verified Player Profile:** {target_name} | **Hcp:** {target_hcp} | **Active Field:** {target_comp}")
                
                # Visual Ledger Status Alert System for the Waiter
                if current_net_folio >= 0:
                    st.success(f"💰 **Prepaid Gate Allowance Remaining:** KES {current_net_folio:,} (Initial Gate Credit: KES {STANDARD_GATE_FEE:,} | Already Spent: KES {previous_spend:,})")
                else:
                    st.warning(f"⚠️ **Authorized Credit Tab Active (Overdraft):** KES {abs(current_net_folio):,} Over Limit (Initial Gate Credit: KES {STANDARD_GATE_FEE:,} | Total Spent: KES {previous_spend:,})")
                
                # --- POS INTERACTIVE SELECTIONS ---
                col_pos1, col_pos2 = st.columns(2)
                with col_pos1:
                    pos_location = st.selectbox("Clubhouse Terminal Point:", ["Main Restaurant", "Halfway House", "Terrace Bar", "Pro Shop"])
                    billing_type = st.radio("Account Allocation Type:", ["Direct Member Folio", "Caddy Voucher", "Guest Chit"], horizontal=True)
                
                with col_pos2:
                    selected_item = st.selectbox("Quick-Select Touchscreen Menu:", list(MENU_ITEMS.keys()))
                    
                    # Dynamically calculate default price based on dropdown selection
                    menu_default_value = MENU_ITEMS[selected_item] if MENU_ITEMS[selected_item] > 0 else 1500
                    
                    spend_amount = st.number_input(
                        "Transaction Amount (KES):", 
                        min_value=10, 
                        max_value=100000, 
                        value=int(menu_default_value), 
                        step=50,
                        key="pos_spend_value_field"
                    )
                    
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
                        "PlayTime": current_time,
                        "BillingType": billing_type
                    }])
                    
                    new_txn.to_csv(POS_FILE, mode='a', header=False, index=False)
                    
                    # Dynamic success toast alerts that verify if it went to credit tab
                    projected_balance = current_net_folio - spend_amount
                    if projected_balance >= 0:
                        st.success(f"🎉 Posted KES {spend_amount:,} via [{billing_type}] to {target_name}'s prepaid ledger footprint.")
                    else:
                        st.warning(f"🚀 Limit Exceeded! Posted KES {spend_amount:,} via [{billing_type}] to {target_name}'s accounts receivable credit tab.")
                    
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