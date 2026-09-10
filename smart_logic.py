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
        if len(df) < 20: 
            return "Neutral"

        # Using closed candle [-2] and previous [-3] for stable buildup logic
        price_now = df['close'].iloc[-2]
        price_prev = df['close'].iloc[-3]
        vol_now = df['volume'].iloc[-2]
        
        vol_avg = df['volume'].rolling(20).mean().iloc[-2]
        price_change = price_now - price_prev
        
        if pd.isna(vol_avg) or vol_avg == 0:
            high_volume = False
        else:
            high_volume = vol_now > (vol_avg * 1.5) 
        
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

        # --- NO REPAINTING: CLOSED CANDLE [-2] FOR LOGIC, CURRENT [-1] FOR ENTRY ---
        closed = df_5min.iloc[-2]
        current = df_5min.iloc[-1]

        # --- INDICATORS (Calculated on closed data to prevent repainting) ---
        ema_20 = EMAIndicator(close=df_5min['close'], window=20).ema_indicator().iloc[-2]
        ema_50 = EMAIndicator(close=df_5min['close'], window=50).ema_indicator().iloc[-2]
        adx = ADXIndicator(high=df_5min['high'], low=df_5min['low'], close=df_5min['close'], window=14).adx().iloc[-2]
        
        vwap_ind = VolumeWeightedAveragePrice(high=df_5min['high'], low=df_5min['low'], close=df_5min['close'], volume=df_5min['volume'], window=14)
        vwap = vwap_ind.volume_weighted_average_price().iloc[-2]
        
        atr = AverageTrueRange(high=df_5min['high'], low=df_5min['low'], close=df_5min['close'], window=14).average_true_range().iloc[-2]
        
        build_up_status = self.analyze_future_buildup(df_5min)

        signal = "NEUTRAL"
        reasons = []
        
        is_uptrend = closed['close'] > ema_20 > ema_50
        is_downtrend = closed['close'] < ema_20 < ema_50
        
        # BUY LOGIC
        if is_uptrend and closed['close'] > vwap and adx > 20:
            if "Long Build Up" in build_up_status or "Short Covering" in build_up_status:
                signal = "BUY"
                reasons.append(f"Trend Up + VWAP + {build_up_status}")
        
        # SELL LOGIC
        elif is_downtrend and closed['close'] < vwap and adx > 20:
            if "Short Build Up" in build_up_status or "Long Unwinding" in build_up_status:
                signal = "SELL"
                reasons.append(f"Trend Down + VWAP Rejected + {build_up_status}")

        if signal == "NEUTRAL":
            return None

        # --- RISK MANAGEMENT (Execution on Current Live Price) ---
        sl_buffer = atr * 1.5
        entry_price = current['close']
        
        if signal == "BUY":
            stop_loss = entry_price - sl_buffer
            target = entry_price + (sl_buffer * 2)
        else:
            stop_loss = entry_price + sl_buffer
            target = entry_price - (sl_buffer * 2)
            
        risk_per_share = abs(entry_price - stop_loss)

        return {
            "Stock": stock_name, 
            "Signal": signal,
            "Price": round(entry_price, 2),
            "Build_Up": build_up_status, 
            "Stop_Loss": round(stop_loss, 2),
            "Target": round(target, 2),
            "Risk_Per_Share": round(risk_per_share, 2), 
            "Reason": ", ".join(reasons)
        }
