# check_price.py
from angel_connect import AngelLoader
from token_manager import get_high_volume_stocks
import pandas as pd

# 1. Login karo
print("Logging in...")
loader = AngelLoader()

# 2. SBIN ka Token dhoondo
print("Fetching Token Map...")
tokens = get_high_volume_stocks()
sbin_token = tokens.get("SBIN")

print(f"\n🔎 Token ID for SBIN: {sbin_token}")

if sbin_token:
    # 3. Data Fetch karo (5 Minute candle)
    print("Fetching Data from Angel One...")
    df = loader.fetch_candle_data(sbin_token, "SBIN", interval="FIVE_MINUTE")
    
    if not df.empty:
        last_candle = df.iloc[-1]
        print("\n------------------------------------------------")
        print(f"🔴 DATA RECEIVED FROM SERVER (Check Date & Time)")
        print("------------------------------------------------")
        print(f"📅 Time:   {last_candle['timestamp']}")
        print(f"💰 Close:  ₹{last_candle['close']}")
        print(f"📈 High:   ₹{last_candle['high']}")
        print(f"📉 Low:    ₹{last_candle['low']}")
        print("------------------------------------------------")
        
        # Google Price se match karne ke liye Logic
        print("\n👉 Agar Date purani hai (e.g. 2024), toh Logic 'Date Range' ka galat hai.")
        print("👉 Agar Price Google se ₹5-10 alag hai, toh ye 'Futures' ka data hai.")
        print("👉 Agar Price Google se match kar raha hai, toh Dashboard mein display issue hai.")
    else:
        print("❌ Data Empty Aaya! (Angel One ne data nahi diya)")
else:
    print("❌ SBIN Token List mein nahi mila!")