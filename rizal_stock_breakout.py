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
import plotly.graph_objects as go
from ticker_funcs import *

# streamlit run rizal_stock_breakout.py

#====== FUNCS =====

def dailyClosePricesbyPeriod(ticker,str_period='5y'):
    #['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y','5y', 'ytd', 'max']
    df = yf.download(ticker, period=str_period)
    df.reset_index(inplace=True)
    df.columns = ['Date','Close','High','Low','Open','Volume']
    #df['ticker']=ticker
    return df


def simpleMovingAveragesClosePrice(df):
    df['sma10'] = df['Close'].rolling(window=10).mean()
    df['sma20'] = df['Close'].rolling(window=20).mean()
    df['sma50'] = df['Close'].rolling(window=50).mean()
    return df.sort_values(by=['Date'],ascending=[False])


def exponentialMovingAveragesClosePrice(df):
    df['EMA10']= df['Close'].ewm(span=10).mean()
    df['EMA20']= df['Close'].ewm(span=20).mean()
    df['EMA50']= df['Close'].ewm(span=50).mean()
    df['EMA150']= df['Close'].ewm(span=150).mean()
    return df.sort_values(by=['Date'],ascending=[False])
    

def findBreakOut(df,ticker):
    ticker = ticker[0]
    qry = """
                SELECT 
                '{ticker}' AS ticker
                ,*
                ,CASE 
                WHEN Close > EMA10 AND Close > EMA20 AND Close > EMA50 THEN 'Yes'
                ELSE 'No' END AS 'break_out'

                ,CASE 
                WHEN Close < EMA150 THEN 'Yes'
                ELSE 'No' END AS break_down_150ema
                
                FROM df
                """.format(ticker=ticker)
    return sqldf(qry,locals())

def breakOutSignals(df):
    qry="""
        SELECT *
        ,LAG ( break_out,1,0) OVER ( ORDER BY Date ) AS prev1
        ,LAG ( break_out,2,0) OVER ( ORDER BY Date ) AS prev2
        ,LAG ( break_out,3,0) OVER ( ORDER BY Date ) AS prev3
        FROM df
        ORDER BY Date DESC
        """
    
    qry2="""
        SELECT *
        
        ,CASE
        WHEN break_out = 'Yes' AND prev1 = 'Yes' AND prev2 = 'Yes' AND prev3 = 'No' THEN 'Buy'
        ELSE '' END AS Flag_Buy
        
        ,CASE
        WHEN prev1 = 'Yes'AND prev2 = 'Yes' AND prev3 = 'Yes' AND break_out = 'No' THEN 'Sell'
        ELSE '' END AS Flag_Sell
        FROM df
        """
    
    qry3 =  """
            SELECT *
            ,CASE
            WHEN Flag_Buy='Buy' THEN 'Yes Buy'
            WHEN Flag_Sell = 'Sell' THEN 'Sell'
            ELSE break_out END AS break_out_signal
            FROM df
            """
    
    
    df = sqldf(qry,locals())
    df = sqldf(qry2,locals())
    df = sqldf(qry3,locals())
    return df
  
  
  

st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

                     
                       
                       
st.title('Stock Break Outs & Financials')
st.markdown("""#### Break Out: Close Price above 10EMA, 20EMA, 50EMA """)
st.markdown("#####")
st.link_button("Go to Last 3 Day BreakOut Stock Screener", "https://rizal-3day-stock-breakout.streamlit.app/")


#ticker = st.multiselect('Select a ticker:',ticker_list,['QCOM'])#,disabled=True)  
#st.markdown("##")
ticker_list = SP500tickers(extra_ticker_list)
   

st.markdown("####")
ticker = [st.selectbox('Select a ticker:',ticker_list)]#,index=None)  


#====== DOWNLOAD TICKER DATA =========
df = dailyClosePricesbyPeriod(ticker)
df = exponentialMovingAveragesClosePrice(df)
df = findBreakOut(df,ticker)  
df = breakOutSignals(df)

lastBreakOutSignal = df['break_out_signal'][0]
break_down_150ema = df['break_down_150ema'][0]



recent_df = fetchRecent(ticker,recent_ls)
qtr_df = financials_quarter(ticker)

longBusinessSummary = recent_df['longBusinessSummary'].values[0]
forwardPE = round(recent_df['forwardPE'][0],2)
trailingPE = round(recent_df['trailingPE'][0],2)
revenueGrowth = round(recent_df['revenueGrowth'][0],4)
operatingMargins = round(recent_df['operatingMargins'][0],4)
returnOnEquity = round(recent_df['returnOnEquity'][0],4)
debt_ratio = round(recent_df['debt_ratio'][0],4)

marketCap = recent_df['marketCap'][0]
shortName = recent_df['shortName'][0]
industry = recent_df['industry'][0]



#st.markdown("#####")
st.markdown("#####")
col1, col2, col3 = st.columns(3)#, border=True)
# ================== RED FLAGS ! ==========================
#st.markdown("#####")
with col1:
    st.write(f'__:classical_building:   {shortName}__ ')
    #st.write(f'* __{shortName}__')
    st.write('* __Industry:__  ',industry)
    st.write('* __MarketCap:__  ',round(marketCap/1000000000,2),'__billion__' )
    st.write('* __ForwardPE:__  ',forwardPE)
    st.write(f'* __Break Out Signal:__  {lastBreakOutSignal}',)

#st.markdown("#####")
#st.markdown("#####")

with col2:
    st.write("__:large_red_square:  Red Flags  (if exist):__")
    #if forwardPE > trailingPE and trailingPE!=0: st.write('* __forwardPE:__ ', forwardPE, ' > trailingPE: ', trailingPE,' :x:')
    if debt_ratio >=0.33 :
        st.write('* __debt_ratio:__  ',round(debt_ratio*100,1),'__%__',' :x:')
    if revenueGrowth < 0 :
        st.write('* __revenueGrowth:__  ',round(revenueGrowth*100,1),'__%__',' :x:')
    if returnOnEquity < 0.1 :
        st.write('* __returnOnEquity:__  ',round(returnOnEquity*100,1),'__%__',':x:')
    if operatingMargins < 0.1 :
        st.write('* __operatingMargins:__  ',round(operatingMargins*100,1),'__%__',' :x:')
    if break_down_150ema == 'Yes':
        st.write('* __Below 150EMA!__ :x:')


#st.markdown("#####")
#st.markdown("#####")
with col3:
    st.write("__:large_green_circle:  Green Flags (if exist):__")
    if revenueGrowth >= 0.1 :
        st.write('* __revenueGrowth:__ ',round(revenueGrowth*100,1),'__%__',':heavy_check_mark:')
    if returnOnEquity >= 0.2 :
        st.write('* __returnOnEquity:__ ',round(returnOnEquity*100,1),'__%__',':heavy_check_mark:')
    if operatingMargins >= 0.2 :
        st.write('* __operatingMargins:__',round(operatingMargins*100,1),'__%__',':heavy_check_mark:')
    if break_down_150ema == 'No':
        st.write('* __Above 150EMA:  Yes!__ :heavy_check_mark:')

    if break_down_150ema == 'No' and lastBreakOutSignal in ['Yes','Yes Buy']:
        st.write('* __Above 150,50,20,10 EMA:  Yes!__ :heavy_check_mark:')
    


st.markdown("#####")
#================== Daily Close Price Scatter Plot ==================
closeTitle = ticker[0] + ' Daily Close Prices'

fig_close_prices = px.scatter(df, x="Date", y="Close"
                                , color="break_out_signal"
                                #, symbol = 'break_down_150ema'
                                , color_discrete_map = {'Yes':'green'
                                                       ,'Yes Buy':'yellow'
                                                       ,'No':'grey'
                                                       ,'Sell': 'red'
                                                      }
                                #,color_discrete_sequence = ['red','blue']
                                , title = closeTitle )




#fig_close_prices = go.Figure(fig_close_prices_scatter.data+fig_150ema_line.data)
st.plotly_chart(fig_close_prices, key="scatter1")#, on_select="rerun")

#================ Daily Volume Bar Chart ================= 
volumeTitle = ticker[0] + ' Volume'
fig_volume = px.bar(df, x="Date", y="Volume" 
                        #,color="break_out",color_discrete_map = {'Yes':'green','No':'grey'}
                        , color="break_out_signal"
                        , color_discrete_map = {'Yes':'green'
                                               ,'Yes Buy':'yellow'
                                               ,'No':'grey'
                                               ,'Sell': 'red'
                                              }
                       ,title =  volumeTitle)
st.plotly_chart(fig_volume,key='bar1')


breakout_cols = ['ticker','Date','Open','Close','Volume'
                 ,'EMA10','EMA20','EMA50','EMA150'
                 #,'break_out'
                 ,'break_out_signal','break_down_150ema']
st.dataframe(df[breakout_cols])


cols = ['date','ticker','shortName','net_interest_income_ratio','interest_income_ratio','debt_to_ebitda'
    ,'gross_margin','npat_margin'
    ,'Total Revenue','Net Income','Accounts Receivable','Free Cash Flow','EBITDA'
    ,'Cash And Cash Equivalents','Capital Expenditure'
   ]



st.markdown("##")
st.markdown("""## Recent Financials""")

#========= RECENT & QTR FINANCE TABLES ===================
st.dataframe(recent_df)
st.dataframe(qtr_df[cols],use_container_width=True)







# ======================== TAB 1 BAR CHARTS ===================  
st.markdown("##")

col1_chart, col2_chart = st.columns(2)

#col1_chart.write('\nTotal Revenue')
fig_revenue = px.bar(qtr_df, x="date", y="Total Revenue", color="shortName", title = 'Total Revenue' )
col1_chart.plotly_chart(fig_revenue, key="ticker1")#, on_select="rerun")

#col2_chart.write('\nNet Income')
fig_netincome = px.bar(qtr_df, x="date", y="Net Income", color="shortName", title='Net Income')
col2_chart.plotly_chart(fig_netincome, key="ticker2")#, on_select="rerun")



col1_chart_a, col2_chart_a = st.columns(2)

#col1_chart_a.write('\nFree Cash Flow')
fig_fcf = px.bar(qtr_df, x="date", y="Free Cash Flow", color="shortName", title='Free Cash Flow')
col1_chart_a.plotly_chart(fig_fcf, key="ticker4")#, on_select="rerun")

#col2_chart_a.write('\nAccounts Receivable')
fig_act = px.bar(qtr_df, x="date", y="Accounts Receivable", color="shortName", title='Accounts Receivable')
col2_chart_a.plotly_chart(fig_act, key="ticker5")#, on_select="rerun")



col1_chart_b, col2_chart_b = st.columns(2)

#col1_chart_b.write('\nCash And Cash Equivalents')
fig_cash = px.bar(qtr_df, x="date", y="Cash And Cash Equivalents", color="shortName", title='Cash And Cash Equivalents')
col1_chart_b.plotly_chart(fig_cash, key="ticker3")#, on_select="rerun")

#col2_chart_b.write('\nCapital Expenditure')
fig_capex = px.bar(qtr_df, x="date", y="Capital Expenditure", color="shortName",title='Capital Expenditure')
col2_chart_b.plotly_chart(fig_capex, key="ticker6")#, on_select="rerun")

#dailyClosePrice_df  = closingPricesDaily(ticker[0])
#fig_line = px.line(dailyClosePrice_df, x="Date", y="Close", title='Daily Close Price')#, color="green")
#st.plotly_chart(fig_line, key="ticker7")#, on_select="rerun")
#st.dataframe(dailyClosePrice_df)

st.write('Company Profile:')
st.write(longBusinessSummary)

