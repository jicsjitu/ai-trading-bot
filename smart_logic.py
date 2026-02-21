# smart_logic.py
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, ADXIndicator 
from ta.volume import VolumeWeightedAveragePrice 
from ta.volatility import AverageTrueRange

class SmartAnalyzer:
    def __init__(self):
        pass

    def analyze_future_buildup(self, df):
        if len(df) < 20: # Kam se kam 20 candles chahiye moving average ke liye
            return "Neutral"

        price_now = df['close'].iloc[-1]
        price_prev = df['close'].iloc[-2]
        vol_now = df['volume'].iloc[-1]
        
        # Rolling Volume Avg
        vol_avg = df['volume'].rolling(20).mean().iloc[-1]
        
        price_change = price_now - price_prev
        
        if pd.isna(vol_avg) or vol_avg == 0:
            high_volume = False
        else:
            high_volume = vol_now > (vol_avg * 1.5) # Thoda strict kiya (1.5x)
        
        build_up = "Neutral"
        
        if price_change > 0 and high_volume:
            build_up = "Long Build Up 🟢"
        elif price_change < 0 and high_volume:
            build_up = "Short Build Up 🔴"
        elif price_change > 0 and not high_volume:
            build_up = "Short Covering ⚡"
        elif price_change < 0 and not high_volume:
            build_up = "Long Unwinding ⚠️"
            
        return build_up

    def analyze_stock(self, df_5min, stock_name):
        if df_5min.empty or len(df_5min) < 50:
            return None

        # --- INDICATORS ---
        ema_20 = EMAIndicator(close=df_5min['close'], window=20).ema_indicator().iloc[-1]
        ema_50 = EMAIndicator(close=df_5min['close'], window=50).ema_indicator().iloc[-1]
        adx = ADXIndicator(high=df_5min['high'], low=df_5min['low'], close=df_5min['close'], window=14).adx().iloc[-1]
        
        vwap_ind = VolumeWeightedAveragePrice(high=df_5min['high'], low=df_5min['low'], close=df_5min['close'], volume=df_5min['volume'], window=14)
        vwap = vwap_ind.volume_weighted_average_price().iloc[-1]
        
        atr = AverageTrueRange(high=df_5min['high'], low=df_5min['low'], close=df_5min['close'], window=14).average_true_range().iloc[-1]
        
        price = df_5min['close'].iloc[-1]
        build_up_status = self.analyze_future_buildup(df_5min)

        signal = "NEUTRAL"
        reasons = []
        
        is_uptrend = price > ema_20 > ema_50
        is_downtrend = price < ema_20 < ema_50
        
        # BUY LOGIC
        if is_uptrend and price > vwap and adx > 20:
            if "Long Build Up" in build_up_status or "Short Covering" in build_up_status:
                signal = "BUY"
                reasons.append(f"Trend Up + VWAP + {build_up_status}")
        
        # SELL LOGIC
        elif is_downtrend and price < vwap and adx > 20:
            if "Short Build Up" in build_up_status or "Long Unwinding" in build_up_status:
                signal = "SELL"
                reasons.append(f"Trend Down + VWAP Rejected + {build_up_status}")

        if signal == "NEUTRAL":
            return None

        # --- RISK MANAGEMENT ---
        sl_buffer = atr * 1.5
        if "BUY" in signal:
            stop_loss = price - sl_buffer
            target = price + (sl_buffer * 2)
        else:
            stop_loss = price + sl_buffer
            target = price - (sl_buffer * 2)
            
        risk_per_share = abs(price - stop_loss)

        return {
            "Stock": stock_name, 
            "Signal": signal,
            "Price": round(price, 2),
            "Build_Up": build_up_status, # Dashboard yahi dhoond raha tha
            "Stop_Loss": round(stop_loss, 2),
            "Target": round(target, 2),
            "Risk_Per_Share": round(risk_per_share, 2), # YEH KEY MISSING THI
            "Reason": ", ".join(reasons)
        }