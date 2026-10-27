import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Forex Analyser 1H", layout="wide")
st.title("Analyser - Forex BUY/SELL 1H Strategy")

pair_map = {
    "Gold (XAU/USD)": "GC=F",
    "USD/ZAR": "USDZAR=X",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

pair = st.selectbox("Select Forex Pair", list(pair_map.keys()), index=1)
symbol = pair_map[pair]
timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
interval = {"1h":"60m", "4h":"240m", "1d":"1d"}[timeframe]

@st.cache_data(ttl=600)
def get_data(sym, inter):
    df = yf.download(sym, period="60d", interval=inter, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

df = get_data(symbol, interval)

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['SMA20'] = df['Close'].rolling(20).mean()
df['SMA50'] = df['Close'].rolling(50).mean()
df['RSI'] = calc_rsi(df['Close'])

df = df.dropna()
last = df.iloc[-1]
price = float(last['Close'])
sma20 = float(last['SMA20'])
sma50 = float(last['SMA50'])
rsi = float(last['RSI'])

score = 50
reason = []

if price > sma20 > sma50:
    trend = "UPTREND"
    signal = "BUY 🟢"
    score += 20
    reason.append("Price > SMA20 > SMA50")
elif price < sma20 < sma50:
    trend = "DOWNTREND"
    signal = "SELL 🔴"
    score += 20
    reason.append("Price < SMA20 < SMA50")
else:
    trend = "RANGING"
    signal = "WAIT 🟡"
    reason.append("Price between SMAs")

if 40 <= rsi <= 70 and "BUY" in signal:
    score += 25
    reason.append(f"RSI {rsi:.1f} healthy for BUY")
elif 30 <= rsi <= 60 and "SELL" in signal:
    score += 25
    reason.append(f"RSI {rsi:.1f} healthy for SELL")
elif rsi > 70 or rsi < 30:
    score -= 20
    reason.append(f"RSI {rsi:.1f} overbought/oversold - risky")

score = max(10, min(95, score))

st.metric(f"{pair} Price ({timeframe})", f"{price:.4f}")
c1,c2,c3 = st.columns(3)
c1.metric("RSI", f"{rsi:.1f}")
c2.metric("SMA20", f"{sma20:.2f}")
c3.metric("SMA50", f"{sma50:.2f}")

st.subheader(f"{signal} - {trend} | Confidence: {score}%")
st.write("Reason: " + " | ".join(reason))
st.line_chart(df[['Close','SMA20','SMA50']].tail(100))

st.divider()
if score >= 80:
    st.success(f"🔔 ALERT: {pair} {signal} Score {score}%")
else:
    st.warning(f"No alert - Score {score}% < 80%. Like Gold at RSI 33 - wait.")

st.caption("Educational only - Not financial advice. Demo first.")
