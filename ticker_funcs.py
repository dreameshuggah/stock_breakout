#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np

#from IPython.display import display
#pd.options.display.max_columns = None
#pd.options.display.max_rows = 30
#pd.get_option("display.max_rows")
#pd.set_option('display.max_rows', 100)

from pandasql import sqldf
import yfinance as yf



# FUNCS

#========= break out stock ================
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

#======== SHARE PRICE & COUNTS ================

def closingPricesDaily(ticker):
    df = yf.download(ticker, period="5y")
    if len(df)>0:
        df.reset_index(inplace=True)
        df['Ticker']= ticker
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df = df[['Ticker','Date','Close']].sort_values(by=['Date'],ascending=False)
    else:
        df = pd.DataFrame()
    return df


def closingPrices(ticker):
    df = yf.download(ticker, period="5y")
    df.reset_index(inplace=True)
    #print(df.columns)
    #print('daily data shape: ',df.shape)
    df = df[['Date','Close']]
    df = sqldf("""  SELECT 
                    '{ticker}' AS ticker
                    ,Date AS date
                    ,Close AS close_price
                    ,strftime('%Y', date)||'-'||strftime('%m', date) AS ym
                    FROM df a
                    INNER JOIN (SELECT 
                                MAX(Date) AS maxdate
                                FROM df
                                GROUP BY strftime('%Y', Date)||'-'||strftime('%m', Date)
                                ) b ON a.Date = b.maxdate
              """.format(ticker=ticker),locals())
    #print('before:',df.shape)
    df = df.drop_duplicates(subset=['date'],keep='last')
    #print('after:',df.shape)
    return df




def sharesCount(ticker,start_date = "2018-12-1"):
    # func for share counts last day of the month
    # download n shares
    stock = yf.Ticker(ticker)
    df = stock.get_shares_full(start=start_date, end=None)
    df = df.to_frame()
    df.reset_index(inplace=True)
    df.rename(columns={0: "n_shares","index": "date"}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    
    # fetch max date per month
    df =sqldf("""
                        SELECT 
                        '{ticker}' AS ticker
                        ,date
                        ,n_shares
                        ,strftime('%Y', date)||'-'||strftime('%m', date) AS ym
                        FROM df a
                        INNER JOIN (SELECT 
                                    MAX(Date) AS maxdate
                                    FROM df
                                    GROUP BY strftime('%Y', date)||'-'||strftime('%m', date)
                                    ) b ON a.Date = b.maxdate
                        """.format(ticker=ticker),locals())
    #print('before:',df.shape)
    df = df.drop_duplicates(subset=['date'],keep='last')
    #print('after:',df.shape)
    return df



def combineClosePriceSharesCount(ticker):
    close_df = closingPrices(ticker)
    n_shares_df = sharesCount(ticker)
    df = sqldf("""
                SELECT
                a.ticker
                ,a.ym
                ,a.close_price
                ,b.n_shares
                ,a.date AS date_close_price
                ,b.date AS date_n_shares
                ,a.close_price * b.n_shares AS market_cap
                FROM close_df a
                INNER JOIN n_shares_df b ON a.ym = b.ym
                ORDER BY a.ym DESC
                """,locals())
    return df




def closePriceSharesCount(ticker_list):
    df = pd.DataFrame()
    for ticker in ticker_list:
        #print(ticker)
        tmp_df = combineClosePriceSharesCount(ticker)
        tmp_df = tmp_df[tmp_df['ticker'].notnull()]
        if len(tmp_df)>0:
            df = pd.concat([df,tmp_df])
    return df


def closePriceDailyByList(ticker_list):
    df = pd.DataFrame()
    for ticker in ticker_list:
        #print(ticker)
        tmp_df = closingPricesDaily(ticker)
        tmp_df = tmp_df[tmp_df['Ticker'].notnull()]
        if len(tmp_df)>0:
            df = pd.concat([df,tmp_df])
    return df


#========== QUARTERLY FINANCIALS ===========
import streamlit as st
@st.cache_data
def financials_quarter(ticker_list):
    qtr_cols = list(set(['ticker','shortName','sector','industry','Total Assets','Total Liabilities Net Minority Interest'
            ,'Other Intangible Assets','Total Debt','Interest Income','Total Revenue'
            ,'Current Assets','Current Liabilities'
            ,'Gross Profit','Operating Income','Total Equity Gross Minority Interest'
            ,'EBIT','EBITDA','Interest Expense','Working Capital','Retained Earnings'
            ]))
    
    df = pd.DataFrame(columns=qtr_cols)
    for ticker in ticker_list:
        #print(ticker)
        # Get the ticker object
        stock = yf.Ticker(ticker)
        if 'sector' not in stock.info.keys():
            sector = np.nan 
        else:
            sector = stock.info['sector']
        
        if 'industry' not in stock.info.keys():
            industry = np.nan 
        else:
            industry = stock.info['industry']
        
        if 'shortName' not in stock.info.keys():
            shortName = np.nan 
        else:
            shortName = stock.info['shortName']
        #print(shortName,sector,industry)

        # Get the balance sheet
        balancesheet_df = stock.quarterly_balance_sheet.transpose()
        balancesheet_df.reset_index(inplace=True)
        balancesheet_df.rename(columns={"index": "date"}, inplace=True)
        
        # Get the income statement
        income_df = stock.quarterly_income_stmt.transpose()
        income_df.reset_index(inplace=True)
        income_df.rename(columns={"index": "date_b"}, inplace=True)
        
        # Get the cashflow statement
        cashflow_df = stock.quarterly_cashflow.transpose()
        cashflow_df.reset_index(inplace=True)
        cashflow_df.rename(columns={"index": "date_c"}, inplace=True)
        
        #COMBINE
        tmp_df = sqldf("""SELECT 
                  '{ticker}' AS ticker
                  ,'{shortName}' AS shortName
                  ,'{sector}' AS sector
                  ,'{industry}' AS industry
                  ,* 
                  FROM balancesheet_df a 
                  LEFT JOIN income_df b ON a.date = b.date_b
                  LEFT JOIN cashflow_df c ON a.date = c.date_c
                  """.format(ticker=ticker,shortName=shortName,sector=sector,industry=industry)
               ,locals())
        tmp_df.drop(columns=['date_b','date_c'])
        
        #print(tmp_df.shape)
        df =pd.concat([df,tmp_df]).reset_index(drop=True)
        
    df.dropna(subset=['Total Revenue'], inplace=True)
    
    
    
    # interest income ratio
    qry = """
          SELECT
            `Total Assets`- `Total Liabilities Net Minority Interest` - `Other Intangible Assets` 
            AS tangible_net_worth

            --,`Total Debt`/market_cap AS debt_ratio

            ,`Interest Income`/`Total Revenue` AS interest_income_ratio
            
            ,`Net Interest Income`/`Total Revenue` AS net_interest_income_ratio

            ,`Current Assets`/`Current Liabilities` AS current_liquidity

            ,`Gross Profit`/`Total Revenue` AS gross_margin

            ,`Operating Income`/`Total Revenue` AS operating_profit_of_the_sales

            ,`Total Revenue`/`Total Assets` AS assets_turnover

            ,`Total Revenue`/`Current Assets` AS current_assets_turnover


            ,`Total Equity Gross Minority Interest`/`Total Liabilities Net Minority Interest` 
            AS capital_ratio

            ,`Total Equity Gross Minority Interest`/`Current Liabilities` 
            AS coverage_of_short_term_liabilities_by_equity 

            ,`Net Income`/`Total Revenue` AS npat_margin

            ,EBIT/`Interest Expense` AS interest_cover

            ,`Total Liabilities Net Minority Interest` / (`Total Assets`- `Total Liabilities Net Minority Interest` - `Other Intangible Assets`)
            AS total_liabilities_to_tangible_networth

            ,`Total Debt`/ EBITDA AS debt_to_ebitda

            ,`Working Capital`/`Total Revenue` AS working_capital_to_sales

            ,`Working Capital`/`Total Assets`  AS A_LIQUIDITY
            ,`Retained Earnings`/`Total Assets` AS B_PROFITABILITY
            , EBIT/`Total Assets` AS C_OPERATING_EFFICIENCY
            --, market_cap/`Total Liabilities Net Minority Interest` AS D_INDEBTNESS

            -- ASSETS TURNOVER
            , `Total Revenue`/`Total Assets` AS E_PRODUCTIVITY 
            ,* FROM df
            """
    #print(qry)
    df= sqldf(qry,locals())
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df



def latestRatios(df):
    # for left join to yahoo stats 
    interest_income_ratio_df = sqldf("""
                                    SELECT 
                                    a.ticker AS ticker_b
                                    ,a.interest_income_ratio
                                    ,a.net_interest_income_ratio
                                    --,a.perc_chg_total_revenue
                                    --,a.Zone
                                    FROM df a
                                    INNER JOIN (
                                                SELECT
                                                ticker
                                                ,max(date) AS max_date
                                                FROM df
                                                GROUP BY 1
                                              ) b on a.ticker = b.ticker AND a.date = b.max_date
                                    """,locals())
    interest_income_ratio_df['interest_income_ratio']=interest_income_ratio_df['interest_income_ratio'].fillna(0)
    interest_income_ratio_df['net_interest_income_ratio']=interest_income_ratio_df['net_interest_income_ratio'].fillna(0)
    return interest_income_ratio_df


# In[4]:


recent_ls = ['shortName'
            ,'industry'
            ,'shortRatio'
            ,'trailingPE','forwardPE'    
            ,'currentPrice','fiftyTwoWeekLow','fiftyTwoWeekHigh'
            ,'targetMedianPrice','targetHighPrice'
            ,'fiftyDayAverage','twoHundredDayAverage'
            
            ,'returnOnEquity','returnOnAssets','operatingMargins','ebitdaMargins'
            ,'revenueGrowth'
            ,'totalDebt','marketCap','freeCashflow'
            ,'debtToEquity'
            ,'longBusinessSummary','sector'
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
        #print(ticker)
        tmp_df = recentTickerFinance(ticker,recent_ls)
        df = pd.concat([df,tmp_df])
    return df.fillna(0)




def marketTrend(df):
    qry="""
        SELECT 

        CASE 
        WHEN perc_Chg_52WkHigh > -10 AND perc_Chg_52WkHigh <= -5 THEN 'Dip'
        WHEN perc_Chg_52WkHigh > -20 AND perc_Chg_52WkHigh <= -10 THEN 'Correction'
        WHEN perc_Chg_52WkHigh <= -20 THEN 'Bearish'
        ELSE '-' END AS market_trend
        ,* 
        FROM df
        """
    return sqldf(qry,locals())




import streamlit as st
@st.cache_data
def fetchRecent(ticker_list,recent_ls):
    df = recentFinance(ticker_list,recent_ls)
    
    qry_recent_ratios = """
                    SELECT
                    ROUND(  (currentPrice-fiftyTwoWeekHigh)/fiftyTwoWeekHigh  ,4)*100 AS perc_Chg_52WkHigh
                    ,ROUND((targetMedianPrice/currentPrice)-1,4)*100 AS upside_Perc_targetMedianPrice
                    ,totalDebt/marketCap AS debt_ratio
                    ,*
                    FROM df 
                    """
    df = sqldf(qry_recent_ratios,locals())
    return marketTrend(df)





def filterBuyDf(df,forwardPE_cutoff):
    qry="""
        SELECT * 
        FROM df

        WHERE debt_ratio < 0.33
        AND operatingMargins >= 0.1
        --AND perc_Chg_52WkHigh < -20
        AND forwardPE < {forwardPE_cutoff}
        
        ORDER BY revenueGrowth DESC--forwardPE
        """.format(forwardPE_cutoff=forwardPE_cutoff)


    buy_df = sqldf(qry,locals())
    return buy_df

import streamlit as st
@st.cache_data
def filterNetIncomeRatio(buy_df,interest_income_ratio_df):
    buy_df = sqldf("""
                SELECT *
                FROM buy_df a
                LEFT JOIN interest_income_ratio_df b ON a.ticker = b.ticker_b
                WHERE b.interest_income_ratio < 0.05 
                AND b.net_interest_income_ratio < 0.05
                """,locals())
    buy_df = buy_df.drop(columns=['ticker_b'])
    return buy_df










