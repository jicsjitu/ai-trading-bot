# smart_logic.py
import pandas as pd
import numpy as np
from datetime import datetime
from ta.trend import EMAIndicator, ADXIndicator 
from ta.volume import VolumeWeightedAveragePrice 
from ta.volatility import AverageTrueRange, BollingerBands

class SmartAnalyzer:
    def __init__(self):
        pass

    def is_valid_time(self, timestamp_str):
        # Market ke choppy/sideways time (11:30 to 13:30) ko filter out karta hai
        try:
            dt = pd.to_datetime(timestamp_str)
            time_obj = dt.time()
            
            morning_start = datetime.strptime("09:15", "%H:%M").time()
            morning_end = datetime.strptime("11:30", "%H:%M").time()
            
            afternoon_start = datetime.strptime("13:30", "%H:%M").time()
            afternoon_end = datetime.strptime("15:15", "%H:%M").time()
            
            if (morning_start <= time_obj <= morning_end) or (afternoon_start <= time_obj <= afternoon_end):
                return True
            return False
        except:
            return True

    def analyze_stock(self, df_5min, stock_name):
        if df_5min.empty or len(df_5min) < 200:
            return None

        df = df_5min.copy()

        # --- PROFESSIONAL INDICATORS ---
        df['ema_200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()
        df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
        df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
        
        df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14).adx()
        df['vwap'] = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14).volume_weighted_average_price()
        df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
        
        # Bollinger Bands for Squeeze & True Breakout
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['close'] # Volatility squeeze measure
        
        # Volume Spike (2.5x of 10-period average)
        df['vol_avg_10'] = df['volume'].rolling(10).mean()
        df['volume_spike'] = df['volume'] > (df['vol_avg_10'] * 2.5)
        
        # --- NO REPAINTING: CLOSED CANDLE [-2] FOR LOGIC ---
        closed = df.iloc[-2]  
        current = df.iloc[-1] 
        
        # Time Filter Check
        if not self.is_valid_time(current['timestamp']):
            return None

        # --- FAKE BREAKOUT PREVENTION CALCULATIONS ---
        candle_range = closed['high'] - closed['low']
        if candle_range == 0:
            return None
            
        candle_body = abs(closed['close'] - closed['open'])
        body_ratio = candle_body / candle_range # Body kitni strong hai
        
        # Upper wick/shadow check (Buyer rejection check)
        upper_wick = closed['high'] - max(closed['open'], closed['close'])
        is_clean_candle = upper_wick < (candle_range * 0.3) # Wick 30% se choti honi chahiye

        signal = "NEUTRAL"
        reasons = []
        
        # Trend Rules
        is_uptrend = (closed['close'] > closed['ema_20'] > closed['ema_50']) and (closed['close'] > closed['ema_200'])
        is_downtrend = (closed['close'] < closed['ema_20'] < closed['ema_50']) and (closed['close'] < closed['ema_200'])
        
        # --- BUY LOGIC (Zero Fake Breakout Filter) ---
        # 1. Trend Up 2. Price above VWAP 3. Strong ADX (>25) 4. Volume Spike 5. Clean Candle Body (>60%) 6. Breaking Bollinger High
        if is_uptrend and (closed['close'] > closed['vwap']) and (closed['adx'] > 25):
            if closed['volume_spike'] and (body_ratio >= 0.6) and is_clean_candle:
                if closed['close'] >= closed['bb_high'] * 0.99: # Band breakout confirmation
                    if current['close'] >= closed['close']: # Early catch validation
                        signal = "BUY"
                        reasons.append("Pro Anti-Fake Breakout + Vol-Spike + Clean Body")
                        
        # --- SELL LOGIC ---
        elif is_downtrend and (closed['close'] < closed['vwap']) and (closed['adx'] > 25):
            if closed['volume_spike'] and (body_ratio >= 0.6) and is_clean_candle:
                if closed['close'] <= closed['bb_low'] * 1.01:
                    if current['close'] <= closed['close']:
                        signal = "SELL"
                        reasons.append("Pro Breakdown + Rejection Clean + High Vol")

        if signal == "NEUTRAL":
            return None

        # --- PROFESSIONAL RISK MANAGEMENT (1:2 Risk/Reward) ---
        sl_buffer = closed['atr'] * 1.5
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
            "Build_Up": "Institutional Verified 🛡️", 
            "Stop_Loss": round(stop_loss, 2),
            "Target": round(target, 2),
            "Risk_Per_Share": round(risk_per_share, 2), 
            "Reason": reasons[0]
        }
