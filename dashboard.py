# dashboard.py (Corrected & Integrated)
import streamlit as st
import time
import pandas as pd
from angel_connect import AngelLoader
from smart_logic import SmartAnalyzer
from token_manager import get_high_volume_stocks # YEH IMPORT ZAROORI HAI

# Page Config
st.set_page_config(page_title="Pro AI Trader Agent", layout="wide")

st.title("🚀 AI Trading Agent (Smart Money Logic)")
st.markdown("### Analyzing Indian Market - Sector & Price Action")

# --- CACHING LOGIC ---
@st.cache_resource
def get_angel_loader():
    return AngelLoader()

@st.cache_data
def load_tokens():
    # Ab hum hardcoded dictionary nahi, balki dynamic list use karenge
    return get_high_volume_stocks()

# Initialize Logic
try:
    loader = get_angel_loader()
    st.sidebar.success("API Connected ✅")
except Exception as e:
    st.error(f"Login Failed: {e}")
    st.stop()

analyzer = SmartAnalyzer()

# --- SIDEBAR & SCAN BUTTON ---
token_map = load_tokens()
st.sidebar.info(f"Tracking {len(token_map)} Liquid Stocks")

# Scan Speed Control
scan_delay = st.sidebar.slider("Scan Speed (Seconds)", 0.5, 2.0, 1.0)

col1, col2 = st.columns([1, 4])
with col1:
    start_scan = st.button('🔍 Scan Market Now', type="primary")

if start_scan:
    results = []
    
    # Progress Bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    stock_list = list(token_map.items())
    total_stocks = len(stock_list)
    
    st.markdown("---")
    st.write("### 📊 Live Analysis Results")

    for i, (name, token) in enumerate(stock_list):
        status_text.text(f"Scanning ({i+1}/{total_stocks}): {name}...")
        
        try:
            # 1. Fetch Data
            df = loader.fetch_candle_data(token, name, interval="FIVE_MINUTE")
            
            # 2. Analyze
            if not df.empty:
                trade_setup = analyzer.analyze_stock(df, name)
                if trade_setup:
                    results.append(trade_setup)
                    st.toast(f"🚨 Found: {name} ({trade_setup['Signal']})")
        
        except Exception as e:
            # Failures ko ignore karo taaki scan na ruke
            pass
        
        # Update Progress & Sleep (Throttling)
        progress_bar.progress((i + 1) / total_stocks)
        time.sleep(scan_delay) 

    status_text.text("Scan Complete!")
    progress_bar.progress(100)

    # --- DISPLAY RESULTS ---
    if results:
        st.canvas = st.container()
        st.balloons()
        st.success(f"AI Found {len(results)} Trades!")
        
        res_df = pd.DataFrame(results)
        
        def highlight_signal(val):
            color = 'green' if val == 'BUY' else 'red'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            res_df.style.map(highlight_signal, subset=['Signal']),
            use_container_width=True
        )
        
        st.markdown("---")
        # Grid Layout for Cards
        cols = st.columns(3)
        for idx, trade in enumerate(results):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.subheader(f"{trade['Stock']}")
                    
                    # Color Logic
                    color = "green" if trade['Signal'] == "BUY" else "red"
                    
                    st.markdown(f":{color}[**{trade['Signal']}**] @ ₹{trade['Price']}")
                    st.metric("Target", f"₹{trade['Target']}", delta=f"Risk: ₹{trade['Risk_Per_Share']}", delta_color="inverse")
                    st.text(f"🛑 SL: ₹{trade['Stop_Loss']}")
                    
                    st.info(f"Logic: {trade['Reason']}")
                    st.caption(f"Momentum: {trade['Build_Up']}")
            
    else:
        st.warning("Market is sideways/choppy. No high-probability setups found.")
        st.caption("Try scanning again in 15 minutes.")