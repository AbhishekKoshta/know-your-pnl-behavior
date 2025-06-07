import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import random
import re

# 🎨 Fun theme setup
st.set_page_config(
    page_title="💰 Trading PnL Funhouse",
    layout="wide",
    page_icon="📊"
)

# 🏆 Initialize session state
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True
    st.session_state.visit_count = 0
    st.session_state.last_visit = datetime.now().strftime("%Y-%m-%d")
    st.session_state.badges = []
    st.session_state.symbols_analyzed = set()

# 👥 Visitor tracking (simulated)
st.session_state.visit_count += 1
current_date = datetime.now().strftime("%Y-%m-%d")
if current_date != st.session_state.last_visit:
    st.session_state.daily_visits = 1
    st.session_state.last_visit = current_date
else:
    st.session_state.daily_visits = st.session_state.get('daily_visits', 0) + 1

# 🎪 Main header
st.title("🎯💰📈 Trading PnL Funhouse 🎢📉")
st.caption("Analyze your trades for patterns, discipline, and performance 🧠💼")

# 👥 Visitor stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("👋 Today's Visitors", st.session_state.daily_visits)
with col2:
    st.metric("📅 Monthly Visitors", st.session_state.visit_count * random.randint(1, 3))
with col3:
    st.metric("⏱ Your Last Visit", st.session_state.last_visit)

# 🏆 Achievement system
def check_badges(symbol_count, pnl_value):
    new_badges = []
    if symbol_count >= 3 and "🔍 Analyst" not in st.session_state.badges:
        new_badges.append("🔍 Analyst")
    if symbol_count >= 10 and "📊 Pro Trader" not in st.session_state.badges:
        new_badges.append("📊 Pro Trader")
    if pnl_value > 10000 and "💰 Big Winner" not in st.session_state.badges:
        new_badges.append("💰 Big Winner")
    return new_badges

# 📂 File upload
st.header("📤 Upload Your Trading Data")
uploaded_file = st.file_uploader("Drag & drop your trading CSV file here 👇", type=["csv"])

if uploaded_file is not None:
    try:
        # 📊 Read data
        df = pd.read_csv(uploaded_file)
        
        with st.expander("🔍 Peek at your raw data (first 5 rows)"):
            st.dataframe(df.head())
        
        # 🛠 Data processing
        # st.header("🧹 Step 2: Clean & Prepare Data")
        
        # Check required columns
        required_columns = ['symbol', 'order_execution_time', 'trade_type', 'quantity', 'price']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"🚨 Oops! Missing columns: {', '.join(missing_cols)}")
        else:
            # Extract index name from symbol (e.g., "FINNIFTY2440221300PE" → "FINNIFTY")
            df['index_name'] = df['symbol'].apply(lambda x: re.sub(r'\d+.*', '', x))
            
            # Convert order_execution_time to datetime
            df['order_execution_time'] = pd.to_datetime(df['order_execution_time'])
            
            # Calculate values
            df['trade_value'] = df['quantity'] * df['price']
            df['trade_day'] = df['order_execution_time'].dt.day_name()
            df['trade_hour'] = df['order_execution_time'].dt.hour
            df['trade_date_only'] = df['order_execution_time'].dt.date
            
            # 🎯 Symbol (index) selection
            st.header("🎯 Pick Your Symbol")
            all_indices = df['index_name'].unique()
            selected_index = st.selectbox(
                "Which index do you want to analyze?",
                all_indices,
                index=0
            )
            
            # Track analyzed indices
            st.session_state.symbols_analyzed.add(selected_index)
            
            # Filter data for selected index
            index_df = df[df['index_name'] == selected_index]
            
            # 🏆 Performance dashboard
            st.header(f"🏆 {selected_index} Performance Dashboard")
            
            # 📈 Quick stats
            col1, col2, col3 = st.columns(3)
            with col1:
                total_trades = len(index_df)
                st.metric("📊 Total Trades", total_trades)
            
            with col2:
                buy_volume = index_df[index_df['trade_type'] == 'buy']['quantity'].sum()
                st.metric("🛒 Buy Volume", buy_volume)
            
            with col3:
                sell_volume = index_df[index_df['trade_type'] == 'sell']['quantity'].sum()
                st.metric("💰 Sell Volume", sell_volume)
            
            # 📊 PnL analysis
            st.subheader("💹 Profit & Loss Breakdown")
            
            pnl_df = index_df.groupby('trade_type').agg(
                total_quantity=('quantity', 'sum'),
                avg_price=('price', 'mean'),
                total_value=('trade_value', 'sum'),
                trade_count=('trade_type', 'count')
            ).reset_index()
            
            st.dataframe(pnl_df.style.format({
                'avg_price': '{:.2f}',
                'total_value': '{:.2f}'
            }))
            
            # 📊 Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📅 Daily Performance")
                daily_pnl = index_df.groupby(['trade_date_only', 'trade_type'])['trade_value'].sum().unstack()
                if 'buy' in daily_pnl.columns and 'sell' in daily_pnl.columns:
                    daily_pnl['daily_pnl'] = daily_pnl['sell'] - daily_pnl['buy']
                    fig = px.line(daily_pnl, x=daily_pnl.index, y='daily_pnl', 
                                title=f"Daily PnL for {selected_index}",
                                markers=True)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🕒 Hourly Performance (Execution Time)")
                hour_pnl = index_df.groupby(['trade_hour', 'trade_type'])['trade_value'].sum().unstack()
                if 'buy' in hour_pnl.columns and 'sell' in hour_pnl.columns:
                    hour_pnl['hour_pnl'] = hour_pnl['sell'] - hour_pnl['buy']
                    fig = px.bar(hour_pnl, x=hour_pnl.index, y='hour_pnl', 
                               title=f"Hourly PnL by Execution Time",
                               color='hour_pnl',
                               color_continuous_scale='RdYlGn',
                               labels={'trade_hour': 'Hour of Execution'})
                    st.plotly_chart(fig, use_container_width=True)
            
            # 🧠 Behavioral insights
            st.subheader("🧠 Trading Psychology Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📅 Best Day to Trade")
                dow_pnl = index_df.groupby(['trade_day', 'trade_type'])['trade_value'].sum().unstack()
                if 'buy' in dow_pnl.columns and 'sell' in dow_pnl.columns:
                    dow_pnl['dow_pnl'] = dow_pnl['sell'] - dow_pnl['buy']
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    dow_pnl = dow_pnl.reindex(day_order)
                    best_day = dow_pnl['dow_pnl'].idxmax()
                    st.metric("⭐ Best Day", best_day)
            
            with col2:
                st.subheader("⏰ Best Execution Hour")
                if 'hour_pnl' in locals():
                    best_hour = hour_pnl['hour_pnl'].idxmax()
                    st.metric("⌛ Best Hour", f"{best_hour}:00 - {best_hour+1}:00")
            
            # 🎁 Results summary
            total_pnl = pnl_df[pnl_df['trade_type'] == 'sell']['total_value'].sum() - pnl_df[pnl_df['trade_type'] == 'buy']['total_value'].sum()
            
            if total_pnl > 0:
                st.balloons()
                st.success(f"🎉 Congratulations! You made ₹{total_pnl:,.2f} on {selected_index}!")
            else:
                st.warning(f"🤕 Ouch! You lost ₹{abs(total_pnl):,.2f} on {selected_index}. Better luck next time!")
            
            # 🏆 Check for new badges
            new_badges = check_badges(len(st.session_state.symbols_analyzed), total_pnl)
            if new_badges:
                st.session_state.badges.extend(new_badges)
                with st.expander("🎖️ New Achievement Unlocked!", expanded=True):
                    for badge in new_badges:
                        st.success(f"🏅 You earned the {badge} badge!")
                        time.sleep(1)
            
            # 🎮 Gamification
            st.subheader("🏆 Your Trading Profile")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📌 Indices Analyzed", len(st.session_state.symbols_analyzed))
                st.metric("📅 Days Active", st.session_state.visit_count // 2)
                
            with col2:
                if st.session_state.badges:
                    st.write("🎖️ Your Badges:")
                    for badge in st.session_state.badges:
                        st.write(f"- {badge}")
                else:
                    st.info("🔍 Analyze more indices to earn badges!")
            
            # 📥 Export
            st.download_button(
                label="📥 Download Index Report",
                data=pnl_df.to_csv(index=False),
                file_name=f"{selected_index}_pnl_report.csv",
                mime="text/csv"
            )
            
            # 🔄 Analyze another suggestion
            if len(all_indices) > 1:
                st.subheader("🔍 Try Another Index")
                other_indices = [s for s in all_indices if s != selected_index]
                next_index = random.choice(other_indices)
                if st.button(f"🧐 Analyze {next_index} next"):
                    selected_index = next_index
                    st.experimental_rerun()
    
    except Exception as e:
        st.error(f"💥 Yikes! Something went wrong: {str(e)}")
else:
    st.info("👋 Hey there! Upload your trading CSV to get started. Need example data? Check our GitHub!")
    
    if st.session_state.first_visit:
        with st.expander("🎁 Welcome Bonus - Quick Trading Tip!"):
            st.write("""
            💡 **Pro Tip:** The first and last hour of trading typically see the highest volatility. 
            Check the hourly performance charts after uploading your data to find your optimal execution times!
            """)
        st.session_state.first_visit = False

# 📊 Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.write(f"📊 Total dashboard views: {st.session_state.visit_count * 3}")
with col2:
    st.write(f"⏱ Session started: {datetime.now().strftime('%H:%M:%S')}")
