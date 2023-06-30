import yfinance as yf
from datetime import datetime
import streamlit as st
import plotly.express as px
import pandas as pd
#import talib as ta
import awswrangler as wr

# Add title and subtitle to the main interface of the app
st.write('## Kakaopay Stock Dashboard (377300.KS)')

# add new partition to athena table 
sql_1 = """msck repair table rachel.stock1"""
wr.athena.start_query_execution(sql_1, database='rachel')
print('msck')

# load data into dataframe
sql_2 = """select * from rachel.stock1"""
df = wr.athena.read_sql_query(sql_2, database='rachel')
print('select data')

# trim df
df1 = df[['date','close','last_updated']]
df1 = df1.sort_values(by='date', ascending=False)
df1 = df1.reset_index(drop=True)

# memo last updated time
last_updated = df1.last_updated.max()
st.markdown(f"<h10 style='text-align: left; color: grey;'>last updated: {last_updated}</h10>", unsafe_allow_html=True)

# line chart
fig = px.line(df1, x="date", y="close") #
st.plotly_chart(fig, theme=None, use_container_width=True)

print('refreshed.')