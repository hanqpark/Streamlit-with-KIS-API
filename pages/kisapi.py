import json
import pickle
import requests
import datetime


# 해외주식 주문, 잔고
EXCHANGE_CODE = {
    "미국전체": "NASD",
    "나스닥": "NAS",
    "뉴욕": "NYSE",
    "아멕스": "AMEX",
    "홍콩": "SEHK",
    "상해": "SHAA",
    "심천": "SZAA",
    "도쿄": "TKSE",
    "하노이": "HASE",
    "호치민": "VNSE"
}

CURRENCY_CODE = {
    "미국전체": "USD",
    "나스닥": "USD",
    "뉴욕": "USD",
    "아멕스": "USD",
    "홍콩": "HKD",
    "상해": "CNY",
    "심천": "CNY",
    "도쿄": "JPY",
    "하노이": "VND",
    "호치민": "VND"
}

class KoreaInvestment:
    """ 한국투자증권 REST API """

    def __init__(self, api_key: str, api_secret: str, acc_no: str, exchange: str = "서울", mock: bool = False):
        """ 생성자
        Args:
            api_key (str): 발급받은 API key
            api_secret (str): 발급받은 API secret
            acc_no (str): 계좌번호 체계의 앞 8자리-뒤 2자리
            exchange (str): "서울", "나스닥", "뉴욕", "아멕스", "홍콩", "상해", "심천", "도쿄", "하노이", "호치민"
            mock (bool): True (mock trading), False (real trading)
        """

        self.mock = mock
        self.set_base_url(mock)
        self.api_key = api_key
        self.api_secret = api_secret

        # account number
        self.acc_no = acc_no
        self.acc_no_prefix = acc_no.split('-')[0]
        self.acc_no_postfix = acc_no.split('-')[1]

        self.exchange = exchange

        # access token
        self.access_token = None
        if self.check_access_token():
            self.load_access_token()
        else:
            self.issue_access_token()

    def set_base_url(self, mock: bool = True):
        """ 테스트(모의투자) 서버 사용 설정
        Args:
            mock(bool, optional): True: 테스트서버, False: 실서버 Defaults to True.
        """

        if mock:
            self.base_url = "https://openapivts.koreainvestment.com:29443"
        else:
            self.base_url = "https://openapi.koreainvestment.com:9443"

    def issue_access_token(self):
        """ OAuth인증/접근토큰발급 """

        path = "oauth2/tokenP"
        url = f"{self.base_url}/{path}"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.api_secret
        }

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp_data = resp.json()
        self.access_token = f'Bearer {resp_data["access_token"]}'

        # add extra information for the token verification
        now = datetime.datetime.now()
        resp_data['timestamp'] = int(now.timestamp()) + resp_data["expires_in"]
        resp_data['api_key'] = self.api_key
        resp_data['api_secret'] = self.api_secret

        # dump access token
        with open("token.dat", "wb") as f:
            pickle.dump(resp_data, f)

    def check_access_token(self):
        """ check access token
        Returns:
            Bool: True: token is valid, False: token is not valid
        """
        try:
            f = open("token.dat", "rb")
            data = pickle.load(f)
            f.close()

            expire_epoch = data['timestamp']
            now_epoch = int(datetime.datetime.now().timestamp())
            status = False

            if ((now_epoch - expire_epoch > 0) or
                (data['api_key'] != self.api_key) or
                    (data['api_secret'] != self.api_secret)):
                status = False
            else:
                status = True
            return status
        except IOError:
            return False

    def load_access_token(self):
        """ load access token """
        with open("token.dat", "rb") as f:
            data = pickle.load(f)
            self.access_token = f'Bearer {data["access_token"]}'

    def fetch_price(self, symbol: str):
        """ 
        국내주식시세/주식현재가 시세 
        해외주식현재가/해외주식 현재체결가

        Args:
            symbol (str): 종목코드
        Returns:
            dict: _description_
        """

        if self.exchange == "서울":
            return self.fetch_domestic_price("J", symbol)
        else:
            return self.fetch_oversea_price(symbol)

    def fetch_domestic_price(self, market_code: str, symbol: str):
        """ 주식현재가시세
        Args:
            market_code (str): 시장 분류코드
            symbol (str): 종목코드
        Returns:
            dict: API 개발 가이드 참조
        """
        path = "uapi/domestic-stock/v1/quotations/inquire-price"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "FHKST01010100"
        }
        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": symbol
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

    def fetch_oversea_price(self, symbol: str):
        """ 해외주식현재가/해외주식 현재체결가
        Args:
            symbol (str): 종목코드
        Returns:
            dict: API 개발 가이드 참조
        """
        path = "uapi/overseas-price/v1/quotations/price"
        url = f"{self.base_url}/{path}"

        # request header
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "HHDFS00000300"
        }

        # query parameter
        exchange_code = EXCHANGE_CODE[self.exchange]
        params = {
            "AUTH": "",
            "EXCD": exchange_code,
            "SYMB": symbol
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

    def fetch_balance(self):
        """ 잔고 조회
        Returns:
            dict: response data
        """
        if self.exchange == '서울':
            output = {}

            data = self.fetch_balance_domestic()
            output['output1'] = data['output1']
            output['output2'] = data['output2']

            while data['tr_cont'] == 'M':
                fk100 = data['ctx_area_fk100']
                nk100 = data['ctx_area_nk100']

                data = self.fetch_balance_domestic(fk100, nk100)
                output['output1'].extend(data['output1'])
                output['output2'].extend(data['output2'])

            return output
        else:
            # 해외주식 잔고
            output = {}

            data = self.fetch_balance_oversea()
            output['output1'] = data['output1']
            output['output2'] = data['output2']

            while data['tr_cont'] == 'M':
                fk200 = data['ctx_area_fk200']
                nk200 = data['ctx_area_nk200']

                data = self.fetch_balance_oversea(fk200, nk200)
                output['output1'].extend(data['output1'])
                output['output2'].extend(data['output2'])

            return output

    def fetch_balance_domestic(self, ctx_area_fk100: str = "", ctx_area_nk100: str = ""):
        """ 국내주식주문/주식잔고조회
        Args:
            ctx_area_fk100 (str): 연속조회검색조건100
            ctx_areak_nk100 (str): 연속조회키100
        Returns:
            dict: _description_
        """
        path = "uapi/domestic-stock/v1/trading/inquire-balance"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "VTTC8434R" if self.mock else "TTTC8434R"
        }
        params = {
            'CANO': self.acc_no_prefix,
            'ACNT_PRDT_CD': self.acc_no_postfix,
            'AFHR_FLPR_YN': 'N',
            'OFL_YN': 'N',
            'INQR_DVSN': '01',
            'UNPR_DVSN': '01',
            'FUND_STTL_ICLD_YN': 'N',
            'FNCG_AMT_AUTO_RDPT_YN': 'N',
            'PRCS_DVSN': '01',
            'CTX_AREA_FK100': ctx_area_fk100,
            'CTX_AREA_NK100': ctx_area_nk100
        }

        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        data['tr_cont'] = res.headers['tr_cont']
        return data

    def fetch_present_balance(self, foreign_currency: bool = True):
        """ 해외주식주문/해외주식 체결기준현재잔고
        Args:
            foreign_currency (bool): True: 외화, False: 원화
        Returns:
            dict: _description_
        """
        path = "/uapi/overseas-stock/v1/trading/inquire-present-balance"
        url = f"{self.base_url}/{path}"

        # request header
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "VTRP6504R" if self.mock else "CTRP6504R"
        }

        # query parameter
        nation_code = "000"
        if self.exchange in ["나스닥", "뉴욕", "아멕스"]:
            nation_code = "840"
        elif self.exchange == "홍콩":
            nation_code = "344"
        elif self.exchange in ["상해", "심천"]:
            nation_code = "156"
        elif self.exchange == "도쿄":
            nation_code = "392"
        elif self.exchange in ["하노이", "호치민"]:
            nation_code = "704"
        else:
            nation_code = "000"

        market_code = "00"
        if nation_code == "000":
            market_code = "00"
        elif nation_code == "840":
            if self.exchange == "나스닥":
                market_code = "01"
            elif self.exchange == "뉴욕":
                market_code = "02"
            elif self.exchange == "아멕스":
                market_code = "05"
            else:
                market_code = "00"
        elif nation_code == "156":
            market_code = "00"
        elif nation_code == "392":
            market_code = "01"
        elif nation_code == "704":
            if self.exchange == "하노이":
                market_code = "01"
            else:
                market_code = "02"
        else:
            market_code = "01"

        params = {
            'CANO': self.acc_no_prefix,
            'ACNT_PRDT_CD': self.acc_no_postfix,
            "WCRC_FRCR_DVSN_CD": "02" if foreign_currency else "01",
            "NATN_CD": nation_code,
            "TR_MKET_CD": market_code,
            "INQR_DVSN_CD": "00"
        }
        res = requests.get(url, headers=headers, params=params)
        return res.json()

    def fetch_balance_oversea(self, ctx_area_fk200: str = "", ctx_area_nk200: str = ""):
        """ 해외주식주문/해외주식 잔고
        Args:
            ctx_area_fk200 (str): 연속조회검색조건200
            ctx_area_nk200 (str): 연속조회키200
        Returns:
            dict: _description_
        """
        path = "/uapi/overseas-stock/v1/trading/inquire-balance"
        url = f"{self.base_url}/{path}"

        # 주야간원장 구분 호출
        resp = self.fetch_oversea_day_night()
        psbl = resp['output']['PSBL_YN']

        if self.mock:
            tr_id = "VTTS3012R" if psbl == 'N' else 'VTTT3012R'
        else:
            tr_id = "TTTS3012R" if psbl == 'N' else 'JTTT3012R'

        # request header
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": tr_id
        }

        # query parameter
        exchange_cd = EXCHANGE_CODE[self.exchange]
        currency_cd = CURRENCY_CODE[self.exchange]

        params = {
            'CANO': self.acc_no_prefix,
            'ACNT_PRDT_CD': self.acc_no_postfix,
            'OVRS_EXCG_CD': exchange_cd,
            'TR_CRCY_CD': currency_cd,
            'CTX_AREA_FK200': ctx_area_fk200,
            'CTX_AREA_NK200': ctx_area_nk200
        }

        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        data['tr_cont'] = res.headers['tr_cont']
        return data
    
    def fetch_oversea_day_night(self):
        """ 해외주식주문/해외주식 주야간원장구분조회 """
        path = "/uapi/overseas-stock/v1/trading/dayornight"
        url = f"{self.base_url}/{path}"

        # request/header
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "JTTT3010R"
        }

        res = requests.get(url, headers=headers)
        return res.json()

    def fetch_ohlcv(self, symbol: str, timeframe: str = 'D', start_day: str = "", end_day: str = "", adj_price: bool = True):
        """ fetch OHLCV (day, week, month)
        Args:
            symbol (str): 종목코드
            timeframe (str): "D" (일), "W" (주), "M" (월)
            start_day (str): 조회시작일자
            end_day (str): 조회종료일자
            adj_price (bool, optional): True: 수정주가 반영, False: 수정주가 미반영. Defaults to True.
        Returns:
            dict: _description_
        """
        if self.exchange == '서울':
            resp = self.fetch_ohlcv_domestic(
                symbol, timeframe, start_day, end_day, adj_price)
        else:
            resp = self.fetch_ohlcv_overesea(
                symbol, timeframe, end_day, adj_price)
        return resp

    def fetch_ohlcv_domestic(self, symbol: str, timeframe: str = 'D', start_day: str = "", end_day: str = "", adj_price: bool = True):
        """ 국내주식시세/국내주식 기간별 시세(일/주/월/년)
        Args:
            symbol (str): symbol
            timeframe (str, optional): "D": 일, "W": 주, "M": 월, 'Y': 년
            start_day (str, optional): 조회시작일자(YYYYMMDD)
            end_day (str, optional): 조회종료일자(YYYYMMDD)
            adjusted (bool, optional): False: 수정주가 미반영, True: 수정주가 반영
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        url = f"{self.base_url}/{path}"

        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "FHKST03010100"
        }

        if end_day == "":
            now = datetime.datetime.now()
            end_day = now.strftime("%Y%m%d")

        if start_day == "":
            start_day = "19800104"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_day,
            "FID_INPUT_DATE_2": end_day,
            "FID_PERIOD_DIV_CODE": timeframe,
            "FID_ORG_ADJ_PRC": 0 if adj_price else 1
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

    def fetch_ohlcv_overesea(self, symbol: str, timeframe: str = 'D', end_day: str = "", adj_price: bool = True):
        """해외주식현재가/해외주식 기간별시세

        Args:
            symbol (str): symbol
            timeframe (str, optional): "D": 일, "W": 주, "M": 월
            end_day (str, optional): 조회종료일자 (YYYYMMDD)
            adjusted (bool, optional): False: 수정주가 미반영, True: 수정주가 반영
        """
        path = "/uapi/overseas-price/v1/quotations/dailyprice"
        url = f"{self.base_url}/{path}"

        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "HHDFS76240000"
        }

        timeframe_lookup = {
            'D': "0",
            'W': "1",
            'M': "2"
        }

        if end_day == "":
            now = datetime.datetime.now()
            end_day = now.strftime("%Y%m%d")

        # exchange_code = EXCHANGE_CODE[self.exchange]
        exchange_code = "NAS"

        params = {
            "AUTH": "",
            "EXCD": exchange_code,
            "SYMB": symbol,
            "GUBN": timeframe_lookup.get(timeframe, "0"),
            "BYMD": end_day,
            "MODP": 1 if adj_price else 0
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()
