#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import streamlit.components.v1 as components

# streamlit run rizal_3day_stock_breakout.py

import pandas as pd
import numpy as np

#from IPython.display import display
#pd.options.display.max_columns = None
#pd.options.display.max_rows = 30
#pd.get_option("display.max_rows")
#pd.set_option('display.max_rows', 100)

from pandasql import sqldf
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from ThreeDayBreakOut import *


st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

# download finance data
fin_df = recentFinance(screenBreakOuts(),recent_ls)

st.title('Last 3 Days Stock Break Out')
st.dataframe(fin_df)
st.link_button("Go Stock Break Out Page to view charts..", "https://rizal-stock-breakout.streamlit.app/")





st.write('\n\n\n')
st.write('\n\n\n')
#col1, col2 = st.columns([2,1])

st.markdown(""" 
    Filter:
    - total debt / market cap ratio < 0.33
    - operating margins > 0.1
    - revenueGrowth > 0
    - forward PE < 30
    """)



st.write('\n\n\n')
st.write('\n\n\n')
fig_scatter = px.scatter(filterDf(fin_df)
                         , x="returnOnEquity" 
                         , y= "operatingMargins"
                         , color= 'industry'
                         , size= 'forwardPE'
                         #, symbol = 'industry'
                         , hover_data=['ticker','shortName','revenueGrowth','forwardPE']
                         , title = 'Return On Equity vs Operating Margins: Size by Forward PE'
                         #, height = '700'
                        )
st.plotly_chart(fig_scatter, key="ticker0")#, on_select="rerun")

