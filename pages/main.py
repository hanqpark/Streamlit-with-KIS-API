import os
import streamlit as st
# from dotenv import load_dotenv
from kisapi import KoreaInvestment
from pages import *


target_pct_kor = {
    'SK하이닉스': 0.2,
    'POSCO홀딩스': 0.2,
    '삼성바이오로직스': 0.1,
    'KODEX 코스닥150레버리지': 0.1,
    'LG에너지솔루션': 0.2,
    '에코프로비엠': 0.1,
    '엘앤에프': 0.1
}

target_pct_usa = {
    'PFE': 0.1,
    'TSLA': 0.1,
    'T': 0.1,
    'O': 0.1,
    'BAC': 0.1,
    'GOOGL': 0.05 ,
    'IBM': 0.1,
    'NVDA': 0.1,
    'NFLX': 0.05 ,
    'XOM': 0.1,
    'SBUX': 0.1
}

if __name__ == "__main__":
    # load_dotenv()
    # API_KEY = os.environ.get("SIMUL_KEY")
    # API_SEC = os.environ.get("SIMUL_SEC")
    # ACC_NUM = os.environ.get("SIMUL_ACC")
    API_KEY = st.secrets["SIMUL_KEY"]
    API_SEC = st.secrets["SIMUL_SEC"]
    ACC_NUM = st.secrets["SIMUL_ACC"]

    kis_kor = KoreaInvestment(api_key=API_KEY, api_secret=API_SEC, acc_no=ACC_NUM, mock=True)
    kis_usa = KoreaInvestment(api_key=API_KEY, api_secret=API_SEC, acc_no=ACC_NUM, mock=True, exchange="미국전체")

    page_names_to_funcs = {
        "한국투자 Open API with Streamlit": intro,
        "한국주식 리밸런싱": rebalancing_kor,
        "미국주식 리밸런싱": rebalancing_usa,
        "한국주식 백테스팅": backtesting_kor,
        "미국주식 백테스팅": backtesting_usa,
    }

    demo_name = st.sidebar.selectbox("예시 선택", page_names_to_funcs.keys())
    if "한국" in demo_name:
        page_names_to_funcs[demo_name](page_names_to_funcs, kis_kor, target_pct_kor)
    elif "미국" in demo_name:
        page_names_to_funcs[demo_name](page_names_to_funcs, kis_usa, target_pct_usa)
        