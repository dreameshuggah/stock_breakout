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
#from ticker_funcs import *






# ============ FUNCS ============
def SP500tickers():
    df = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    ticker_list = sorted(df['Symbol'].to_list())
    return ticker_list



def dailyClosePricesbyPeriod(ticker,str_period='1y'):
    #['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y','5y', 'ytd', 'max']
    df = yf.download(ticker, period=str_period)
    if len(df)>0:
        df.reset_index(inplace=True)
        df.columns = ['Date','Close','High','Low','Open','Volume']
        df['ticker']=ticker
    else:
        df = pd.DataFrame()       
    return df


def exponentialMovingAveragesClosePrice(df):
    df['EMA10']= df['Close'].ewm(span=10).mean()
    df['EMA20']= df['Close'].ewm(span=20).mean()
    df['EMA50']= df['Close'].ewm(span=50).mean()
    return df.sort_values(by=['Date'],ascending=[False])
    

def findBreakOut(df,ticker):
    qry = """
        SELECT *
        ,CASE 
        WHEN Close > EMA10 AND Close > EMA20 AND Close > EMA50 THEN 'Yes'
        ELSE 'No' END AS 'break_out'
        FROM df
        """.format(ticker=ticker)
    return sqldf(qry,locals())








#==== FETCH RECENT =======
recent_ls = ['shortName'
            ,'industry'
            ,'shortRatio'
            ,'trailingPE','forwardPE'    
            ,'currentPrice'
            #,'fiftyTwoWeekLow'
            ,'fiftyTwoWeekHigh'
            ,'targetMedianPrice'
            #,'targetHighPrice'
            #,'fiftyDayAverage','twoHundredDayAverage'
            
            ,'returnOnEquity','returnOnAssets','operatingMargins','ebitdaMargins'
            ,'revenueGrowth'
            ,'totalDebt','marketCap','freeCashflow'
            ,'debtToEquity'
            #,'longBusinessSummary'
            ,'sector'
            ]







def screenBreakOuts():
    ticker_list = SP500tickers()
    breakOut_ls = []
    
    for ticker in ticker_list:
        df = dailyClosePricesbyPeriod(ticker)
        if len(df)>0:
            df = exponentialMovingAveragesClosePrice(df)
            df = findBreakOut(df,ticker)
            
            if df['break_out'][0]=='Yes' and df['break_out'][1]=='Yes' and df['break_out'][2]=='Yes' :
                breakOut_ls.append(ticker)
        return breakOut_ls





def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res




def recentTickerFinance(ticker,recent_ls):
    fin_dict={'ticker':[ticker]}
    stock = yf.Ticker(ticker)
    for r in recent_ls:
        if r not in stock.info.keys():
            tmp_dict = {r:[np.nan]} 
        else:
            tmp_dict = {r:[stock.info[r]]}    
        fin_dict = Merge(fin_dict,tmp_dict)
    return pd.DataFrame.from_dict(fin_dict)



@st.cache_data
def recentFinance(ticker_ls,recent_ls):
    df = pd.DataFrame()
    for ticker in ticker_ls:
        tmp_df = recentTickerFinance(ticker,recent_ls)
        df = pd.concat([df,tmp_df])  
    df.fillna(0)

    qry = """
          SELECT 
          ROUND(  (currentPrice-fiftyTwoWeekHigh)/fiftyTwoWeekHigh  ,4)*100 AS perc_Chg_52WkHigh
          ,CAST(totalDebt AS FLOAT)/marketCap AS debtRatio
          ,* 
          FROM df
          ORDER BY revenueGrowth DESC
          """
    
    return sqldf(qry,locals())



def filterDf(df,forwardPE_cutoff):
    qry="""
        SELECT * 
        FROM df

        WHERE debtRatio < 0.33
        AND operatingMargins >= 0.1
        AND revenueGrowth > 0
        AND forwardPE < {forwardPE_cutoff}
        """.format(forwardPE_cutoff=forwardPE_cutoff)
    return sqldf(qry,locals())














st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

# download finance data
breakout_ls = screenBreakOuts()
fin_df = recentFinance(breakout_ls,recent_ls)

st.title('Last 3 Days Stock Break Out')
st.dataframe(fin_df)
st.link_button("Go Stock Break Out Page to view charts..", "https://rizal-stock-breakout.streamlit.app/")





st.write('\n\n\n')
st.write('\n\n\n')
col1, col2 = st.columns([2,1])

col1.markdown(""" 
    Filter:
    - total debt / market cap ratio < 0.33
    - operating margins > 0.1
    - revenueGrowth > 0
    - forward PE 
    """)



forwardPE_cutoff = col2.slider("Forward PE cut-off < ", 10, 40, 25)
#revenueGrowth_cutoff = col3.slider("revenueGrowth cut-off > ",0,0.05,0.1)
#marketCap_cutoff = col2.slider("marketCap (in millions) cut-off > ",100,500,1000)

st.write('\n\n\n')
st.write('\n\n\n')
fig_scatter = px.scatter(filterDf(fin_df,forwardPE_cutoff)
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

