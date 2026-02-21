# angel_connect.py
from SmartApi import SmartConnect
import pyotp
import pandas as pd
from datetime import datetime, timedelta
import time
import streamlit as st

# --- SECURITY FIX: Cloud vs Local ---
try:
    import config
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False

class AngelLoader:
    def __init__(self):
        # Decide karo password kahan se lena hai
        if LOCAL_MODE:
            self.api_key = config.API_KEY
            self.client_id = config.CLIENT_ID
            self.pwd = config.PASSWORD
            self.totp_key = config.TOTP_KEY
        else:
            self.api_key = st.secrets["API_KEY"]
            self.client_id = st.secrets["CLIENT_ID"]
            self.pwd = st.secrets["PASSWORD"]
            self.totp_key = st.secrets["TOTP_KEY"]

        self.api = SmartConnect(api_key=self.api_key)
        self.session = self._login()

    def _login(self):
        try:
            totp = pyotp.TOTP(self.totp_key).now()
            data = self.api.generateSession(self.client_id, self.pwd, totp)
            if data['status']:
                print("Login Successful")
                return data
            else:
                print("Login Failed:", data)
                return None
        except Exception as e:
            print(f"Connection Error: {e}")
            return None

    # ... (Neeche ka fetch_candle_data wala function bilkul same rahega, usko mat chhedna) ...

    def fetch_candle_data(self, token, symbol, interval="FIVE_MINUTE"):
        delays = [2, 5] 
        
        for attempt in range(2):
            try:
                # --- LOGIC FIX: Date Range ---
                # Hum pichle 2 din ka data mangenge taaki Indicators (EMA/VWAP) calculate ho sakein.
                # Sirf aaj ka data loge to subah 9:15 pe indicator banega hi nahi.
                to_date = datetime.now()
                from_date = to_date - timedelta(days=3) # Safe side 3 days
                
                historicParam = {
                    "exchange": "NSE",
                    "symboltoken": token,
                    "interval": interval,
                    "fromdate": from_date.strftime('%Y-%m-%d 09:15'),
                    "todate": to_date.strftime('%Y-%m-%d 15:30')
                }
                
                data = self.api.getCandleData(historicParam)
                
                if data['status'] and data['data']:
                    df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['close'] = df['close'].astype(float)
                    df['volume'] = df['volume'].astype(int)
                    df['high'] = df['high'].astype(float)
                    df['low'] = df['low'].astype(float)
                    return df
                
                elif not data['status']:
                    # Error code AB1004 matlab data nahi hai ya limit cross hui
                    # print(f"⚠️ Retry {symbol}...") # Console ganda na karne ke liye comment kiya
                    time.sleep(delays[attempt])
                    continue 
                
            except Exception as e:
                print(f"Error {symbol}: {e}")
                time.sleep(1)
        
        return pd.DataFrame()