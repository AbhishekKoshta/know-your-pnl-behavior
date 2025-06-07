import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO

st.set_page_config(page_title="🎯 F&O Behavioral Dashboard", layout="wide")
st.title("📈 F&O Trade Behavior Dashboard")
st.caption("Analyze your trades for patterns, discipline, and performance 🧠💼")

# Upload section
uploaded_file = st.file_uploader("📤 Upload your Zerodha F&O tradebook CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Filter out only executed orders
    df = df[df['status'].str.lower() == 'complete']

    # Standardize trade direction
    df['direction'] = df['trade_type'].str.lower().map({'buy': 1, 'sell': -1})
    df['net_qty'] = df['quantity'] * df['direction']
    df['amount'] = df['quantity'] * df['price'] * df['direction']

    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df['day'] = df['trade_date'].dt.date

    # Group by symbol + expiry to track pnl
    pnl_summary = df.groupby(['symbol', 'day']).agg(
        total_trades=('order_execution_time', 'count'),
        net_qty=('net_qty', 'sum'),
        net_pnl=('amount', 'sum')
    ).reset_index()

    daily_pnl = pnl_summary.groupby('day')['net_pnl'].sum().reset_index()
    daily_pnl['color'] = np.where(daily_pnl['net_pnl'] >= 0, 'green', 'red')

    st.subheader("🔍 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total P&L", f"₹{df['amount'].sum():,.2f}", delta_color="inverse")
    col2.metric("Number of Trades", f"{len(df)}")
    col3.metric("Win Rate", f"{(df[df['amount'] > 0].shape[0] / df.shape[0] * 100):.2f}%")

    # Bar chart for daily pnl
    st.subheader("📅 Daily P&L")
    fig = px.bar(daily_pnl, x='day', y='net_pnl', color='color', 
                 color_discrete_map={'green': 'green', 'red': 'crimson'}, 
                 title='Daily Profit/Loss')
    st.plotly_chart(fig, use_container_width=True)

    # Behavior flags
    st.subheader("🧠 Behavioral Insights")
    behavior_flags = {
        'Overtrading Days': pnl_summary[pnl_summary['total_trades'] > 10].shape[0],
        'High Loss Days (> ₹2K)': pnl_summary[pnl_summary['net_pnl'] < -2000].shape[0],
        'Consistent Win Days': pnl_summary[pnl_summary['net_pnl'] > 0].shape[0],
        'Loss Streaks': (daily_pnl['net_pnl'] < 0).astype(int).diff().eq(1).sum()
    }
    for key, val in behavior_flags.items():
        st.write(f"✅ **{key}**: {val}")

    # Downloadable cleaned version
    st.subheader("⬇️ Download Cleaned Data")
    cleaned_csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Cleaned CSV", cleaned_csv, file_name="cleaned_trades.csv", mime='text/csv')
else:
    st.info("Please upload a Zerodha tradebook CSV to begin ✨")
