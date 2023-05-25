import os, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint
from kisapi import KoreaInvestment
from collections import defaultdict
from datetime import datetime, timedelta, date

def backtest(df):
    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['noise'] = 1 - abs(df['open']-df['close']) / (df['high']-df['low'])
    df['noise20'] = df['noise'].rolling(window=20).mean()[-2]
    df['range'] = (df['high'] - df['low']) * 0.5
    df['target'] = df['open'] + df['range'].shift(1)
    df['bull'] = df['open'] > df['ma5']

    fee = 0.0005
    df['ror'] = np.where((df['high'] > df['target']) & df['bull'], df['close'] / df['target'] - fee, 1)

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    return df

def get_backtest_kor(kis, ticker, start, end):
    column = ['open', 'high', 'low', 'close']
    data = defaultdict(list)
    dates = []
    flag = False
    while True:
        first = end-timedelta(days=100) if (end-start).days > 100 else start
        res = kis.fetch_ohlcv(ticker, start_day=first.strftime('%Y%m%d'), end_day=end.strftime('%Y%m%d'))
        for ohlcv in res['output2']:
            try:
                strdate = ohlcv['stck_bsop_date']
            except:
                flag = True; break
            yy, mm, dd = int(strdate[:4]), int(strdate[4:6]), int(strdate[6:8])
            d = date(yy, mm, dd)
            if not strdate or d < start: 
                flag = True; break
            dates.append(d)
            data['open'].append(float(ohlcv['stck_oprc']))
            data['high'].append(float(ohlcv['stck_hgpr']))
            data['low'].append(float(ohlcv['stck_lwpr']))
            data['close'].append(float(ohlcv['stck_clpr']))
        if flag:
            break
        end = first-timedelta(days=1)
        
    df = pd.DataFrame(data, columns=column, index=dates).sort_index()
    return backtest(df), res['output1']['hts_kor_isnm']
    
def get_backtest_usa(kis, ticker, start, end):
    column = ['open', 'high', 'low', 'close']
    data = defaultdict(list)
    dates = []
    flag = False
    while True:
        first = end-timedelta(days=100) if (end-start).days > 100 else start
        res = kis.fetch_ohlcv(ticker, start_day=first.strftime('%Y%m%d'), end_day=end.strftime('%Y%m%d'))
        for ohlcv in res['output2']:
            strdate = ohlcv['xymd']
            yy, mm, dd = int(strdate[:4]), int(strdate[4:6]), int(strdate[6:8])
            d = date(yy, mm, dd)
            if not strdate or d < start: 
                flag = True; break
            dates.append(d)
            data['open'].append(float(ohlcv['open']))
            data['high'].append(float(ohlcv['high']))
            data['low'].append(float(ohlcv['low']))
            data['close'].append(float(ohlcv['clos']))
        if flag:
            break
        end = first-timedelta(days=1)
        
    df = pd.DataFrame(data, columns=column, index=dates).sort_index()
    return backtest(df)
        

if __name__ == "__main__":
    API_KEY = os.environ.get("SIMUL_KEY")
    API_SEC = os.environ.get("SIMUL_SEC")
    ACC_NUM = os.environ.get("SIMUL_ACC")
    
    kis = KoreaInvestment(api_key=API_KEY, api_secret=API_SEC, acc_no=ACC_NUM, mock=True, exchange="미국전체")
    tickers = ["TQQQ", "TSLA", "NVDA"]
    start = datetime(2021, 3, 1)
    end = datetime(2023, 5, 20)
    for ticker in tickers:
        df = get_backtest(kis, ticker, start, end)
