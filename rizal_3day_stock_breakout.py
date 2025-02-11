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
def dailyClosePricesbyPeriod(ticker,str_period='1y'):
    df = yf.download(ticker, period=str_period)
    df.reset_index(inplace=True)
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



ticker_list = sorted(list(set(['ADSK', 'CRM', 'MMM', 'ADBE', 'AMD', 'APD', 'ABNB', 'AMR', 'GOOG',
               'AMZN', 'AXP', 'AAPL', 'ANET', 'ARM', 'ASML', 'ACLS', 'BCC',
               'BKNG', 'BOOT', 'AVGO', 'CP', 'CF', 'CVX', 'CTAS', 'CL',
               'CPRT', 'CROX', 'DG', 'ELF', 'DAVA', 'ENPH', 'EXPE', 'XOM', 'FSLR',
               'FTNT', 'INMD', 'INTC', 'ISRG', 'JNJ', 'LRCX', 'LULU', 'CART',
               'MA', 'MRK', 'META', 'MU', 'MSFT', 'MRNA', 'MDLZ', 'NFLX',
               'NKE', 'NVO', 'NVDA', 'OXY', 'OKTA', 'ORCL', 'OTIS', 'PANW',
               'PYPL', 'PEP', 'PFE', 'PUBM', 'QCOM', 'QLYS', 'RVLV',
               'NOW', 'SHOP', 'SWKS', 'SFM', 'TSM', 'TGLS', 'TSLA', 'TXRH', 'KO',
               'EL', 'HSY', 'HD', 'KHC', 'PG', 'TTD', 'ULTA', 'VEEV', 'VICI', 'V',
               'SMCI', 'GFS', 'MRVL','DELL','ANF','CAT','KLAC','AMAT','ADM'
               ,'STLD','APP','CRWD','RKLB','SOUN','ABBV','APG','EDR','MNDY'
                       ])))

breakOut_ls = []
for ticker in ticker_list:
    df = dailyClosePricesbyPeriod(ticker)
    df = exponentialMovingAveragesClosePrice(df)
    df = findBreakOut(df,ticker)

    if len(df)>0:
      if df['break_out'][0]=='Yes' and df['break_out'][1]=='Yes' and df['break_out'][2]=='Yes' :
        breakOut_ls.append(ticker)



        
st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)





st.title('Last 3 Days Stock Break Out')
st.dataframe(recentFinance(breakOut_ls,recent_ls))
st.link_button("Go Stock Break Out Page to view charts..", "https://rizal-stock-breakout.streamlit.app/")

