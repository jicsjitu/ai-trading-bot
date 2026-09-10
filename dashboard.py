# dashboard.py (Clean Ultra-Minimalist Terminal)
import streamlit as st
import pandas as pd
import concurrent.futures
from angel_connect import AngelLoader
from smart_logic import SmartAnalyzer
from token_manager import get_high_volume_stocks

# --- PAGE CONFIG & PRO CSS STYLING ---
st.set_page_config(page_title="Jics Terminal", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stButton>button { border-radius: 6px; font-weight: bold; height: 3em; }
        .signal-buy { color: #3fb950; font-weight: bold; font-size: 1.2rem; }
        .signal-sell { color: #f85149; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- CACHING LOGIC ---
@st.cache_resource
def get_angel_loader():
    return AngelLoader()

@st.cache_data
def load_tokens():
    return get_high_volume_stocks()

# Initialize Logic
try:
    loader = get_angel_loader()
except Exception as e:
    st.error(f"Login Failed: {e}")
    st.stop()

analyzer = SmartAnalyzer()
token_map = load_tokens()

# --- TOP CONTROL BAR (No Title, Only Clean Controls) ---
col_head1, col_head2, col_head3 = st.columns([3, 2, 2])
with col_head1:
    st.caption(f"Tracking: **{len(token_map)}** Liquid Stocks | API: **Connected ✅**")

with col_head2:
    max_threads = st.slider("Scan Speed", 5, 20, 10, label_visibility="collapsed")

with col_head3:
    start_scan = st.button('🔍 Scan Market Now', type="primary", use_container_width=True)

st.markdown("---")

# --- MAIN EXECUTION ON SCAN ---
if start_scan:
    results = []
    stock_list = list(token_map.items())
    total_stocks = len(stock_list)
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    def scan_single_stock(item):
        name, token = item
        try:
            df = loader.fetch_candle_data(token, name, interval="FIVE_MINUTE")
            if not df.empty:
                trade_setup = analyzer.analyze_stock(df, name)
                if trade_setup:
                    return trade_setup
        except Exception:
            pass
        return None

    completed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_stock = {executor.submit(scan_single_stock, stock): stock for stock in stock_list}
        
        for future in concurrent.futures.as_completed(future_to_stock):
            completed_count += 1
            progress_bar.progress(completed_count / total_stocks)
            status_text.text(f"Scanning... {completed_count}/{total_stocks}")
            
            res = future.result()
            if res:
                results.append(res)
                st.toast(f"🚨 Signal Found: {res['Stock']} ({res['Signal']})")

    status_text.empty()
    progress_bar.empty()

    if results:
        res_df = pd.DataFrame(results)

        # --- REORDER COLUMNS (Build_Up before Reason) ---
        cols_order = ['Stock', 'Signal', 'Price', 'Target', 'Stop_Loss', 'Risk_Per_Share', 'Build_Up', 'Reason']
        cols_order = [c for c in cols_order if c in res_df.columns]
        res_df = res_df[cols_order]

        # --- TOP SUMMARY METRICS ---
        total_sigs = len(res_df)
        buy_cnt = len(res_df[res_df['Signal'] == 'BUY'])
        sell_cnt = len(res_df[res_df['Signal'] == 'SELL'])

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Signals", total_sigs)
        m2.metric("BUY Setups 🟢", buy_cnt)
        m3.metric("SELL Setups 🔴", sell_cnt)
        st.markdown("---")

        # --- COLOR HIGHLIGHTING FOR TABLE ---
        def highlight_flows(val):
            if val in ['BUY', 'Long Build Up 🟢', 'Short Covering ⚡']:
                return 'color: #3fb950; font-weight: bold; background-color: rgba(63, 185, 80, 0.15);'
            elif val in ['SELL', 'Short Build Up 🔴', 'Long Unwinding ⚠️']:
                return 'color: #f85149; font-weight: bold; background-color: rgba(248, 81, 73, 0.15);'
            return ''

        # --- SUMMARY TABLE VIEW ---
        st.dataframe(
            res_df.style.map(highlight_flows, subset=['Signal', 'Build_Up']),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Stock": "Stock Name",
                "Signal": "Signal Type",
                "Price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "Target": st.column_config.NumberColumn("Target (₹)", format="₹%.2f"),
                "Stop_Loss": st.column_config.NumberColumn("Stop Loss (₹)", format="₹%.2f"),
                "Risk_Per_Share": st.column_config.NumberColumn("Risk/Share (₹)", format="₹%.2f"),
                "Build_Up": "Flow Status",
                "Reason": "Trigger Reason"
            }
        )
        
        st.markdown("---")
        
        # --- DETAILED TRADE CARDS ---
        cols = st.columns(3)
        for idx, trade in enumerate(results):
            with cols[idx % 3]:
                with st.container(border=True):
                    sig_class = "signal-buy" if trade['Signal'] == "BUY" else "signal-sell"
                    st.markdown(f"### {trade['Stock']}")
                    st.markdown(f"<span class='{sig_class}'>{trade['Signal']}</span> @ **₹{trade['Price']:.2f}**", unsafe_allow_html=True)
                    st.metric("Target", f"₹{trade['Target']:.2f}", delta=f"Risk: ₹{trade['Risk_Per_Share']:.2f}", delta_color="inverse")
                    st.markdown(f"🛑 **Stop Loss:** ₹{trade['Stop_Loss']:.2f}")
                    st.caption(f"⚡ **Status:** {trade['Build_Up']}")
                    st.info(f"💡 **Logic:** {trade['Reason']}")
    else:
        st.warning("No high-probability setups found right now.")
else:
    st.info("👆 Click **'Scan Market Now'** above to start scanning.")
