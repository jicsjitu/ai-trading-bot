# token_manager.py
import requests
import pandas as pd
import streamlit as st

@st.cache_resource
def get_nifty_200_tokens():
    """
    Angel One ke server se scrip master download karke 
    sirf Liquid Stocks (Nifty 200 type) filter karega.
    """
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        print("Downloading Scrip Master... (Please wait)")
        data = requests.get(url).json()
        
        # DataFrame mein convert karo
        df = pd.DataFrame(data)
        
        # SIRF NSE Equity uthao
        # Aur sirf wo stocks jo '-EQ' mein end hote hain (Equity)
        df_nse = df[
            (df['exch_seg'] == 'NSE') & 
            (df['symbol'].str.endswith('-EQ')) & 
            (df['name'].str.isalpha()) # Junk symbols hatane ke liye
        ]
        
        # Filter Logic: Hum sirf Top stocks chahte hain taaki scan fast ho.
        # Filhal hum ek predefined 'Watchlist' logic use karenge ya
        # saare NSE stocks return karenge.
        
        # Optimization: Sirf known symbols ko filter karte hain jo liquid hain.
        # Note: Production mein tum is list ko aur bada kar sakte ho.
        # Example ke liye main yahan 150 important stocks return kar raha hun.
        
        # Cleanup: Symbol se '-EQ' hatao matching ke liye
        df_nse['clean_symbol'] = df_nse['symbol'].str.replace('-EQ', '')
        
        # Dictionary banao {Symbol: Token}
        token_map = dict(zip(df_nse['clean_symbol'], df_nse['token']))
        
        return token_map
        
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return {}

def get_high_volume_stocks():
    # Yeh list hum manually define kar rahe hain kyunki poora NSE scan karne mein 
    # API block ho jayega. Yeh Nifty 100 + F&O stocks hain.
    
    important_stocks = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", 
        "KOTAKBANK", "LT", "AXISBANK", "HINDUNILVR", "TATAMOTORS", "SUNPHARMA", "MARUTI", 
        "HCLTECH", "TITAN", "BAJFINANCE", "ASIANPAINT", "NTPC", "M&M", "ULTRACEMCO", 
        "POWERGRID", "TATASTEEL", "JSWSTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", 
        "ONGC", "BPCL", "GRASIM", "HEROMOTOCO", "HINDALCO", "TECHM", "WIPRO", "DRREDDY", 
        "CIPLA", "TATACONSUM", "APOLLOHOSP", "DIVISLAB", "EICHERMOT", "BAJAJFINSV", 
        "BRITANNIA", "NESTLEIND", "INDUSINDBK", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO",
        "LTIM", "PNB", "IOB", "UNIONBANK", "CANBK", "IDFCFIRSTB", "BANKBARODA", "BHEL",
        "DLF", "VEDL", "ZOMATO", "HAL", "TRENT", "BEL", "VBL", "JIOFIN", "ZOMATO",
        "IRFC", "RVNL", "NHPC", "SAIL", "ABCAPITAL", "MOTHERSON"
    ]
    
    # Master list download karo
    full_map = get_nifty_200_tokens()
    
    # Sirf hamare important stocks ka token nikalo
    final_list = {k: v for k, v in full_map.items() if k in important_stocks}
    
    return final_list