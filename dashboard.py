# dashboard.py (Pro Trading Terminal Edition)
import streamlit as st
import time
import pandas as pd
import concurrent.futures
from angel_connect import AngelLoader
from smart_logic import SmartAnalyzer
from token_manager import get_high_volume_stocks

# --- PAGE CONFIG & PRO CSS STYLING ---
st.set_page_config(page_title="Jitu Kumar Gupta", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; height: 3em; }
        .metric-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
        .signal-buy { color: #3fb950; font-weight: bold; font-size: 1.2rem; }
        .signal-sell { color: #f85149; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Jics")
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
            st.balloons()
            st.success(f"🎯 AI Filtered {len(results)} High-Probability Setups!")
            
            # Summary Table View
            res_df = pd.DataFrame(results)
            def highlight_signal(val):
                color = '#3fb950' if val == 'BUY' else '#f85149'
                return f'color: {color}; font-weight: bold'

            st.dataframe(
                res_df.style.map(highlight_signal, subset=['Signal']),
                use_container_width=True
            )
            
            st.markdown("---")
            st.subheader("🛡️ Detailed Trade Setups")
            
            cols = st.columns(3)
            for idx, trade in enumerate(results):
                with cols[idx % 3]:
                    with st.container(border=True):
                        sig_class = "signal-buy" if trade['Signal'] == "BUY" else "signal-sell"
                        st.markdown(f"### {trade['Stock']}")
                        st.markdown(f"<span class='{sig_class}'>{trade['Signal']}</span> @ **₹{trade['Price']}**", unsafe_allow_html=True)
                        st.metric("Target", f"₹{trade['Target']}", delta=f"Risk: ₹{trade['Risk_Per_Share']}", delta_color="inverse")
                        st.markdown(f"🛑 **Stop Loss:** ₹{trade['Stop_Loss']}")
                        st.info(f"💡 **Logic:** {trade['Reason']}")
                        st.caption(f"⚡ **Status:** {trade['Build_Up']}")
        else:
            st.warning("No high-probability setups found right now. Market might be consolidating or sideways.")
            st.caption("Tip: Try scanning during high volatility hours (9:30 AM - 11:00 AM or 1:30 PM - 2:30 PM).")
    else:
        st.info("👈 Click **'Scan Market Now'** on the sidebar to trigger the AI anti-fake breakout scanner.")

with tab2:
    st.subheader("📌 System & Risk Management Rules")
    st.markdown("""
    - **No Repainting:** Signals are generated strictly on closed candles (`iloc[-2]`) to prevent false triggers.
    - **Anti-Fake Breakout:** Body-to-wick ratio and volume spike filters are actively blocking retail traps.
    - **Risk-Reward Ratio:** Fixed 1:2 risk-to-reward ratio managed via Average True Range (ATR).
    """)
    st.subheader("📈 Tracked Instruments")
    st.write(list(token_map.keys()))
