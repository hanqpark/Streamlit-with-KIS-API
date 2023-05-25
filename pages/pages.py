import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from collections import defaultdict
from backtest import get_backtest_kor, get_backtest_usa


def intro(page_names_to_funcs, kis, target_percents):
    st.write("# 한국투자 Open API with Streamlit")
    st.sidebar.success("예시를 선택해 주세요")
    st.markdown(
        """
        ### 한국투자 Open API
        - 한국투자증권의 트레이딩 서비스를 Open API로 제공하여 개발자들이 다양한 금융 서비스를 만들 수 있도록 지원합니다. 
        - KIS Developers 사이트 내 [API 문서](https://apiportal.koreainvestment.com/apiservice)
        에서 상세한 설명와 예제를 통해 전문 개발자가 아닌 일반인들도 쉽게 금융 서비스를 만들 수 있습니다.
        - 한국투자 Open API의 특장점은 다음과 같습니다.
        """
    )
    st.image('images/kis_open_api.png')
    st.markdown(
        """
        ### Streamlit
        - Streamlit은 Data Science 프로젝트를 위해 만들어진 Open-source app framework 입니다.
        - 사용자가 작성한 Data script를 Wep App으로 변환하여 쉽고 빠르게 공유할 수 있습니다.
        - Front-end를 몰라도 오직 Python으로만 구현 및 실행이 가능합니다.
        """
    )
    st.markdown(
        """
        ### 참고한 사이트
        - [KIS Developers API Documentation](https://apiportal.koreainvestment.com/apiservice)
        - [파이썬을 이용한 한국/미국 주식 자동매매 시스템](https://wikidocs.net/book/7845)
        - [Mojito 파이썬 라이브러리](https://github.com/sharebook-kr/mojito)
        - [Streamlit API Documentation](https://docs.streamlit.io)
        """
    )


def rebalancing_kor(page_names_to_funcs, kis, target_percents):
    """ 
    데이터 처리 작업 
    """
    # create a current portfolio dataframe
    balance = kis.fetch_balance()
    pf_data = defaultdict(list)
    for comp in balance['output1']:
        pf_data['종목코드'].append(comp['pdno'])
        pf_data['종목명'].append(comp['prdt_name'])
        pf_data['매입평균가격'].append(f"{int(float(comp['pchs_avg_pric']))}원")
        pf_data['현재가'].append(f"{comp['prpr']}원")
        pf_data['보유수량'].append(f"{comp['hldg_qty']}주")
        pf_data['매입금액'].append(f"{comp['pchs_amt']}원")
        pf_data['평가금액'].append(comp['evlu_amt'])
        pf_data['평가손익금액'].append(f"{comp['evlu_pfls_amt']}원")
        pf_data['평가손익율'].append(f"{comp['evlu_pfls_rt']}%")
    pf_df = pd.DataFrame(pf_data)

    # create a portfolio rebalancing dataframe
    total_buy = sum(float(comp['pchs_amt']) for comp in balance['output1'])
    total_value = sum(float(comp['evlu_amt']) for comp in balance['output1'])
    rb_data = defaultdict(list)
    for comp in balance['output1']:
        rb_data['종목코드'].append(comp['pdno'])
        rb_data['종목명'].append(comp['prdt_name'])
        rb_data['현재가'].append(f"{comp['prpr']}원")
        rb_data['보유수량'].append(f"{comp['hldg_qty']}주")
        rb_data['평가금액'].append(comp['evlu_amt'])
        
        tg_rt = target_percents[comp['prdt_name']]
        rb_data['목표비율'].append(f"{tg_rt * 100}%")
        
        cr_rt = round(float(comp['evlu_amt']) / total_value , 2)
        rb_data['현재비율'].append(f"{round(cr_rt * 100, 2)}%")
        
        diff_rt = round(cr_rt - tg_rt, 2)
        rb_data['차이'].append(f"{diff_rt * 100}%")
        rb_data['매수/매도'].append( round( -total_value * diff_rt / float(comp['prpr']) ) )
    rb_df = pd.DataFrame(rb_data)
    
    # create a total returns dataframe
    output = balance['output2'][0]
    total_data = {
        "총 매수금액": f'{"{:,}".format(int(output["pchs_amt_smtl_amt"]))}원',
        "총 평가금액": f'{"{:,}".format(int(output["evlu_amt_smtl_amt"]))}원',
        "총 평가손익": f'{"{:,}".format(int(output["evlu_pfls_smtl_amt"]))}원',
        "총 평가손익률": f'{round( ( int(total_value) - int(total_buy) ) / total_buy * 100 , 2)}%'
    }
    total_df = pd.DataFrame.from_dict([total_data])
    
    """ 
    마크다운 작성
    """
    st.markdown(f'# {list(page_names_to_funcs.keys())[1]}')
    st.sidebar.success("다른 예시를 선택해 보세요")
    st.write(
        """
        Hello World!
        """
    )
    st.write('## 현재 포트폴리오')
    st.write(total_df)
    
    # visualize the portfolio with a pie chart
    fig = px.pie(pf_df, values='평가금액', names='종목명')
    st.plotly_chart(fig)
    
    # Table
    st.write(pf_df)
    
    st.write('## 포트폴리오 리밸런싱')
    st.write(rb_df)


def rebalancing_usa(page_names_to_funcs, kis, target_percents):
    """ 
    데이터 처리 작업 
    """
    # create a current portfolio dataframe
    balance = kis.fetch_balance()
    pf_data = defaultdict(list)
    for comp in balance['output1']:
        pf_data['종목코드'].append(comp['ovrs_pdno'])
        pf_data['종목명'].append(comp['ovrs_item_name'])
        pf_data['매입평균가격'].append(f"${float(comp['pchs_avg_pric'])}")
        pf_data['현재가'].append(f"${round(float(comp['now_pric2']), 2)}")
        pf_data['보유수량'].append(f"{comp['ovrs_cblc_qty']}주")
        pf_data['매입금액'].append(f"${round(float(comp['frcr_pchs_amt1']), 2)}")
        pf_data['평가금액'].append(round(float(comp['ovrs_stck_evlu_amt']), 2))
        pf_data['평가손익금액'].append(f"${round(float(comp['frcr_evlu_pfls_amt']), 2)}")
        pf_data['평가손익율'].append(f"{comp['evlu_pfls_rt']}%")
    pf_df = pd.DataFrame(pf_data)

    # create a portfolio rebalancing dataframe
    total_buy = sum(float(comp['frcr_pchs_amt1']) for comp in balance['output1'])
    total_value = sum(float(comp['ovrs_stck_evlu_amt']) for comp in balance['output1'])
    rb_data = defaultdict(list)
    for comp in balance['output1']:
        rb_data['종목코드'].append(comp['ovrs_pdno'])
        rb_data['종목명'].append(comp['ovrs_item_name'])
        rb_data['현재가'].append(f"${round(float(comp['now_pric2']), 2)}")
        rb_data['보유수량'].append(f"{comp['ovrs_cblc_qty']}주")
        rb_data['평가금액'].append(round(float(comp['ovrs_stck_evlu_amt']), 2))
        
        tg_rt = target_percents[comp['ovrs_pdno']]
        rb_data['목표비율'].append(f"{tg_rt * 100}%")
        
        cr_rt = round(float(comp['ovrs_stck_evlu_amt']) / total_value, 2)
        rb_data['현재비율'].append(f"{cr_rt * 100}%")
        
        diff_rt = round(cr_rt - tg_rt, 2)
        rb_data['차이'].append(f"{diff_rt * 100}%")
        rb_data['매수/매도'].append( round( -total_value * diff_rt / float(comp['now_pric2']) ) )
    rb_df = pd.DataFrame(rb_data)
    
    # create a total returns dataframe
    total_data = {
        "총 매수 금액": f'${"{:,}".format(total_buy)}',
        "총 평가 금액": f'${"{:,}".format(round(total_value, 2))}',
        "총 평가 손익": f'${"{:,}".format(round(float(total_value) - float(total_buy), 2))}',
        "총 평가 손익율": f'{round( ( int(total_value) - int(total_buy) ) / total_value * 100 , 2)}%'
    }
    total_df = pd.DataFrame.from_dict([total_data])
    
    """ 
    마크다운 작성
    """
    st.markdown(f"# {list(page_names_to_funcs.keys())[2]}")
    st.sidebar.success("다른 예시를 선택해 보세요")
    st.write(
        """
        Hello World!
        """
    )
    st.write('## 현재 포트폴리오')
    st.write(total_df)
    
    # visualize the portfolio with a pie chart
    fig = px.pie(pf_df, values='평가금액', names='종목명')
    st.plotly_chart(fig)
    
    # Table
    st.write(pf_df)
    
    st.write('## 포트폴리오 리밸런싱')
    st.write(rb_df)


def backtesting_kor(page_names_to_funcs, kis, target_percents=None):
    st.markdown(f"# {list(page_names_to_funcs.keys())[3]}")
    st.sidebar.success("다른 예시를 선택해 보세요")
    st.write(
        """
        한국주식으로 변동성 돌파매매 백테스팅 구현
        """
    )
    # Define the start and end dates for the backtest
    start_date = st.sidebar.date_input("시작 날짜", datetime.date(2019, 1, 1))
    end_date = st.sidebar.date_input("종료 날짜", datetime.date(2023, 1, 1))
    
    # Define the initial_investment, rebalancing frequency and threshold
    tickers = st.sidebar.text_input('종목 입력 - 콤마( , )로 구분', '000660, 247540, 122630, 233740')
    tickers = list(ticker.strip().upper() for ticker in tickers.split(","))
    
    for ticker in tickers:
        try:
            df, stock_name = get_backtest_kor(kis, ticker, start_date, end_date)
            st.header(f"{stock_name} ({ticker})")
            mdd, hpr = st.columns(2)
            with hpr:
                st.subheader("누적 수익률")
                st.markdown(f"**:red[{round(df['hpr'][-2]*100, 2)}] %**")
            st.line_chart(df, y="hpr")
            with mdd:
                st.subheader("Max DrawDown")
                st.write(f"**:red[{round(df['dd'].max(), 2)}] %**")
        except ValueError:
            st.subheader(f"{ticker} 종목의 정보를 불러올 수 없습니다.")


def backtesting_usa(page_names_to_funcs, kis, target_percents=None):
    st.markdown(f"# {list(page_names_to_funcs.keys())[4]}")
    st.sidebar.success("다른 예시를 선택해 보세요")
    st.write(
        """
        미국주식으로 변동성 돌파매매 백테스팅 구현
        """
    )
    # Define the start and end dates for the backtest
    start_date = st.sidebar.date_input("시작 날짜", datetime.date(2019, 1, 1))
    end_date = st.sidebar.date_input("종료 날짜", datetime.date(2023, 1, 1))
    
    # Define the initial_investment, rebalancing frequency and threshold
    tickers = st.sidebar.text_input('종목 입력 - 콤마( , )로 구분', 'TQQQ, TSLA, NVDA')
    tickers = list(ticker.strip().upper() for ticker in tickers.split(","))
    
    for ticker in tickers:
        try:
            df = get_backtest_usa(kis, ticker, start_date, end_date)
            st.header(f"{ticker}")
            mdd, hpr = st.columns(2)
            with hpr:
                st.subheader("누적 수익률")
                st.markdown(f"**:red[{round(df['hpr'][-2]*100, 2)}] %**")
            st.line_chart(df, y="hpr")
            with mdd:
                st.subheader("Max DrawDown")
                st.write(f"**:red[{round(df['dd'].max(), 2)}] %**")
        except ValueError:
            st.subheader(f"{ticker} 종목의 정보를 불러올 수 없습니다.")
            