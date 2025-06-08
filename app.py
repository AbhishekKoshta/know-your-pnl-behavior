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
st.title("💰📈 Trading PnL Funhouse 🎢📉")
st.caption("Comment on my articale for any changes - https://medium.com/@abhi771991/decoding-your-trading-destiny-introducing-your-trading-kundali-6152b6e96ecc")

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
st.header("📤 Step 1: Upload Your Trading Data")
uploaded_file = st.file_uploader("Drag & drop your trading CSV file here 👇", type=["csv"])

if uploaded_file is not None:
    try:
        # 📊 Read data
        df = pd.read_csv(uploaded_file)
        
        with st.expander("🔍 Peek at your raw data (first 5 rows)"):
            st.dataframe(df.head())
        
        # 🛠 Data processing
        st.header("🧹 Step 2: Clean & Prepare Data")
        
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
            df['trade_hour'] = df['order_execution_time'].dt.hour
            df['trade_date_only'] = df['order_execution_time'].dt.date
            
            # Create proper day of week columns (this fixes the error)
            df['trade_weekday'] = df['order_execution_time'].dt.dayofweek  # Monday=0, Sunday=6
            df['trade_day_name'] = df['order_execution_time'].dt.day_name()  # Full day name
            
            # 🎯 Index selection section
            st.header("🎯 Step 3: Pick Your Index")
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
            
            # =============================================
            # 🕒 TIME-BASED ANALYSIS (Index Specific)
            # =============================================
            st.subheader("⏰ Time-Based Performance")
            
            # Day of week analysis - FIXED IMPLEMENTATION
            st.markdown("#### 📅 Day of Week Analysis")
            
            # Group by weekday number and day name together
            dow_pnl = index_df.groupby(['trade_weekday', 'trade_day_name', 'trade_type'])['trade_value'].sum().unstack()
            
            if 'buy' in dow_pnl.columns and 'sell' in dow_pnl.columns:
                dow_pnl['dow_pnl'] = dow_pnl['sell'] - dow_pnl['buy']
                
                # Sort by weekday number (Monday=0 to Sunday=6)
                dow_pnl = dow_pnl.sort_index(level='trade_weekday')
                
                # Get day names in correct order for display
                day_names = dow_pnl.index.get_level_values('trade_day_name').unique()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(dow_pnl.reset_index(), 
                                x='trade_day_name', 
                                y='dow_pnl',
                                title=f"PnL by Day of Week",
                                color='dow_pnl',
                                color_continuous_scale='RdYlGn',
                                category_orders={"trade_day_name": list(day_names)})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    best_day = dow_pnl['dow_pnl'].idxmax()[1]  # Get day name from multi-index
                    worst_day = dow_pnl['dow_pnl'].idxmin()[1]
                    st.metric("⭐ Best Day", best_day)
                    st.metric("💔 Worst Day", worst_day)
                    st.dataframe(dow_pnl[['buy', 'sell', 'dow_pnl']].style.format("{:.2f}"))

                # Add this after the day-wise analysis section (around line 200 in previous code)

                # =========================================
                # 🔴 Mangal Dosh Warning (Dynamic Alert)
                # =========================================
                if 'Mangalvaar' in dow_pnl.index and dow_pnl.loc['Mangalvaar', 'pnl'] < 0:
                    loss_percent = abs(dow_pnl.loc['Mangalvaar', 'pnl']) / dow_pnl['pnl'].abs().sum() * 100
                    
                    st.warning(f"""
                    🔴 **Mangal Ka Prabhav!**  
                    Aapke {selected_index} trades mein:  
                    - Mangalvaar (Tuesday) ko sabse zyada nuksaan hua: **₹{abs(dow_pnl.loc['Mangalvaar', 'pnl']):,.0f}**  
                    - Ye aapke kul nuksaan ka **{loss_percent:.0f}%** hai  

                    💡 *Panditji ka sujhav:*  
                    "Mangalvaar ko trade avoid karein, ya stop-loss zaroor lagayein!"  
                    """, icon="⚠️")
                    
                    # Add astrological GIF
                    st.image("https://i.gifer.com/7IAj.gif", width=200, 
                             caption="Mangal grah aapke trades ko prabhavit kar raha hai")

                # =========================================
                # 🪐 Grah Anusaar Trading Tips (Planetary Advice)
                # =========================================
                st.subheader("🪐 Grah Anusaar Trading Tips")

                planetary_advice = {
                    "Somvaar": "Shani ka prabhav - Patience rakhein, long-term trades prefer karein",
                    "Mangalvaar": "Mangal grah aggressive - Stop-loss na bhulein!",
                    "Budhvaar": "Budh favorable - Intraday trades ke liye best din",
                    "Guruvaar": "Guru ka ashirwad - New strategies try karne ka shubh samay",
                    "Shukravaar": "Shukra positive - Option buying ke liye achha din"
                }

                selected_day = st.selectbox("Din chunein:", list(planetary_advice.keys()))
                st.info(f"""
                {selected_day} ka sujhav:  
                ✨ *"{planetary_advice[selected_day]}"*  
                """)
            
            # Hourly analysis
            st.markdown("#### 🕒 Hour of Day Analysis")
            hour_pnl = index_df.groupby(['trade_hour', 'trade_type'])['trade_value'].sum().unstack()
            
            if 'buy' in hour_pnl.columns and 'sell' in hour_pnl.columns:
                hour_pnl['hour_pnl'] = hour_pnl['sell'] - hour_pnl['buy']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(hour_pnl.reset_index(), 
                                x='trade_hour', 
                                y='hour_pnl',
                                title=f"PnL by Execution Hour",
                                color='hour_pnl',
                                color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    best_hour = hour_pnl['hour_pnl'].idxmax()
                    worst_hour = hour_pnl['hour_pnl'].idxmin()
                    st.metric("⏰ Best Hour", f"{best_hour}:00")
                    st.metric("👎 Worst Hour", f"{worst_hour}:00")
                    st.dataframe(hour_pnl[['buy', 'sell', 'hour_pnl']].style.format("{:.2f}"))
            
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
            
            # 🔄 Analyze another suggestion
            if len(all_indices) > 1:
                st.subheader("🔍 Try Another Index")
                other_indices = [s for s in all_indices if s != selected_index]
                next_index = random.choice(other_indices)
                if st.button(f"🧐 Analyze {next_index} next"):
                    selected_index = next_index
                    st.experimental_rerun()
            
            # =============================================
            # 🌍 COMPLETE ANALYSIS SECTION (ALL INDICES)
            # =============================================
            st.markdown("---")
            st.header("🌍 Complete Analysis (All Indices)")
            
            # Overall stats
            st.subheader("📊 Overall Performance")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📌 Total Indices Traded", len(df['index_name'].unique()))
            with col2:
                st.metric("🔄 Total Trades", len(df))
            with col3:
                total_pnl_all = df[df['trade_type'] == 'sell']['trade_value'].sum() - df[df['trade_type'] == 'buy']['trade_value'].sum()
                st.metric("💰 Net PnL (All)", f"₹{total_pnl_all:,.2f}")
            
            # Day of week analysis (all indices) - FIXED IMPLEMENTATION
            st.subheader("📅 Best Days to Trade (All Indices)")
            
            dow_all = df.groupby(['trade_weekday', 'trade_day_name', 'trade_type'])['trade_value'].sum().unstack()
            if 'buy' in dow_all.columns and 'sell' in dow_all.columns:
                dow_all['dow_pnl'] = dow_all['sell'] - dow_all['buy']
                dow_all = dow_all.sort_index(level='trade_weekday')
                
                # Get ordered day names
                day_names_all = dow_all.index.get_level_values('trade_day_name').unique()
                
                fig = px.bar(dow_all.reset_index(), 
                            x='trade_day_name', 
                            y='dow_pnl',
                            title="Overall PnL by Day of Week",
                            color='dow_pnl',
                            color_continuous_scale='RdYlGn',
                            category_orders={"trade_day_name": list(day_names_all)})
                st.plotly_chart(fig, use_container_width=True)
                
                best_day_all = dow_all['dow_pnl'].idxmax()[1]
                worst_day_all = dow_all['dow_pnl'].idxmin()[1]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⭐ Overall Best Day", best_day_all)
                with col2:
                    st.metric("💔 Overall Worst Day", worst_day_all)
            
            # Hourly analysis (all indices)
            st.subheader("🕒 Best Execution Times (All Indices)")
            
            hour_all = df.groupby(['trade_hour', 'trade_type'])['trade_value'].sum().unstack()
            if 'buy' in hour_all.columns and 'sell' in hour_all.columns:
                hour_all['hour_pnl'] = hour_all['sell'] - hour_all['buy']
                
                fig = px.bar(hour_all.reset_index(), 
                            x='trade_hour', 
                            y='hour_pnl',
                            title="Overall PnL by Execution Hour",
                            color='hour_pnl',
                            color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
                
                best_hour_all = hour_all['hour_pnl'].idxmax()
                worst_hour_all = hour_all['hour_pnl'].idxmin()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⏰ Overall Best Hour", f"{best_hour_all}:00")
                with col2:
                    st.metric("👎 Overall Worst Hour", f"{worst_hour_all}:00")
            
            # Index comparison
            st.subheader("📈 Index Performance Comparison")
            
            index_comparison = df.groupby(['index_name', 'trade_type'])['trade_value'].sum().unstack()
            if 'buy' in index_comparison.columns and 'sell' in index_comparison.columns:
                index_comparison['pnl'] = index_comparison['sell'] - index_comparison['buy']
                index_comparison = index_comparison.sort_values('pnl', ascending=False)
                
                fig = px.bar(index_comparison.reset_index(), 
                            x='index_name', 
                            y='pnl',
                            title="PnL by Index",
                            color='pnl',
                            color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(index_comparison.style.format("{:.2f}"))
            
            # 📥 Export complete analysis
            st.download_button(
                label="📥 Download Complete Analysis Report",
                data=index_comparison.to_csv(),
                file_name="complete_pnl_analysis.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"💥 Yikes! Something went wrong: {str(e)}")
        st.error("Please check your data format and try again.")
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
st.markdown("""
❤️ Pasand aaya? Apne trading friends ko bhi batayein: [Share on WhatsApp](https://wa.me/?text=Check%20this%20cool%20trading%20dashboard%20{https://know-your-pnl-behavior-bttqhrtvdzsse3wsp7spuf.streamlit.app/})
""")
st.markdown("""💡 For more details read - https://medium.com/@abhi771991/apni-trading-kundali-dekho-f0ed39377ff2""")
""")col1, col2 = st.columns(2)
with col1:
    st.write(f"📊 Total dashboard views: {st.session_state.visit_count * 3}")
with col2:
    st.write(f"⏱ Session started: {datetime.now().strftime('%H:%M:%S')}")
