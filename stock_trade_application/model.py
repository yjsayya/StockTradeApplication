import requests
import time
import yaml, json

from stock_trade_application.message import Message

# 1. config.yaml 파일 읽기
with open('../config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
URL_BASE = _cfg['URL_BASE']


class Stock_trade:
    """
        1. get_balance() - 현금 잔고조회
        2. get_stock_balance() - 주식 잔고조회
        3. sell - 종목 매수
        4. buy - 종목 매도
        5. get_target_price() - 변동성 돌파 전략으로 매수 목표가 조회
        6. get_current_price() - 현재가 조회
    """
    
    @staticmethod
    def get_balance() -> int:
        """현금 잔고조회"""

        PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
        URL = f"{URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey": APP_KEY,
            "appSecret": APP_SECRET,
            "tr_id": "TTTC8908R",
            "custtype": "P",
        }
        params = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": "005930",
            "ORD_UNPR": "65500",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "Y"
        }
        res = requests.get(URL, headers=headers, params=params)
        cash = res.json()['output']['ord_psbl_cash']
        Message.send_message(f"주문 가능 현금 잔고: {cash}원")
        return int(cash)
    
    @staticmethod
    def get_stock_balance() -> dict:
        """주식 잔고조회"""
        
        PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
        URL = f"{URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey": APP_KEY,
            "appSecret": APP_SECRET,
            "tr_id": "TTTC8434R",
            "custtype": "P",
        }
        params = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        res = requests.get(URL, headers=headers, params=params)

        stock_list = res.json()['output1']
        evaluation = res.json()['output2']
        stock_dict = {}
        Message.send_message(f"====주식 보유잔고====")
        for stock in stock_list:
            if int(stock['hldg_qty']) > 0:
                stock_dict[stock['pdno']] = stock['hldg_qty']
                Message.send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
                time.sleep(0.1)

        Message.send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
        time.sleep(0.1)
        Message.send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
        time.sleep(0.1)
        Message.send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
        time.sleep(0.1)
        Message.send_message(f"=================")

        return stock_dict
    
    
    @staticmethod
    def get_current_price(code="005930"):
        """특정 종목의 현재가 조회"""

        PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
        URL = f"{URL_BASE}/{PATH}"
        headers = {"Content-Type": "application/json",
                   "authorization": f"Bearer {ACCESS_TOKEN}",
                   "appKey": APP_KEY,
                   "appSecret": APP_SECRET,
                   "tr_id": "FHKST01010100"}
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
        }
        
        res = requests.get(URL, headers=headers, params=params)

        return int(res.json()['output']['stck_prpr'])

    @staticmethod
    def get_target_price(code="005930"):
        """변동성 돌파 전략으로 매수 목표가 조회"""

        PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
        URL = f"{URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey": APP_KEY,
            "appSecret": APP_SECRET,
            "tr_id": "FHKST01010400"}
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_org_adj_prc": "1",
            "fid_period_div_code": "D"
        }

        res = requests.get(URL, headers=headers, params=params)
        stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
        stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
        stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
        target_price = stck_oprc + (stck_hgpr - stck_lwpr) * 0.5
        return target_price


    @staticmethod
    def buy(code="005930", qty="1") -> bool:
        """주식 시장가 매수"""
        PATH = "uapi/domestic-stock/v1/trading/order-cash"
        URL = f"{URL_BASE}/{PATH}"
        data = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": code,
            "ORD_DVSN": "01",
            "ORD_QTY": str(int(qty)),
            "ORD_UNPR": "0",
        }
        headers = {"Content-Type": "application/json",
                   "authorization": f"Bearer {ACCESS_TOKEN}",
                   "appKey": APP_KEY,
                   "appSecret": APP_SECRET,
                   "tr_id": "TTTC0802U",
                   "custtype": "P",
                   "hashkey": Token.hashkey(data)
        }
        # Request
        res = requests.post(URL, headers=headers, data=json.dumps(data))
        if res.json()['rt_cd'] == '0':
            Message.send_message(f"[매수 성공]{str(res.json())}")
            return True
        else:
            Message.send_message(f"[매수 실패]{str(res.json())}")
            return False

    @staticmethod
    def sell(code="005930", qty="1") -> bool:
        """주식 시장가 매도"""

        PATH = "uapi/domestic-stock/v1/trading/order-cash"
        URL = f"{URL_BASE}/{PATH}"
        data = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": code,
            "ORD_DVSN": "01",
            "ORD_QTY": qty,
            "ORD_UNPR": "0",
        }
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey": APP_KEY,
            "appSecret": APP_SECRET,
            "tr_id": "TTTC0801U",
            "custtype": "P",
            "hashkey": Token.hashkey(data)
        }

        res = requests.post(URL, headers=headers, data=json.dumps(data))
        if res.json()['rt_cd'] == '0':
            Message.send_message(f"[매도 성공]{str(res.json())}")
            return True
        else:
            Message.send_message(f"[매도 실패]{str(res.json())}")
            return False


class Token:

    @staticmethod
    def get_access_token() -> str:
        """토큰 발급"""
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }
        PATH = "oauth2/tokenP"
        URL = f"{URL_BASE}/{PATH}"

        # Request
        res = requests.post(URL, headers=headers, data=json.dumps(body))
        ACCESS_TOKEN = res.json()["access_token"]

        return ACCESS_TOKEN

    @staticmethod
    def hashkey(datas) -> str:
        """암호화"""
        PATH = "uapi/hashkey"
        URL = f"{URL_BASE}/{PATH}"
        headers = {
            'content-Type': 'application/json',
            'appKey': APP_KEY,
            'appSecret': APP_SECRET,
        }

        # Request
        res = requests.post(URL, headers=headers, data=json.dumps(datas))
        hashkey = res.json()["HASH"]

        return hashkey