import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st


def fetch_live_nairobi_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-1.2921&longitude=36.8219&current_weather=true"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return response.json()["current_weather"]["temperature"]
    except Exception:
        pass
    return 22.0


def load_pos(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        df.columns = df.columns.str.strip()
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    if "AmountKES" not in df.columns and "Amount" in df.columns:
        df["AmountKES"] = df["Amount"]
    if "AmountKES" not in df.columns:
        df["AmountKES"] = 0
    if "COGS" not in df.columns:
        df["COGS"] = pd.to_numeric(df["AmountKES"], errors="coerce") * 0.35
    if "ServedBy" not in df.columns:
        df["ServedBy"] = "Unknown"
    if "MemberID" not in df.columns:
        df["MemberID"] = ""
    if "PlayerName" not in df.columns:
        df["PlayerName"] = ""
    df["AmountKES"] = pd.to_numeric(df["AmountKES"], errors="coerce").fillna(0)
    df["COGS"] = pd.to_numeric(df["COGS"], errors="coerce").fillna(df["AmountKES"] * 0.35)
    return df


def render_fb_pos(POS_FILE, LEADERBOARD_FILE):
    st.title("FairwayIQ Clubhouse F&B Terminal")
    st.caption("Predictive Golf Hospitality Billing, Weather Sync & Turn Queue Control")

    STANDARD_GATE_FEE = 2000
    WAITERS = ["Grace Wambui", "Rodrick Tabu", "Albert Karimi", "Martha Njeri", "Jane Wangari"]

    live_temp = fetch_live_nairobi_weather()
    is_hot_day = live_temp >= 26.0

    if is_hot_day:
        st.warning(f"High Temperature Alert: {live_temp}°C. Cold drinks prioritised.")
        MENU_ITEMS = {
            "Tusker / White Cap Lager": {"price": 400, "cogs": 180, "stock": 48},
            "Mayer's Mineral Water (500ml)": {"price": 150, "cogs": 40, "stock": 60},
            "Manual Custom Amount": {"price": 0, "cogs": 0, "stock": 999},
            "Club Sandwich & French Fries": {"price": 850, "cogs": 280, "stock": 15},
            "Halfway House Samosas (Pair)": {"price": 300, "cogs": 90, "stock": 8},
            "Premium House Coffee": {"price": 350, "cogs": 70, "stock": 100},
            "19th Hole Mixed Grill Platter": {"price": 2200, "cogs": 850, "stock": 12}
        }
    else:
        st.success(f"Weather Sync: {live_temp}°C. Normal menu active.")
        MENU_ITEMS = {
            "Manual Custom Amount": {"price": 0, "cogs": 0, "stock": 999},
            "Premium House Coffee": {"price": 350, "cogs": 70, "stock": 100},
            "Halfway House Samosas (Pair)": {"price": 300, "cogs": 90, "stock": 8},
            "Tusker / White Cap Lager": {"price": 400, "cogs": 180, "stock": 48},
            "Club Sandwich & French Fries": {"price": 850, "cogs": 280, "stock": 15},
            "19th Hole Mixed Grill Platter": {"price": 2200, "cogs": 850, "stock": 12},
            "Mayer's Mineral Water (500ml)": {"price": 150, "cogs": 40, "stock": 60}
        }

    if "live_stock" not in st.session_state:
        st.session_state.live_stock = {item: specs["stock"] for item, specs in MENU_ITEMS.items()}

    if not os.path.exists(POS_FILE):
        os.makedirs(os.path.dirname(POS_FILE) or ".", exist_ok=True)
        pd.DataFrame(columns=[
            "TransactionID", "MemberID", "PlayerName", "PointOfSale",
            "AmountKES", "COGS", "PlayDate", "PlayTime", "BillingType",
            "ServedBy", "FulfilmentPoint", "PickupETA"
        ]).to_csv(POS_FILE, index=False)

    st.subheader("Live Inventory & Waste Alerts")
    low_stock_found = False
    alert_cols = st.columns(3)
    alert_idx = 0
    for item, stock_count in st.session_state.live_stock.items():
        if stock_count <= 10 and item != "Manual Custom Amount":
            with alert_cols[alert_idx % 3]:
                st.error(f"Critical Stock: {item} ({stock_count} left)")
            alert_idx += 1
            low_stock_found = True
    if not low_stock_found:
        st.success("Inventory balances are currently optimal.")

    st.markdown("---")
    st.subheader("Log New Member Purchase")

    player_mapping = {}
    if os.path.exists(LEADERBOARD_FILE):
        try:
            df_players = pd.read_csv(LEADERBOARD_FILE, engine="python", on_bad_lines="skip")
            df_players.columns = df_players.columns.str.strip()
            if not df_players.empty:
                for _, row in df_players.iterrows():
                    p_id = row.get("MemberID", "9999")
                    p_name = row.get("PlayerName", "Unknown Player")
                    p_hcp = row.get("Handicap", "N/A")
                    p_comp = row.get("Competition", "Active Event")
                    p_team = row.get("Team", "Individual")
                    player_mapping[f"{p_name} | {p_team} (ID: {p_id})"] = {
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
    target_id = player_data["MemberID"]
    target_name = player_data["PlayerName"]
    target_hcp = player_data["Handicap"]
    target_comp = player_data["Competition"]

    df_pos_calc = load_pos(POS_FILE)
    previous_spend = 0
    if not df_pos_calc.empty:
        df_pos_calc["MemberID"] = df_pos_calc["MemberID"].astype(str)
        previous_spend = df_pos_calc[df_pos_calc["MemberID"] == str(target_id)]["AmountKES"].sum()

    current_net_folio = STANDARD_GATE_FEE - previous_spend
    st.info(f"Verified Player: {target_name} | Hcp: {target_hcp} | Field: {target_comp}")
    if str(target_id) == "9999":
        st.info("Casual Sale Mode. No prepaid gate allowance.")
    elif current_net_folio >= 0:
        st.success(f"Prepaid remaining: KES {current_net_folio:,.0f}")
    else:
        st.warning(f"Overdraft: KES {abs(current_net_folio):,.0f}")

    col_pos1, col_pos2 = st.columns(2)
    with col_pos1:
        pos_location = st.selectbox("Clubhouse Terminal Point:", ["Main Restaurant", "Halfway House", "Terrace Bar", "Pro Shop"])
        billing_type = st.radio("Account Allocation Type:", ["Direct Member Folio", "Caddy Voucher", "Guest Chit"], horizontal=True)
        steward_name = st.selectbox("Served By (Steward Name):", WAITERS)
        fulfilment_point = st.selectbox(
            "Order Fulfillment Point:",
            ["Serve Immediately", "Pick-up Hole 4 Tee", "Ready at Hole 9 Turn", "Hole 10 Tee", "19th Hole Lounge Table"]
        )
    with col_pos2:
        selected_item = st.selectbox("Quick-Select Menu:", list(MENU_ITEMS.keys()))
        available_qty = st.session_state.live_stock.get(selected_item, 999)
        allow_billing = available_qty > 0
        if not allow_billing:
            st.error(f"{selected_item} is out of stock.")
        menu_default_value = MENU_ITEMS[selected_item]["price"] if MENU_ITEMS[selected_item]["price"] > 0 else 1500
        spend_amount = st.number_input(
            "Transaction Amount (KES):",
            min_value=10, max_value=100000, value=int(menu_default_value), step=50
        )
        eta_minutes = 0
        if "Hole 4" in fulfilment_point:
            eta_minutes = 60
        elif "Hole 9" in fulfilment_point:
            eta_minutes = 135
        elif "Hole 10" in fulfilment_point:
            eta_minutes = 150
        eta_display = (datetime.now() + timedelta(minutes=eta_minutes)).strftime("%H:%M") if eta_minutes > 0 else "Instant / Live"
        st.metric("Est. Pace-of-Play Prep Time", eta_display)

    if st.button("Confirm & Post to Member Folio", type="primary", disabled=not allow_billing):
        now = datetime.now()
        item_cogs = MENU_ITEMS[selected_item]["cogs"] if selected_item in MENU_ITEMS else (spend_amount * 0.4)
        new_txn = pd.DataFrame([{
            "TransactionID": f"TXN-{int(datetime.timestamp(now))}",
            "MemberID": target_id,
            "PlayerName": target_name,
            "PointOfSale": pos_location,
            "AmountKES": spend_amount,
            "COGS": item_cogs,
            "PlayDate": now.strftime("%Y-%m-%d"),
            "PlayTime": now.strftime("%H:%M:%S"),
            "BillingType": billing_type,
            "ServedBy": steward_name,
            "FulfilmentPoint": fulfilment_point,
            "PickupETA": eta_display
        }])
        if os.path.exists(POS_FILE):
            new_txn.to_csv(POS_FILE, mode="a", header=False, index=False)
        else:
            new_txn.to_csv(POS_FILE, mode="w", header=True, index=False)
        if selected_item != "Manual Custom Amount" and selected_item in st.session_state.live_stock:
            st.session_state.live_stock[selected_item] -= 1
        st.success(f"Posted KES {spend_amount:,} for {target_name}. Prep: {fulfilment_point}.")
        st.rerun()

    st.markdown("---")
    st.subheader("Live Tournament Hospitality & COGS Analytics")
    df_pos = load_pos(POS_FILE)
    if df_pos.empty:
        st.info("Awaiting initial terminal data log.")
        return

    total_rev = df_pos["AmountKES"].sum()
    total_cogs = df_pos["COGS"].sum()
    gross_profit = total_rev - total_cogs
    gp_margin = (gross_profit / total_rev * 100) if total_rev > 0 else 0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Hospitality Revenue", f"KES {total_rev:,.0f}")
    m2.metric("Total Food/Bev COGS", f"KES {total_cogs:,.0f}")
    m3.metric("Gross Profit Yield", f"KES {gross_profit:,.0f}")
    m4.metric("GP Margin %", f"{gp_margin:.1f}%")

    st.write("### Steward Performance Leaderboard")
    steward_totals = df_pos.groupby("ServedBy")["AmountKES"].sum().reset_index()
    st.bar_chart(data=steward_totals, x="ServedBy", y="AmountKES")

    st.write("### Real-time Fulfilment Queue")
    queue_cols = [c for c in ["TransactionID", "PlayerName", "FulfilmentPoint", "PickupETA", "AmountKES", "ServedBy"] if c in df_pos.columns]
    queue_df = df_pos[queue_cols].sort_values(by=queue_cols[0], ascending=False)

    def color_turn_point(val):
        if "Hole 9" in str(val) or "Hole 10" in str(val):
            return "background-color: #ffcccc; font-weight: bold; color: black;"
        if "Hole 4" in str(val):
            return "background-color: #ffe5cc; color: black;"
        return ""

    if "FulfilmentPoint" in queue_df.columns:
        st.dataframe(queue_df.style.map(color_turn_point, subset=["FulfilmentPoint"]), use_container_width=True)
    else:
        st.dataframe(queue_df, use_container_width=True)