import streamlit as st
import streamlit.components.v1 as components
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


# streamlit run rizal_stock_breakout.py

#====== FUNCS =====

def dailyClosePricesbyPeriod(ticker,str_period='1y'):
    df = yf.download(ticker, period=str_period)
    df.reset_index(inplace=True)
    return df


def movingAveragesClosePrice(df):
    df['sma10'] = df['Close'].rolling(window=10).mean()
    df['sma20'] = df['Close'].rolling(window=20).mean()
    df['sma50'] = df['Close'].rolling(window=50).mean()
    df = df.sort_values(by=['Date'],ascending=[False])
    return df


def findBreakOut(df):
    qry = """
        SELECT *
        ,CASE 
        WHEN Close > sma10 AND Close > sma20 AND Close > sma50 THEN 'Yes'
        ELSE 'No' END AS 'break_out'
        FROM df
        """
    return sqldf(qry,locals())
  
  
  

st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)


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
               ,'STLD','APP','CRWD','RKLB','SOUN'
                       ])))
                       
                       
                       
                       
st.title('Stock Break Out')
ticker = st.multiselect('Select a ticker:',ticker_list,['QCOM'])#,disabled=True)      
      

if len(ticker)==1:    
  df = dailyClosePricesbyPeriod(ticker)
  df = movingAveragesClosePrice(df)
  df = findBreakOut(df)  
  
  closeTitle = ticker[0] + ' Daily Close Prices'
  fig_close_prices = px.scatter(df, x="Date", y="Close", color="break_out", title = closeTitle )
  st.plotly_chart(fig_close_prices, key="scatter1")#, on_select="rerun")
  
  
  volumeTitle = ticker[0] + ' Volume'
  fig_volume = px.bar(df, x="Date", y="Volume" ,color="break_out", title =  volumeTitle)
  st.plotly_chart(fig_volume,key='bar1')
  
  st.dataframe(df)

