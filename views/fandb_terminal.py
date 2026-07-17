import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

def render_fb_pos(POS_FILE, LEADERBOARD_FILE):
    st.title("🍔 FairwayIQ Clubhouse F&B Terminal")
    st.caption("Predictive Golf Hospitality Billing, COGS Control & Turn Sync Engine")

    STANDARD_GATE_FEE = 2000  # Baseline prepaid credit initialized at gate check-in

    # --- CLUBHOUSE STEWARDS / STAFF ---
    WAITERS = ["Grace Wambui", "Rodrick Tabu", "Albert Karimi", "Martha Njeri", "Jane Wangari"]

    # --- ADVANCED MENU MATRIX (Price, COGS, and Live Stock Count) ---
    MENU_ITEMS = {
        "⌨️ Manual Custom Amount": {"price": 0, "cogs": 0, "stock": 999},
        "🍺 Tusker / White Cap Lager": {"price": 400, "cogs": 180, "stock": 48},  # High risk item
        "🥪 Club Sandwich & French Fries": {"price": 850, "cogs": 280, "stock": 15},
        "🥟 Halfway House Samosas (Pair)": {"price": 300, "cogs": 90, "stock": 8},   # Low stock warning target
        "☕ Premium House Coffee": {"price": 350, "cogs": 70, "stock": 100},
        "🥩 19th Hole Mixed Grill Platter": {"price": 2200, "cogs": 850, "stock": 12},
        "💧 Mayer's Mineral Water (500ml)": {"price": 150, "cogs": 40, "stock": 60}
    }

    # --- SESSION STATE STOCK TRACKER (Ensures real-time auto-depletion is persistent) ---
    if "live_stock" not in st.session_state:
        st.session_state.live_stock = {item: specs["stock"] for item, specs in MENU_ITEMS.items()}

    # --- FIXED DATABASE SCHEMA ENGINE (Resolved missing ServedBy column mismatch) ---
    if not os.path.exists(POS_FILE):
        os.makedirs(os.path.dirname(POS_FILE), exist_ok=True)
        pd.DataFrame(columns=[
            "TransactionID", "MemberID", "PlayerName", "PointOfSale",
            "AmountKES", "COGS", "PlayDate", "PlayTime", "BillingType",
            "ServedBy", "FulfilmentPoint", "PickupETA"
        ]).to_csv(POS_FILE, index=False)

    # --- REAL-TIME LOW STOCK ALERTS ---
    st.subheader("⚠️ Live Inventory & Waste Alerts")
    low_stock_found = False
    alert_cols = st.columns(3)
    alert_idx = 0
    for item, stock_count in st.session_state.live_stock.items():
        if stock_count <= 10 and item != "⌨️ Manual Custom Amount":
            with alert_cols[alert_idx % 3]:
                st.error(f"🚨 **Critical Stock Alert:** {item} is running low ({stock_count} remaining)!")
            alert_idx += 1
            low_stock_found = True
    if not low_stock_found:
        st.success("🟢 All multi-outlet high-demand inventory balances are currently optimal.")

    st.markdown("---")
    st.subheader("🛒 Log New Member Purchase")

    # --- DYNAMIC PLAYER CAPTURE ---
    player_mapping = {}
    if os.path.exists(LEADERBOARD_FILE):
        try:
            df_players = pd.read_csv(LEADERBOARD_FILE)
            if not df_players.empty:
                for _, row in df_players.iterrows():
                    p_id = row.get('MemberID', '9999')
                    p_name = row.get('PlayerName', 'Unknown Player')
                    p_hcp = row.get('Handicap', 'N/A')
                    p_comp = row.get('Competition', 'Active Event')
                    
                    player_mapping[f"{p_name} (ID: {p_id})"] = {
                        "MemberID": p_id,
                        "PlayerName": p_name,
                        "Handicap": p_hcp,
                        "Competition": p_comp
                    }
        except Exception:
            pass

    player_mapping["Walk-in Guest / Casual Chit (ID: 9999)"] = {
        "MemberID": 9999,
        "PlayerName": "Walk-in Guest",
        "Handicap": "N/A",
        "Competition": "Casual Lounge Sale"
    }

    selected_player_label = st.selectbox("Select Active Player at Counter:", list(player_mapping.keys()))
    
    player_data = player_mapping[selected_player_label]
    target_id = player_data['MemberID']
    target_name = player_data['PlayerName']
    target_hcp = player_data['Handicap']
    target_comp = player_data['Competition']
    
    previous_spend = 0
    if os.path.exists(POS_FILE):
        try:
            df_pos_calc = pd.read_csv(POS_FILE)
            if not df_pos_calc.empty:
                df_pos_calc['MemberID'] = df_pos_calc['MemberID'].astype(str)
                previous_spend = df_pos_calc[df_pos_calc['MemberID'] == str(target_id)]['AmountKES'].sum()
        except Exception:
            pass
    
    current_net_folio = STANDARD_GATE_FEE - previous_spend
    
    st.info(f"📋 **Verified Player Profile:** {target_name} | **Hcp:** {target_hcp} | **Active Field:** {target_comp}")
    
    if target_id == 9999:
        st.info("ℹ️ **Casual Sale Mode:** Direct payments or guest chits. No prepaid gate allowance applies.")
    elif current_net_folio >= 0:
        st.success(f"💰 **Prepaid Gate Allowance Remaining:** KES {current_net_folio:,} (Initial Gate Credit: KES {STANDARD_GATE_FEE:,} | Already Spent: KES {previous_spend:,})")
    else:
        st.warning(f"⚠️ **Authorized Credit Tab Active (Overdraft):** KES {abs(current_net_folio):,} Over Limit (Initial Gate Credit: KES {STANDARD_GATE_FEE:,} | Total Spent: KES {previous_spend:,})")
    
    # --- POS INTERACTIVE SELECTIONS ---
    col_pos1, col_pos2 = st.columns(2)
    with col_pos1:
        pos_location = st.selectbox("Clubhouse Terminal Point:", ["Main Restaurant", "Halfway House", "Terrace Bar", "Pro Shop"])
        billing_type = st.radio("Account Allocation Type:", ["Direct Member Folio", "Caddy Voucher", "Guest Chit"], horizontal=True)
        steward_name = st.selectbox("Served By (Steward Name):", WAITERS)
        
        fulfilment_point = st.selectbox(
            "📍 Order Fulfillment Point:",
            ["Serve Immediately", "Pick-up Hole 4 Tee", "Ready at Hole 9 Turn", "Hole 10 Tee", "19th Hole Lounge Table"]
        )
        
    with col_pos2:
        selected_item = st.selectbox("Quick-Select Touchscreen Menu:", list(MENU_ITEMS.keys()))
        
        # Check live stock limit
        available_qty = st.session_state.live_stock[selected_item]
        if available_qty <= 0:
            st.error(f"❌ {selected_item} is Out of Stock! Please clear and select an alternative menu item.")
            allow_billing = False
        else:
            allow_billing = True
            
        menu_default_value = MENU_ITEMS[selected_item]["price"] if MENU_ITEMS[selected_item]["price"] > 0 else 1500
        
        spend_amount = st.number_input(
            "Transaction Amount (KES):",
            min_value=10,
            max_value=100000,
            value=int(menu_default_value),
            step=50,
            key="pos_spend_value_field"
        )
        
        # Calculate Predictive Pickup ETA based on Golf Pace-of-Play (approx 15 mins per hole)
        eta_minutes = 0
        if "Hole 4" in fulfilment_point:
            eta_minutes = 60
        elif "Hole 9" in fulfilment_point:
            eta_minutes = 135
        elif "Hole 10" in fulfilment_point:
            eta_minutes = 150
        calculated_eta = datetime.now() + timedelta(minutes=eta_minutes)
        eta_display = calculated_eta.strftime('%H:%M') if eta_minutes > 0 else "Instant / Live"
        st.metric("🕒 Est. Pace-of-Play Prep Time", eta_display, help="Calculated based on standard 15 min-per-hole pace from tee sheet.")

    if st.button("Confirm & Post to Member Folio", type="primary", disabled=not allow_billing):
        txn_id = f"TXN-{int(datetime.timestamp(datetime.now()))}"
        
        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M:%S')

        # Dynamically evaluate COGS based on selection
        item_cogs = MENU_ITEMS[selected_item]["cogs"] if selected_item in MENU_ITEMS else (spend_amount * 0.4)
        
        new_txn = pd.DataFrame([{
            "TransactionID": txn_id,
            "MemberID": target_id,
            "PlayerName": target_name,
            "PointOfSale": pos_location,
            "AmountKES": spend_amount,
            "COGS": item_cogs,
            "PlayDate": current_date,
            "PlayTime": current_time,
            "BillingType": billing_type,
            "ServedBy": steward_name,
            "FulfilmentPoint": fulfilment_point,
            "PickupETA": eta_display
        }])
        
        if os.path.exists(POS_FILE):
            new_txn.to_csv(POS_FILE, mode='a', header=False, index=False)
        else:
            new_txn.to_csv(POS_FILE, mode='w', header=True, index=False)
        
        # Deduct stock on successful transaction
        if selected_item != "⌨️ Manual Custom Amount":
            st.session_state.live_stock[selected_item] -= 1
        
        if target_id == 9999:
            st.success(f"🎉 Posted KES {spend_amount:,} Walk-In transaction successfully. Served by {steward_name}.")
        else:
            projected_balance = current_net_folio - spend_amount
            if projected_balance >= 0:
                st.success(f"🎉 Posted KES {spend_amount:,} to {target_name}'s prepaid footprint. Prep Location: {fulfilment_point}.")
            else:
                st.warning(f"🚀 Limit Exceeded! Overdraft posted to {target_name}'s credit tab. ETA: {eta_display}.")
        
        st.rerun()

    # --- 2. EXECUTIVE INSIGHT ---
    st.markdown("---")
    st.subheader("📈 Live Tournament Hospitality & COGS Analytics")
    if os.path.exists(POS_FILE):
        try:
            df_pos = pd.read_csv(POS_FILE)
            if not df_pos.empty:
                # Type corrections
                df_pos['AmountKES'] = pd.to_numeric(df_pos['AmountKES'], errors='coerce')
                df_pos['COGS'] = pd.to_numeric(df_pos['COGS'], errors='coerce').fillna(df_pos['AmountKES'] * 0.35)
                
                total_rev = df_pos['AmountKES'].sum()
                total_cogs = df_pos['COGS'].sum()
                gross_profit = total_rev - total_cogs
                gp_margin = (gross_profit / total_rev * 100) if total_rev > 0 else 0
                
                # Commercial Metrics Display
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Total Hospitality Revenue", f"KES {total_rev:,.0f}")
                col_m2.metric("Total Food/Bev COGS", f"KES {total_cogs:,.0f}")
                col_m3.metric("Gross Profit Yield", f"KES {gross_profit:,.0f}")
                col_m4.metric("GP Margin %", f"{gp_margin:.1f}%")
                
                # Dynamic performance charts (Steward Leaderboard)
                st.write("### 🏆 Steward Performance Leaderboard")
                steward_totals = df_pos.groupby("ServedBy")["AmountKES"].sum().reset_index()
                steward_totals = steward_totals.sort_values(by="AmountKES", ascending=False)
                st.bar_chart(data=steward_totals, x="ServedBy", y="AmountKES")

                # Color-highlighted fulfillment priorities (Addressing on-course friction)
                st.write("### 📜 Real-time Fulfilment Queue")
                queue_df = df_pos[["TransactionID", "PlayerName", "FulfilmentPoint", "PickupETA", "AmountKES", "ServedBy"]].sort_values(by="TransactionID", ascending=False)
                
                # Flag priority on-course turnovers
                def color_turn_point(val):
                    if "Hole 9" in str(val) or "Hole 10" in str(val):
                        return 'background-color: #ffcccc; font-weight: bold; color: black;'  # Red alert for pace-of-play prep
                    elif "Hole 4" in str(val):
                        return 'background-color: #ffe5cc; color: black;' # Light orange warning
                    return ''

                styled_queue = queue_df.style.map(color_turn_point, subset=["FulfilmentPoint"])
                st.dataframe(styled_queue, use_container_width=True)
            else:
                st.info("Awaiting initial terminal data log.")
        except Exception as e:
            st.info(f"Awaiting initial terminal data log: {e}")
    else:
        st.info("Awaiting initial terminal data log.")