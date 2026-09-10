# dashboard.py (Pro Trading Terminal Edition)
import streamlit as st
import pandas as pd
import concurrent.futures
from angel_connect import AngelLoader
from smart_logic import SmartAnalyzer
from token_manager import get_high_volume_stocks

# --- PAGE CONFIG & PRO CSS STYLING ---
st.set_page_config(page_title="Jitu Kumar Gupta - Terminal", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; height: 3em; }
        .signal-buy { color: #3fb950; font-weight: bold; font-size: 1.2rem; }
        .signal-sell { color: #f85149; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Jics Pro Terminal")
st.markdown("### Institutional-Grade Multi-Threaded Market Scanner")

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
    st.sidebar.success("API Connected ✅")
except Exception as e:
    st.sidebar.error(f"Login Failed: {e}")
    st.stop()

analyzer = SmartAnalyzer()
token_map = load_tokens()

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Terminal Settings")
st.sidebar.info(f"Tracking: **{len(token_map)}** Liquid Stocks")
max_threads = st.sidebar.slider("Scan Speed (Workers)", 5, 20, 10)

st.sidebar.markdown("---")
start_scan = st.sidebar.button('🔍 Scan Market Now', type="primary")

# --- MAIN INTERFACE ---
tab1, tab2 = st.tabs(["🚨 Live Trade Signals", "📊 Market Health & Info"])

with tab1:
    if start_scan:
        results = []
        stock_list = list(token_map.items())
        total_stocks = len(stock_list)
        
        st.write("### 🔄 Scanning Live Order Book & Price Action...")
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
                status_text.text(f"Progress: {completed_count}/{total_stocks} stocks analyzed...")
                
                res = future.result()
                if res:
                    results.append(res)
                    st.toast(f"🚨 Signal Found: {res['Stock']} ({res['Signal']})")

        status_text.text("Scan Completed Successfully!")
        progress_bar.progress(100)

        if results:
            st.success(f"🎯 Filtered {len(results)} High-Probability Setups!")
            
            res_df = pd.DataFrame(results)

            # --- TOP SUMMARY METRICS ---
            total_sigs = len(res_df)
            buy_cnt = len(res_df[res_df['Signal'] == 'BUY'])
            sell_cnt = len(res_df[res_df['Signal'] == 'SELL'])

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Signals", total_sigs)
            m2.metric("BUY Setups 🟢", buy_cnt)
            m3.metric("SELL Setups 🔴", sell_cnt)
            st.markdown("---")

            # --- CLEAN SUMMARY TABLE VIEW ---
            st.dataframe(
                res_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                    "Stop_Loss": st.column_config.NumberColumn("Stop Loss (₹)", format="₹%.2f"),
                    "Target": st.column_config.NumberColumn("Target (₹)", format="₹%.2f"),
                    "Risk_Per_Share": st.column_config.NumberColumn("Risk/Share (₹)", format="₹%.2f"),
                }
            )
            
            st.markdown("---")
            st.subheader("🛡️ Detailed Trade Cards")
            
            cols = st.columns(3)
            for idx, trade in enumerate(results):
                with cols[idx % 3]:
                    with st.container(border=True):
                        sig_class = "signal-buy" if trade['Signal'] == "BUY" else "signal-sell"
                        st.markdown(f"### {trade['Stock']}")
                        st.markdown(f"<span class='{sig_class}'>{trade['Signal']}</span> @ **₹{trade['Price']:.2f}**", unsafe_allow_html=True)
                        st.metric("Target", f"₹{trade['Target']:.2f}", delta=f"Risk: ₹{trade['Risk_Per_Share']:.2f}", delta_color="inverse")
                        st.markdown(f"🛑 **Stop Loss:** ₹{trade['Stop_Loss']:.2f}")
                        st.info(f"💡 **Logic:** {trade['Reason']}")
                        st.caption(f"⚡ **Status:** {trade['Build_Up']}")
        else:
            st.warning("No high-probability setups found right now. Market might be consolidating or sideways.")
    else:
        st.info("👈 Click **'Scan Market Now'** on the sidebar to trigger the live price action scanner.")

with tab2:
    st.subheader("📌 System & Risk Management Rules")
    st.markdown("""
    - **No Repainting:** Signals are generated strictly on closed candles (`iloc[-2]`) to prevent false triggers.
    - **Volume & Flow Analysis:** Real-time tracking of Long Build Up, Short Covering, Short Build Up, and Long Unwinding flows.
    - **Risk-Reward Ratio:** Fixed 1:2 risk-to-reward ratio managed via Average True Range (ATR).
    """)
    st.subheader("📈 Tracked Instruments")
    st.write(list(token_map.keys()))
