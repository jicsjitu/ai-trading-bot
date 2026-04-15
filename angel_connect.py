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
                ist_timezone = pytz.timezone('Asia/Kolkata')
                now = datetime.now(ist_timezone)
                
                # --- ANGEL ONE SECRET FIX ---
                # Pura current time mat maango. 5 minute peeche ka maango taaki candle 'Close' ho chuki ho.
                safe_to_date = now - timedelta(minutes=5)
                # 5 din peeche ka data maango taaki weekends (Sat/Sun) bhi cover ho jayein
                from_date = safe_to_date - timedelta(days=5)
                
                historicParam = {
                    "exchange": "NSE",
                    "symboltoken": str(token), # Ise hamesha text (string) format mein bhejna hota hai
                    "interval": interval,
                    "fromdate": from_date.strftime('%Y-%m-%d 09:15'),
                    "todate": safe_to_date.strftime('%Y-%m-%d %H:%M') 
                }
                
                data = self.api.getCandleData(historicParam)
                
                # Agar status True hai aur data list empty nahi hai
                if data and data.get('status') and data.get('data'):
                    df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['close'] = df['close'].astype(float)
                    df['volume'] = df['volume'].astype(int)
                    df['high'] = df['high'].astype(float)
                    df['low'] = df['low'].astype(float)
                    return df
                
                elif data and not data.get('status'):
                    # Ab terminal mein actual error message aayega!
                    print(f"⚠️ API Rejected {symbol}: {data.get('message')}")
                    time.sleep(delays[attempt])
                    continue 
                
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                time.sleep(2)
        
        return pd.DataFrame()
