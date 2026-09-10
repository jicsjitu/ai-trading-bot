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
        
        # Cleanup: Symbol se '-EQ' hatao matching ke liye
        df_nse['clean_symbol'] = df_nse['symbol'].str.replace('-EQ', '')
        
        # Dictionary banao {Symbol: Token}
        token_map = dict(zip(df_nse['clean_symbol'], df_nse['token']))
        
        return token_map
        
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return {}

def get_high_volume_stocks():
    # Yeh list poori tarah updated aur optimized hai jisme saare high-momentum, 
    # F&O, defense, aur liquid intraday stocks shamil hain.
    
    important_stocks = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", 
        "KOTAKBANK", "LT", "AXISBANK", "HINDUNILVR", "TATAMOTORS", "SUNPHARMA", "MARUTI", 
        "HCLTECH", "TITAN", "BAJFINANCE", "ASIANPAINT", "NTPC", "M&M", "ULTRACEMCO", 
        "POWERGRID", "TATASTEEL", "JSWSTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", 
        "ONGC", "BPCL", "GRASIM", "HEROMOTOCO", "HINDALCO", "TECHM", "WIPRO", "DRREDDY", 
        "CIPLA", "TATACONSUM", "APOLLOHOSP", "DIVISLAB", "EICHERMOT", "BAJAJFINSV", 
        "BRITANNIA", "NESTLEIND", "INDUSINDBK", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO",
        "LTIM", "PNB", "IOB", "UNIONBANK", "CANBK", "IDFCFIRSTB", "BANKBARODA", "BHEL",
        "DLF", "VEDL", "ZOMATO", "HAL", "TRENT", "BEL", "VBL", "JIOFIN", 
        "IRFC", "RVNL", "NHPC", "SAIL", "ABCAPITAL", "MOTHERSON",
        "TATAPOWER", "TVSMOTOR", "ASHOKLEY", "AMBUJACEM", "INDIGO", "SHRIRAMFIN", "PBFINTECH",
        "JINDALSTEL", "SIEMENS", "ABB", "CHOLAFIN", "DIXON", "PERSISTENT", "COFORGE",
        "MAZDOCK", "COCHINSHIP", "BDL", "GODREJPROP", "OBEROIRL", "APOLLOTYRE", "LUPIN", "GODREJCP", "MCX",
        "PFC", "RECLTD", "IEX", "BHARATFORG", "EXIDEIND", "SRF", "PIIND", "MUTHOOTFIN", "JUBLFOOD", "TORNTPHARM", "AUROPHARMA",
        "PVRINOX", "UPL"
    ]
    
    # Master list download karo
    full_map = get_nifty_200_tokens()
    
    # Sirf hamare important stocks ka token nikalo
    final_list = {k: v for k, v in full_map.items() if k in important_stocks}
    
    return final_list
