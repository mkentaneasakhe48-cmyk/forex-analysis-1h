import streamlit as st
import yfinance as yf
import pandas as pd
import ta

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

# Get data
df = yf.download(symbol, period="60d", interval=interval)
df = df.dropna()
df['SMA20'] = df['Close'].rolling(20).mean()
df['SMA50'] = df['Close'].rolling(50).mean()
df['RSI'] = ta.momentum.rsi(df['Close'], window=14)

last = df.iloc[-1]
price = float(last['Close'])
sma20 = float(last['SMA20'])
sma50 = float(last['SMA50'])
rsi = float(last['RSI'])

# Strategy Logic 1H
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
    reason.append("Price between SMAs - no trend")

# RSI filter
if 40 <= rsi <= 70 and "BUY" in signal:
    score += 25
    reason.append(f"RSI {rsi:.1f} healthy for BUY")
elif 30 <= rsi <= 60 and "SELL" in signal:
    score += 25
    reason.append(f"RSI {rsi:.1f} healthy for SELL")
elif rsi > 70 or rsi < 30:
    score -= 20
    reason.append(f"RSI {rsi:.1f} overbought/oversold - risky to enter now")

# Cap score
score = max(10, min(95, score))

st.metric(f"{pair} Price ({timeframe})", f"{price:.4f}")
col1, col2, col3 = st.columns(3)
col1.metric("RSI", f"{rsi:.1f}")
col2.metric("SMA20", f"{sma20:.2f}")
col3.metric("SMA50", f"{sma50:.2f}")

st.subheader(f"{signal} - {trend} | Confidence: {score}%")
st.write("Reason: " + " | ".join(reason))

st.line_chart(df[['Close','SMA20','SMA50']].tail(100))

# Alert
st.divider()
st.subheader("Alert")
if score >= 80:
    st.success(f"🔔 ALERT READY: {pair} {signal} Score {score}% - Time to check XM!")
    st.info("Connect Telegram Bot Token to send this automatically to your phone.")
else:
    st.warning(f"No alert yet - Score {score}% < 80%. Like Gold at RSI 33 - weak signal, wait.")

st.caption("Educational only - Not financial advice. Test on XM Demo first.")
