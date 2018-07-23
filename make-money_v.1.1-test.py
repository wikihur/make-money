import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import pandas as pd
import sqlite3
from datetime import datetime
import numpy
import csv
import re

class ParameterTypeError(Exception):
    """ 파라미터 타입이 일치하지 않을 경우 발생하는 예외 """

    def __init__(self, msg="파라미터 타입이 일치하지 않습니다."):
        self.msg = msg

    def __str__(self):
        return self.msg

class KiwoomConnectError(Exception):
    """ 키움서버에 로그인 상태가 아닐 경우 발생하는 예외 """

    def __init__(self, msg="로그인 여부를 확인하십시오"):
        self.msg = msg

    def __str__(self):
        return self.msg

class KiwoomProcessingError(Exception):
    """ 키움에서 처리실패에 관련된 리턴코드를 받았을 경우 발생하는 예외 """

    def __init__(self, msg="처리 실패"):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg

class ReturnCode(object):
    """ 키움 OpenApi+ 함수들이 반환하는 값 """

    OP_ERR_NONE = 0 # 정상처리
    OP_ERR_FAIL = -10   # 실패
    OP_ERR_LOGIN = -100 # 사용자정보교환실패
    OP_ERR_CONNECT = -101   # 서버접속실패
    OP_ERR_VERSION = -102   # 버전처리실패
    OP_ERR_FIREWALL = -103  # 개인방화벽실패
    OP_ERR_MEMORY = -104    # 메모리보호실패
    OP_ERR_INPUT = -105 # 함수입력값오류
    OP_ERR_SOCKET_CLOSED = -106 # 통신연결종료
    OP_ERR_SISE_OVERFLOW = -200 # 시세조회과부하
    OP_ERR_RQ_STRUCT_FAIL = -201    # 전문작성초기화실패
    OP_ERR_RQ_STRING_FAIL = -202    # 전문작성입력값오류
    OP_ERR_NO_DATA = -203   # 데이터없음
    OP_ERR_OVER_MAX_DATA = -204 # 조회가능한종목수초과
    OP_ERR_DATA_RCV_FAIL = -205 # 데이터수신실패
    OP_ERR_OVER_MAX_FID = -206  # 조회가능한FID수초과
    OP_ERR_REAL_CANCEL = -207   # 실시간해제오류
    OP_ERR_ORD_WRONG_INPUT = -300   # 입력값오류
    OP_ERR_ORD_WRONG_ACCTNO = -301  # 계좌비밀번호없음
    OP_ERR_OTHER_ACC_USE = -302 # 타인계좌사용오류
    OP_ERR_MIS_2BILL_EXC = -303 # 주문가격이20억원을초과
    OP_ERR_MIS_5BILL_EXC = -304 # 주문가격이50억원을초과
    OP_ERR_MIS_1PER_EXC = -305  # 주문수량이총발행주수의1%초과오류
    OP_ERR_MIS_3PER_EXC = -306  # 주문수량이총발행주수의3%초과오류
    OP_ERR_SEND_FAIL = -307 # 주문전송실패
    OP_ERR_ORD_OVERFLOW = -308  # 주문전송과부하
    OP_ERR_MIS_300CNT_EXC = -309    # 주문수량300계약초과
    OP_ERR_MIS_500CNT_EXC = -310    # 주문수량500계약초과
    OP_ERR_ORD_WRONG_ACCTINFO = -340    # 계좌정보없음
    OP_ERR_ORD_SYMCODE_EMPTY = -500 # 종목코드없음

    CAUSE = {
        0: '정상처리',
        -10: '실패',
        -100: '사용자정보교환실패',
        -102: '버전처리실패',
        -103: '개인방화벽실패',
        -104: '메모리보호실패',
        -105: '함수입력값오류',
        -106: '통신연결종료',
        -200: '시세조회과부하',
        -201: '전문작성초기화실패',
        -202: '전문작성입력값오류',
        -203: '데이터없음',
        -204: '조회가능한종목수초과',
        -205: '데이터수신실패',
        -206: '조회가능한FID수초과',
        -207: '실시간해제오류',
        -300: '입력값오류',
        -301: '계좌비밀번호없음',
        -302: '타인계좌사용오류',
        -303: '주문가격이20억원을초과',
        -304: '주문가격이50억원을초과',
        -305: '주문수량이총발행주수의1%초과오류',
        -306: '주문수량이총발행주수의3%초과오류',
        -307: '주문전송실패',
        -308: '주문전송과부하',
        -309: '주문수량300계약초과',
        -310: '주문수량500계약초과',
        -340: '계좌정보없음',
        -500: '종목코드없음'
    }

class RealType(object):

    REALTYPE = {
        '주식시세': {
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '거일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            311: '시가총액(억)'
        },

        '주식체결': {
            20: '체결시간(HHMMSS)',
            10: '체결가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            15: '체결량',
            13: '누적체결량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비(계약,주)',
            29: '거래대금증감',
            30: '전일거래량대비(비율)',
            31: '거래회전율',
            32: '거래비용',
            228: '체결강도',
            311: '시가총액(억)',
            290: '장구분',
            691: 'KO접근도'
        },

        '주식호가잔량': {
            21: '호가시간',
            41: '매도호가1',
            61: '매도호가수량1',
            81: '매도호가직전대비1',
            51: '매수호가1',
            71: '매수호가수량1',
            91: '매수호가직전대비1',
            42: '매도호가2',
            62: '매도호가수량2',
            82: '매도호가직전대비2',
            52: '매수호가2',
            72: '매수호가수량2',
            92: '매수호가직전대비2',
            43: '매도호가3',
            63: '매도호가수량3',
            83: '매도호가직전대비3',
            53: '매수호가3',
            73: '매수호가수량3',
            93: '매수호가직전대비3',
            44: '매도호가4',
            64: '매도호가수량4',
            84: '매도호가직전대비4',
            54: '매수호가4',
            74: '매수호가수량4',
            94: '매수호가직전대비4',
            45: '매도호가5',
            65: '매도호가수량5',
            85: '매도호가직전대비5',
            55: '매수호가5',
            75: '매수호가수량5',
            95: '매수호가직전대비5',
            46: '매도호가6',
            66: '매도호가수량6',
            86: '매도호가직전대비6',
            56: '매수호가6',
            76: '매수호가수량6',
            96: '매수호가직전대비6',
            47: '매도호가7',
            67: '매도호가수량7',
            87: '매도호가직전대비7',
            57: '매수호가7',
            77: '매수호가수량7',
            97: '매수호가직전대비7',
            48: '매도호가8',
            68: '매도호가수량8',
            88: '매도호가직전대비8',
            58: '매수호가8',
            78: '매수호가수량8',
            98: '매수호가직전대비8',
            49: '매도호가9',
            69: '매도호가수량9',
            89: '매도호가직전대비9',
            59: '매수호가9',
            79: '매수호가수량9',
            99: '매수호가직전대비9',
            50: '매도호가10',
            70: '매도호가수량10',
            90: '매도호가직전대비10',
            60: '매수호가10',
            80: '매수호가수량10',
            100: '매수호가직전대비10',
            121: '매도호가총잔량',
            122: '매도호가총잔량직전대비',
            125: '매수호가총잔량',
            126: '매수호가총잔량직전대비',
            23: '예상체결가',
            24: '예상체결수량',
            128: '순매수잔량(총매수잔량-총매도잔량)',
            129: '매수비율',
            138: '순매도잔량(총매도잔량-총매수잔량)',
            139: '매도비율',
            200: '예상체결가전일종가대비',
            201: '예상체결가전일종가대비등락율',
            238: '예상체결가전일종가대비기호',
            291: '예상체결가',
            292: '예상체결량',
            293: '예상체결가전일대비기호',
            294: '예상체결가전일대비',
            295: '예상체결가전일대비등락율',
            13: '누적거래량',
            299: '전일거래량대비예상체결률',
            215: '장운영구분'
        },

        '장시작시간': {
            215: '장운영구분(0:장시작전, 2:장종료전, 3:장시작, 4,8:장종료, 9:장마감)',
            20: '시간(HHMMSS)',
            214: '장시작예상잔여시간'
        },

        '업종지수': {
            20: '체결시간',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            15: '거래량',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비(계약,주)'
        },

        '업종등락': {
            20: '체결시간',
            252: '상승종목수',
            251: '상한종목수',
            253: '보합종목수',
            255: '하락종목수',
            254: '하한종목수',
            13: '누적거래량',
            14: '누적거래대금',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            256: '거래형성종목수',
            257: '거래형성비율',
            25: '전일대비기호'
        },

        '주문체결': {
            9201: '계좌번호',
            9203: '주문번호',
            9205: '관리자사번',
            9001: '종목코드',
            912: '주문업무분류(jj:주식주문)',
            913: '주문상태(10:원주문, 11:정정주문, 12:취소주문, 20:주문확인, 21:정정확인, 22:취소확인, 90,92:주문거부)',
            302: '종목명',
            900: '주문수량',
            901: '주문가격',
            902: '미체결수량',
            903: '체결누계금액',
            904: '원주문번호',
            905: '주문구분(+:현금매수, -:현금매도)',
            906: '매매구분(보통, 시장가등)',
            907: '매도수구분(1:매도, 2:매수)',
            908: '체결시간(HHMMSS)',
            909: '체결번호',
            910: '체결가',
            911: '체결량',
            10: '체결가',
            27: '최우선매도호가',
            28: '최우선매수호가',
            914: '단위체결가',
            915: '단위체결량',
            938: '당일매매수수료',
            939: '당일매매세금'
        },

        '잔고': {
            9201: '계좌번호',
            9001: '종목코드',
            302: '종목명',
            10: '현재가',
            930: '보유수량',
            931: '매입단가',
            932: '총매입가',
            933: '주문가능수량',
            945: '당일순매수량',
            946: '매도매수구분',
            950: '당일총매도손익',
            951: '예수금',
            27: '최우선매도호가',
            28: '최우선매수호가',
            307: '기준가',
            8019: '손익율'
        },

        '주식시간외호가': {
            21: '호가시간(HHMMSS)',
            131: '시간외매도호가총잔량',
            132: '시간외매도호가총잔량직전대비',
            135: '시간외매수호가총잔량',
            136: '시간외매수호가총잔량직전대비'
        }
    }

class FidList(object):
    """ receiveChejanData() 이벤트 메서드로 전달되는 FID 목록 """

    CHEJAN = {
        9201: '계좌번호',
        9203: '주문번호',
        9205: '관리자사번',
        9001: '종목코드',
        912: '주문업무분류',
        913: '주문상태',
        302: '종목명',
        900: '주문수량',
        901: '주문가격',
        902: '미체결수량',
        903: '체결누계금액',
        904: '원주문번호',
        905: '주문구분',
        906: '매매구분',
        907: '매도수구분',
        908: '주문/체결시간',
        909: '체결번호',
        910: '체결가',
        911: '체결량',
        10: '현재가',
        27: '(최우선)매도호가',
        28: '(최우선)매수호가',
        914: '단위체결가',
        915: '단위체결량',
        938: '당일매매수수료',
        939: '당일매매세금',
        919: '거부사유',
        920: '화면번호',
        921: '921',
        922: '922',
        923: '923',
        949: '949',
        10010: '10010',
        917: '신용구분',
        916: '대출일',
        930: '보유수량',
        931: '매입단가',
        932: '총매입가',
        933: '주문가능수량',
        945: '당일순매수수량',
        946: '매도/매수구분',
        950: '당일총매도손일',
        951: '예수금',
        307: '기준가',
        8019: '손익율',
        957: '신용금액',
        958: '신용이자',
        959: '담보대출수량',
        924: '924',
        918: '만기일',
        990: '당일실현손익(유가)',
        991: '당일실현손익률(유가)',
        992: '당일실현손익(신용)',
        993: '당일실현손익률(신용)',
        397: '파생상품거래단위',
        305: '상한가',
        306: '하한가'
    }

class StockWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 메시지
        self.msg = ""
        self.screenNo = "6002"
        self.realtimeList = []

        ### 계좌 정보
        self.file_account = "account_info.txt"
        self.account_num = ""
        self.account_pass = ""

        # 비동기 방식으로 동작되는 이벤트를 동기화(순서대로 동작) 시킬 때
        self.loginLoop = None
        self.requestLoop = None
        self.orderLoop = None
        self.conditionLoop = None

        # 예수금
        self.opw00001Data = 0

        # 보유종목 정보
        self.opw00018Data = {'accountEvaluation': [], 'stocks': []}

        # 주문채결 정보
        self.opw00007Data = {'orderList': []}

        # 주문유형 (1: 신규매수, 2: 신규매도, 3: 매수취소, 4: 매도취소, 5: 매수정정, 6: 매도정정)
        self.order_type = 1

        # 호가 거래구분(00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 그외에는 api 문서참조)
        self.hoga_type = "00"

        # Setting Windows
        win_width = 800
        win_height = 750
        win_x = 100
        win_y = 100

        base_x = 10
        base_y = 10

        self.setWindowTitle("Make Money Ver.1.0")
        self.setGeometry(win_x, win_y, win_width, win_height)

        label = QLabel('Log print', self)
        label.move(base_x, base_y)

        self.log_edit = QTextEdit(self)
        self.log_edit.setGeometry(base_x, win_height / 16, win_width/3 -30 , win_height/3)
        self.log_edit.setEnabled(True)


        btn_login = QPushButton("로그인", self)
        btn_login.move(win_width - 120, base_y)
        btn_login.clicked.connect(self.btn_login_clicked)

        label = QLabel('종목코드: ', self)
        label.move(win_width / 3, base_y)

        self.code_edit = QLineEdit(self)
        self.code_edit.move(win_width / 3, win_height / 16)
        self.code_edit.setText("000660")

        btn_real_start = QPushButton("실시간 받기", self)
        btn_real_start.move(win_width / 3, win_height / 16 + 40)
        btn_real_start.clicked.connect(self.btn_real_start_clicked)

        btn_real_stop = QPushButton("실시간 중지", self)
        btn_real_stop.move(win_width / 3, win_height / 16 + 80)
        btn_real_stop.clicked.connect(self.btn_real_stop_clicked)

        btn_real_start_total = QPushButton("Total 실시간 받기", self)
        btn_real_start_total.move(win_width / 3, win_height / 16 + 120)
        btn_real_start_total.clicked.connect(self.btn_total_real_start_clicked)

        btn_real_stop_total = QPushButton("Total 실시간 중지", self)
        btn_real_stop_total.move(win_width / 3, win_height / 16 + 160)
        btn_real_stop_total.clicked.connect(self.btn_total_real_stop_clicked)


        reged_code = QLabel('등록된코드: ', self)
        reged_code.move(win_width / 3 + 120 , base_y)

        self.listWidget = QListWidget(self)
        self.listWidget.setGeometry(win_width / 3 + 120, win_height / 16, 120, 180)
        self.listWidget.itemClicked.connect(self.item_click)

        order_price = QLabel('주문가격: ', self)
        order_price.move(win_width / 2 + 140, win_height / 16 + 40)

        self.order_price_edit = QLineEdit(self)
        self.order_price_edit.setGeometry(win_width / 2 + 200, win_height / 16 + 40, 60,30)
        self.order_price_edit.setText("")

        order_amount = QLabel('주문수량: ', self)
        order_amount.move(win_width / 2 + 140, win_height / 16 + 80)

        self.amount_edit = QLineEdit(self)
        self.amount_edit.setGeometry(win_width / 2 + 200, win_height / 16 + 80, 60,30)
        self.amount_edit.setText("")

        profit_label = QLabel('설정수익률: ', self)
        profit_label.move(win_width / 2 + 130, win_height / 16 + 120)

        self.profit_edit = QLineEdit(self)
        self.profit_edit.setGeometry(win_width / 2 + 200, win_height / 16 + 120, 60,30)
        self.profit_edit.setText("1")

        loss_label = QLabel('설정손실률: ', self)
        loss_label.move(win_width / 2 + 130, win_height / 16 + 160)

        self.loss_edit = QLineEdit(self)
        self.loss_edit.setGeometry(win_width / 2 + 200, win_height / 16 + 160, 60,30)
        self.loss_edit.setText("3")


        btn_test_order_buy = QPushButton("매수 테스트", self)
        btn_test_order_buy.move(win_width - 120, win_height / 8)
        btn_test_order_buy.clicked.connect(self.btn_test_order_buy_clicked)

        btn_test_order_sell_deposit = QPushButton("매도 테스트", self)
        btn_test_order_sell_deposit.move(win_width - 120, win_height / 8 + 40)
        btn_test_order_sell_deposit.clicked.connect(self.btn_test_order_sell_clicked)

        btn_test_order_market_buy = QPushButton("시장가 매수", self)
        btn_test_order_market_buy.move(win_width - 120, win_height / 8 + 80)
        btn_test_order_market_buy.clicked.connect(self.btn_test_order_market_buy_clicked)

        btn_test_order_market_sell = QPushButton("시장가 매도", self)
        btn_test_order_market_sell.move(win_width - 120, win_height / 8 + 120)
        btn_test_order_market_sell.clicked.connect(self.btn_test_order_market_sell_clicked)

        btn_simulation_test = QPushButton("시뮬레이션", self)
        btn_simulation_test.move(win_width - 120, win_height / 8 + 160)
        btn_simulation_test.clicked.connect(self.btn_simulation_test_clicked)

        btn_get_low =  QPushButton("저가근접조회", self)
        btn_get_low.move((win_width / 2) - 30, win_height / 2 - 140)
        btn_get_low.clicked.connect(self.btn_get_low_clicked)

        btn_get_high = QPushButton("고가근접조회", self)
        btn_get_high.move((win_width / 2) + 80, win_height / 2 - 140)
        btn_get_high.clicked.connect(self.btn_get_high_clicked)

        btn_query_account = QPushButton("계좌잔고 조회", self)
        btn_query_account.move(win_width / 3, win_height/2 - 100)
        btn_query_account.clicked.connect(self.btn_query_account_clicked)

        btn_query_order = QPushButton("주문체결 조회", self)
        btn_query_order.move(win_width / 2, win_height/2 - 100)
        btn_query_order.clicked.connect(self.btn_query_order_clicked)

        btn_get_deposit = QPushButton("예수금조회", self)
        btn_get_deposit.move(win_width / 2 + 130, win_height/2 - 100)
        btn_get_deposit.clicked.connect(self.btn_get_deposit_clicked)

        account_info_label = QLabel('계좌잔고: ', self)
        account_info_label.move(base_x, win_height/3 + 50)

        self.account_info_date_label = QLabel('', self)
        self.account_info_date_label.setGeometry(base_x + 60, win_height / 3 + 50, 130, 30)

        self.account_info_edit = QTextEdit(self)
        self.account_info_edit.setGeometry(base_x, win_height/3 + 80, win_width - 20, win_height / 6)

        transaction_label = QLabel('주문체결: ', self)
        transaction_label.move(base_x, win_height/2 + 100)

        self.transaction_date_label = QLabel('', self)
        self.transaction_date_label.setGeometry(base_x + 60, win_height / 2 + 100, 130, 30)

        self.transaction_info_edit = QTextEdit(self)
        self.transaction_info_edit.setGeometry(base_x, win_height/2 + 130, win_width - 20, win_height / 6)

        self.auto_trade_checkbox = QCheckBox("자동 매매", self)
        self.auto_trade_checkbox.move(win_width - 220, base_y)
        self.auto_trade_checkbox.resize(100, 30)
        self.auto_trade_checkbox.setChecked(True)
        self.auto_trade_checkbox.stateChanged.connect(self.checkBoxState)

        self.db_checkbox = QCheckBox("DB Save", self)
        self.db_checkbox.move(win_width - 220, base_y + 20)
        self.db_checkbox.resize(100, 30)
        self.db_checkbox.setChecked(False)
        self.db_checkbox.stateChanged.connect(self.checkDBState)

        self.simulation_checkbox = QCheckBox("Simulation", self)
        self.simulation_checkbox.move(win_width - 220, base_y + 40)
        self.simulation_checkbox.resize(100, 30)
        self.simulation_checkbox.setChecked(False)
        self.simulation_checkbox.stateChanged.connect(self.checkSimulState)

        self.createKiwoomInstance()
        self.setSignalSlots()

        database = "D:/kiwoom_db/market_price.db"
        self.conn = sqlite3.connect(database)
        self.log_edit.append("DB 접속 완료")

        # second data log
        logfile_name = str(datetime.now().strftime('%Y%m%d')) + "_LOG.txt"
        self.f_log = open(logfile_name, "a", encoding='utf-8')

        # 최저가 저장을 위한
        self.lowest_price = {}

        # 자동매매 Flag (코드별)_Rule1
        self.code_auto_flag = {}

        # 자동매매 Flag (코드별)_Rule2
        self.code_auto_flag_rule_bull = {}

        # 자동매매 Flag
        self.auto_trade_flag = True

        # 체결강도 차이를 위해
        self.before_stock_data = {}

        # 매수호가가 한단계 올라갔을 때 시점의 체결 count 체크를 위한
        self.trans_cnt = {}

        # 매수세 체크를 위해 Flag 가 시작된 시간 저장을 위한
        self.check_trans_time = {}

        self.check_trans_time_rule_bull = {}

        # 체결 count 가 만족할 때 매수/매도 세를 저장하기 위한
        # trans_data[stock_code][0] = 매수체결량
        # trans_data[stock_code][1] = 매도체결량
        self.trans_data = {}

        self.trans_data_rule_bull = {}

        # Sell order list
        self.sell_order_list = {}

        # 최우선 매수 평균을 위한
        self.top_buy_price = {}

        # 체결 강도 표준편차를 위한
        self.stdev_strong = {}

        # kospi list
        self.kospi_code_list = []

        # kosdaq list
        self.kosdaq_code_list = []

        # 시뮬레이션 flag
        self.simulation_flag = False

        # 시뮬레이션 시 기존 date
        self.before_simul_date = ""

        # 시뮬레이션 시 사용할 file
        simfile_name = str(datetime.now().strftime('%Y%m%d')) + "_SIM.txt"
        self.f_sim = open(simfile_name, "w")
        self.csv_row_cnt = 0

        # DB를 저장할지에 대한 Flag
        self.db_flag = False

        # KOSPI 시총 100위 저장
        self.kospi_100 = []

        # KOSDAQ 시총 100위 저장
        self.kosdaq_100 = []

    def getAccountInfo(self):

        id_string = ""
        pass_string = ""

        if len(self.server) == 0 or self.server != "1":
            id_string = "ACCOUNT_NUMBER"
            pass_string = "ACCOUNT_PASS"

        else:
            id_string = "ACCOUNT_VIRT_NUMBER"
            pass_string = "ACCOUNT_VIRT_PASS"

        try:
            with open(self.file_account, "r") as f_account:
                for line in f_account.readlines():
                    split_line = line.split(":")
                    if(split_line[0] == id_string):
                        self.account_num = ''.join(split_line[1].splitlines())
                    elif(split_line[0] == pass_string):
                        self.account_pass = ''.join(split_line[1].splitlines())

        except FileNotFoundError as e:
            print(str(e))
            print("계좌 정보를 파일에 입력하세요")
            exit(-1)

    def checkBoxState(self):
        if self.auto_trade_checkbox.isChecked() == True:
            self.auto_trade_flag = True
        else:
            self.auto_trade_flag = False

    def checkSimulState(self):
        if self.simulation_checkbox.isChecked() == True:
            self.simulation_flag = True
        else:
            self.simulation_flag = False

    def checkDBState(self):
        if self.db_checkbox.isChecked() == True:
            self.db_flag = True
        else:
            self.db_flag = False

    def item_click(self, item):
        self.code_edit.setText(item.text())

    def btn_total_real_start_clicked(self):

        self.simul_list = [
            "000120","033780","009150","028260","000720",
            "010950","004170","005830","096770","000660",
            "012330","006360","053800","006400","068270",
            "023530","002790","010620","035250","161390",
            "181710","017670","251270","128940","036460",
            "051910","139480","000810","015760","271560",
            "005490","130960","010130","036570","018260",
            "047810","008930","038540","069080","178920",
            "192080","000270","004990","009540","055550",
            "039030","006040","004020","086790","003550",
            "090430","058470","090460","079440","207940",
            "007310","029780","066570","068760","215600",
            "112040","253450" ]

        for f in self.simul_list:
            self.set_real_start(f)

    def set_buy_condition_each_code(self):
        self.buy_rule = {
            "000120": [3, 1],
            "008770": [3, 1],
            "009240": [3, 1],
            "033780": [3, 1],
            "009150": [3, 2],
            "028260": [3, 2],
            "084110": [3, 2],
            "000720": [3, 3],
            "010950": [3, 3],
            "004170": [3, 4],
            "005830": [3, 4],
            "096770": [3, 4],
            "000660": [3, 5],
            "012330": [3, 5],
            "067160": [3, 5],
            "006360": [3, 6],
            "053800": [3, 6],
            "006400": [3, 8],
            "068270": [3, 8],
            "023530": [3, 9],
            "002790": [4, 1],
            "005380": [4, 1],
            "010620": [4, 1],
            "035250": [4, 1],
            "161390": [4, 1],
            "181710": [4, 1],
            "017670": [4, 2],
            "251270": [4, 2],
            "128940": [4, 3],
            "036460": [4, 4],
            "051910": [4, 4],
            "139480": [4, 4],
            "000810": [4, 5],
            "015760": [4, 5],
            "271560": [4, 5],
            "005490": [4, 6],
            "130960": [4, 6],
            "010130": [4, 8],
            "036570": [4, 8],
            "018260": [5, 1],
            "047810": [5, 1],
            "034230": [5, 1],
            "067630": [5, 1],
            "008930": [5, 2],
            "038540": [5, 2],
            "069080": [5, 2],
            "178920": [5, 2],
            "192080": [5, 2],
            "000270": [5, 4],
            "004990": [5, 4],
            "009540": [5, 5],
            "055550": [5, 5],
            "039030": [5, 6],
            "006040": [6, 1],
            "004020": [6, 2],
            "086790": [6, 2],
            "003550": [6, 3],
            "090430": [6, 3],
            "058470": [6, 3],
            "090460": [6, 3],
            "079440": [6, 6],
            "207940": [6, 7],
            "007310": [7, 1],
            "029780": [7, 1],
            "066570": [7, 1],
            "041510": [7, 1],
            "068760": [7, 2],
            "215600": [7, 3],
            "112040": [7, 4],
            "253450": [7, 7],
            "140410": [7, 9]
        }

    def btn_total_real_stop_clicked(self):

        if self.simulation_flag:
            self.realtimeList.clear()
            self.listWidget.clear()
            self.listWidget.addItems(self.realtimeList)

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        for code in self.realtimeList:
            self.setRealRemove(self.screenNo, code)

        self.realtimeList.clear()
        self.listWidget.clear()
        self.listWidget.addItems(self.realtimeList)

    def set_real_start(self, code):

        if self.simulation_flag:
            self.realtimeList.append(code)
            self.listWidget.clear()
            self.listWidget.addItems(self.realtimeList)

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        if code in self.realtimeList:
            print("해당 코드는 이미 등록되어있습니다.")
            return
        else:
            # 이미 등록되어있는 게 있을 때
            if len(self.realtimeList) > 0:
                newornot = "1"
            else:
                # 처음 등록 할 때
                newornot = "0"

            if(len(self.realtimeList) > 99):
                print("100 개 초과")
                return

            self.setRealReg(self.screenNo, code, "10;228", newornot)
            self.realtimeList.append(code)

        self.listWidget.clear()
        self.listWidget.addItems(self.realtimeList)

    # 실시간 데이터 받기 함수
    def btn_real_start_clicked(self):

        code = self.code_edit.text()
        newornot = ""

        if self.simulation_flag:
            self.realtimeList.append(code)
            self.listWidget.clear()
            self.listWidget.addItems(self.realtimeList)

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        if code in self.realtimeList:
            print("해당 코드는 이미 등록되어있습니다.")
            return
        else:
            # 이미 등록되어있는 게 있을 때
            if len(self.realtimeList) > 0:
                newornot = "1"
            else:
                #처음 등록 할 때
                newornot = "0"

            self.setRealReg(self.screenNo, code, "10;228", newornot)
            self.realtimeList.append(code)

        self.listWidget.clear()
        self.listWidget.addItems(self.realtimeList)

    # 실시간 데이터 받기 중지 함수
    def btn_real_stop_clicked(self):
        code = self.code_edit.text()

        if self.simulation_flag:
            self.realtimeList.remove(code)
            self.listWidget.clear()
            self.listWidget.addItems(self.realtimeList)

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        if code in self.realtimeList:
            self.setRealRemove(self.screenNo, code)
            self.realtimeList.remove(code)
        else:
            print("등록된 Code 가 아닙니다.")

        self.listWidget.clear()
        self.listWidget.addItems(self.realtimeList)

    # 로그인 함수
    def btn_login_clicked(self):
        self.commConnect()
        self.getCodeList()
        self.getAccountInfo()
        self.set_buy_condition_each_code()
        #self.btn_query_account_clicked()

    # 종목 코드 받기 함수
    def getCodeList(self):
        self.log_edit.append("종목 코드 받기")
        ret = self.kiwoom_api.dynamicCall("GetCodeListByMarket(QString)", ["0"])
        self.kospi_code_list = ret.split(';')

        ret = self.kiwoom_api.dynamicCall("GetCodeListByMarket(QString)", ["10"])
        self.kosdaq_code_list = ret.split(';')

    # 예수금 조회 함수
    def btn_get_deposit_clicked(self):
        self.log_edit.append("예수금조회")

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        self.setInputValue("계좌번호", self.account_num)
        self.setInputValue("비밀번호", self.account_pass)
        self.setInputValue("비밀번호입력매체구분", "00")
        self.setInputValue("조회구분", "2")

        self.commRqData("예수금상세현황요청", "opw00001", 0, "0101")

    def btn_get_low_clicked(self):
        self.log_edit.append("저가근접조회")

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        # 고저구분 = 1:고가, 2:저가
        # 근접율 = 05:0.5 10:1.0, 15:1.5, 20:2.0. 25:2.5, 30:3.0
        # 시장구분 = 000:전체, 001:코스피, 101:코스닥
        # 거래량구분 = 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
        # 종목조건 = 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기
        # 신용조건 = 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 9:신용융자전체

        self.setInputValue("고저구분", "2")
        self.setInputValue("근접율", "10")
        self.setInputValue("시장구분", "000")
        self.setInputValue("거래량구분", "00100")
        self.setInputValue("종목조건", "1")
        self.setInputValue("신용조건", "1")

        self.commRqData("저가근접조회", "OPT10018", 0, "0101")

    def btn_get_high_clicked(self):
        self.log_edit.append("고가근접조회")

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        # 고저구분 = 1:고가, 2:저가
        # 근접율 = 05:0.5 10:1.0, 15:1.5, 20:2.0. 25:2.5, 30:3.0
        # 시장구분 = 000:전체, 001:코스피, 101:코스닥
        # 거래량구분 = 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
        # 종목조건 = 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기
        # 신용조건 = 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 9:신용융자전체

        self.setInputValue("고저구분", "1")
        self.setInputValue("근접율", "10")
        self.setInputValue("시장구분", "000")
        self.setInputValue("거래량구분", "00100")
        self.setInputValue("종목조건", "1")
        self.setInputValue("신용조건", "1")

        self.commRqData("고가근접조회", "OPT10018", 0, "0101")

    # 매수 테스트 함수
    def btn_test_order_buy_clicked(self):
        self.order_type = 1
        self.test_order()

    # 매도 테스트 함수
    def btn_test_order_sell_clicked(self):
        self.order_type = 2
        self.test_order()

    # 시장가 매수 테스트 함수
    def btn_test_order_market_buy_clicked(self):
        self.order_type = 1
        self.hoga_type = "03"
        self.test_order()

    # 시장가 매도 테스트 함수
    def btn_test_order_market_sell_clicked(self):
        self.order_type = 2
        self.hoga_type = "03"
        self.test_order()

    def btn_simulation_test_clicked(self):
        print("Simulation Start")

        if(self.simulation_flag):

            for code in self.realtimeList:
                self.csv_row_cnt = 0
                filename = "D:/data/" + code + ".csv"
                # filename = code + ".csv"
                f = open(filename, "r", encoding='UTF8')
                rdr = csv.reader(f)

                # code = filename[30:36]

                for line in rdr:
                    #        print(line)
                    line.append(code)
                    self.checkCondition(line)
                    self.csv_row_cnt += 1

                # Today 정보를 파일에 쓰기 위해
                line[0] = "END"
                self.checkCondition(line)

                f.close()

            self.f_sim.close()
        else:
            print("Need to set simulation checkbox")
            self.log_edit.append("Need to set simulation checkbox")

    # 매수/매도 테스트 함수
    def test_order(self):
        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        stock_code = self.code_edit.text()
        price = self.order_price_edit.text()
        amount = self.amount_edit.text()
        order_type = self.order_type

        hoga_type = self.hoga_type

        if(stock_code == "" or price == "" or amount == ""):
            print("종목코드, 가격, 수량을 확인하세요")
            return

        type = { 1: "신규매수", 2:"신규매도", 3:"매수취소", 4:"매도취소", 5:"매수정정", 6:"매도정정"}

        self.log_edit.append("종목유형:" + type[order_type] + ", " + stock_code + "," + price + "," + amount)
        self.sendOrder("testorder", "1002", self.account_num, order_type, stock_code, int(amount), int(price), hoga_type, "")

    # 계좌 잔고 함수
    def btn_query_account_clicked(self):
        self.log_edit.append("계좌잔고 조회")

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        self.setInputValue("계좌번호", self.account_num)
        self.setInputValue("비밀번호", self.account_pass)
        self.setInputValue("비밀번호입력매체구분", "00")
        self.setInputValue("조회구분", "2")

        self.commRqData("계좌평가잔고내역요청", "opw00018", 0, "0101")

    # 주문 체결 조회 함수
    def btn_query_order_clicked(self):
        self.log_edit.append("주문체결 조회")

        today = datetime.now().strftime('%Y%m%d')

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        self.setInputValue("주문일자", today)

        self.setInputValue("계좌번호", self.account_num)
        self.setInputValue("비밀번호", "")
        self.setInputValue("비밀번호입력매체구분", "00")

        # 조회구분 = 1:주문순, 2:역순, 4:체결내역만
        self.setInputValue("조회구분", "1")

        # 주식채권구분 = 0:전체, 1:주식, 2:채권권
        self.setInputValue("주식채권구분", "1")

        # 매도수구분 = 0:전체, 1:매도, 2:매수
        self.setInputValue("매도수구분", "0")

        #code = self.code_edit.text()
        #self.setInputValue("종목코드", code)
        self.setInputValue("시작주문번호", "")

        self.commRqData("계좌별주문체결내역상세요청", "opw00007", 0, "0101")

    # Create Kiwoom Instance
    def createKiwoomInstance(self):
        self.kiwoom_api = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        #self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def setSignalSlots(self):
        self.kiwoom_api.OnEventConnect.connect(self.eventConnect)
        self.kiwoom_api.OnReceiveTrData.connect(self.receiveTrData)
        self.kiwoom_api.OnReceiveRealData.connect(self.receiveRealData)
        self.kiwoom_api.OnReceiveChejanData.connect(self.receiveChejanData)
        self.kiwoom_api.OnReceiveMsg.connect(self.receiveMsg)

    def commConnect(self):
        self.kiwoom_api.dynamicCall("CommConnect()")
        self.loginLoop = QEventLoop()
        self.loginLoop.exec_()

        result = ""

        if self.getConnectState():
            result = " 로그인 성공 "
        else:
            result = " 로그인 실패 "

        self.log_edit.append(result)

    def getConnectState(self):
        """
        현재 접속상태를 반환합니다.

        반환되는 접속상태는 아래와 같습니다.
        0: 미연결, 1: 연결

        :return: int
        """
        state = self.kiwoom_api.dynamicCall("GetConnectState()")
        return state

    def eventConnect(self, returnCode):
        """
        통신 연결 상태 변경시 이벤트

        returnCode가 0 이면 로그인 성공
        그 외에는 ReturnCode 클래스 참조.

        :param returnCode: int
        """

        try:
            if returnCode == ReturnCode.OP_ERR_NONE:

                self.server = self.GetServerGubun()

                if len(self.server) == 0 or self.server != "1":
                    #self.msg += "실서버 연결 성공" + "\r\n\r\n"
                    print("실서버 연결 성공" + "\r\n\r\n")

                else:
                    #self.msg += "모의투자서버 연결 성공" + "\r\n\r\n"
                    print("모의투자서버 연결 성공" + "\r\n\r\n")

            else:
                #self.msg += "연결 끊김: 원인 - " + ReturnCode.CAUSE[returnCode] + "\r\n\r\n"
                print("연결 끊김: 원인 - " + ReturnCode.CAUSE[returnCode] + "\r\n\r\n")


        except Exception as error:
            print (error)

        finally:
            # commConnect() 메서드에 의해 생성된 루프를 종료시킨다.
            # 로그인 후, 통신이 끊길 경우를 대비해서 예외처리함.
            try:
                self.loginLoop.exit()
            except AttributeError:
                pass

    def getStepPrice(self, stock_code, current_price):

        step_price = 0
        if (current_price < 1000):
            step_price = 1
        elif (current_price < 5000):
            step_price = 5
        elif (current_price < 10000):
            step_price = 10
        elif (current_price < 50000):
            step_price = 50
        elif (current_price < 100000):
            step_price = 100
        elif (current_price < 500000):
            if(stock_code in self.kospi_code_list):
                step_price = 500
            else:
                step_price = 100
        elif (current_price < 1000000):
            if (stock_code in self.kospi_code_list):
                step_price = 1000
            else:
                step_price = 100
        return step_price

    def getDiffTime(self, stock_code, make_time):
        # 시간 차이 계산
        before_hour = int(self.check_trans_time[stock_code][:2])
        before_min = int(self.check_trans_time[stock_code][2:4])
        before_sec = int(self.check_trans_time[stock_code][4:])

        current_hour = int(make_time[:2])
        current_min = int(make_time[2:4])
        current_sec = int(make_time[4:])

        diff_time = ((current_hour * 3600) + (current_min * 60) + current_sec) - \
                    ((before_hour * 3600) + (before_min * 60) + before_sec)
        return diff_time

    def getDiffTime_rule_bull(self, stock_code, make_time):
        # 시간 차이 계산
        before_hour = int(self.check_trans_time_rule_bull[stock_code][:2])
        before_min = int(self.check_trans_time_rule_bull[stock_code][2:4])
        before_sec = int(self.check_trans_time_rule_bull[stock_code][4:])

        current_hour = int(make_time[:2])
        current_min = int(make_time[2:4])
        current_sec = int(make_time[4:])

        diff_time = ((current_hour * 3600) + (current_min * 60) + current_sec) - \
                    ((before_hour * 3600) + (before_min * 60) + before_sec)
        return diff_time

    def getBuyCnt(self, current_price, buy_def_price):
        buy_cnt = 1

        temp_cnt = int(buy_def_price / current_price)

        if (temp_cnt == 0):
            temp_cnt = 1

        buy_cnt = temp_cnt

        return buy_cnt

    def checkCondition(self, data_list):
        """
            새로운 룰
            - 저가가 변경 시점 부터 1분 동안 Waiting
            - 매수세, 체결강도의 표준편차, 체결강도의 차이를 비교
         """

        if (len(data_list) == 0 or len(data_list) < 23):
            print("Empty Data List")
            return

        if (data_list[0] == "index"):
            print("first row")
            return

        """
        Data Format
        ['007390', '+31000', '+900', '+2.99', '23063', '714', '+61', 
         '+31000', '+31000', '+31000', '090001', '2', '-9080814', '+31000', 
         '+30950', '-277626313250', '-0.25', '0.04', '103', '14.70', '2', '16410', '0']
       """

        # Buy
        stock_code = data_list[0]
        current_price = abs(int(data_list[1]))
        make_amount = int(data_list[6])
        make_time = data_list[10]
        low_price = abs(int(data_list[9]))
        first_sell_price = abs(int(data_list[13]))
        first_buy_price = abs(int(data_list[14]))
        make_strong = abs(float(data_list[19]))

        simul_date = ""
        if(self.simulation_flag):
            stock_code = data_list[23]
            current_price = abs(int(data_list[2]))
            make_amount = int(data_list[7])
            make_time = data_list[1]
            low_price = abs(int(data_list[12]))
            first_sell_price = abs(int(data_list[5]))
            first_buy_price = abs(int(data_list[6]))
            make_strong = abs(float(data_list[19]))
            simul_date = data_list[0]

            split_data = re.split(" ", simul_date)
            if (self.before_simul_date != split_data[0]):
                self.code_auto_flag[stock_code] = False

                if(self.lowest_price.get(stock_code)):
                    del self.lowest_price[stock_code]

                self.trans_cnt[stock_code] = 0
                self.trans_data[stock_code] = [0, 0]
                self.stdev_strong.clear()
                self.top_buy_price.clear()
                self.before_simul_date = split_data[0]

        # 체결시간 9시 전이면 return
        if (abs(int(make_time)) < 90000):
            print("[before AM.9]")
            return

        # 기본 매수량
        buy_cnt = 1

        # 매수시 주문 기준 금액 (10만원)
        buy_def_price = 100000

        # 수익률 0.8%
        #profit_rate = 1.008
        profit_rate = 1.0 + abs(float(self.profit_edit.text()) / 100)

        # 손절매 -2%
        #loss_rate = 0.97
        loss_rate = 1.0 - abs(float(self.loss_edit.text()) / 100)

        # 체결 list 건수가 아래 이상일 때
        threshold_make_cnt = 100

        # 체결강도(매수/매도)(매수세:bull_power) 의 비율이 아래 이상일 때
        threshold_make_amount = 1.5

        # 저가가 변경된 후 기다리는 시간 (초)
        threshold_make_time = 60

        # 현재 저가와 최우선 매수호가 사이의 변동값
        # 1이면 저가와 최우선 매수호가가 계속 같았던 것이고
        # 1보다 높으면 최우선 매수호가가 올라가는 중
        threshold_div_avg_low = 1

        # 체결 강도 차이가 아래 보다
        threshold_diff_strong = 1

        # 체결강도의 표준편차 기준
        threshold_stdev_strong = 1

        # 호가 단위 금액을 저장하기 위한
        step_price = self.getStepPrice(stock_code, current_price)

        # 최저가 값이 없을 때 현재 저가를 저장
        if (not self.lowest_price.get(stock_code)):
            print("Change Lowest price: because empty list DATE[%s], C[%s], P[%d]" %
                  (str(datetime.today()), stock_code, low_price))

            self.code_auto_flag[stock_code] = True
            self.lowest_price[stock_code] = low_price
            self.trans_cnt[stock_code] = 0
            self.trans_data[stock_code] = [0, 0]
            self.check_trans_time[stock_code] = make_time
            if (self.stdev_strong.get(stock_code)):
                del self.stdev_strong[stock_code]
            if (self.top_buy_price.get(stock_code)):
                del self.top_buy_price[stock_code]

        # 기존에 최저가 보다 낮은 저가가 나왔을 때 최저가 변경
        if (self.lowest_price[stock_code] > low_price):
            print("Change Lowest price : DATE[%s], C[%s],P[%d]" % (str(datetime.today()), stock_code, low_price))

            self.code_auto_flag[stock_code] = True
            self.lowest_price[stock_code] = low_price
            self.trans_cnt[stock_code] = 0
            self.trans_data[stock_code] = [0, 0]
            self.check_trans_time[stock_code] = make_time
            if (self.stdev_strong.get(stock_code)):
                del self.stdev_strong[stock_code]
            if (self.top_buy_price.get(stock_code)):
                del self.top_buy_price[stock_code]

        # 자동 매수 Check Flag 가 Enable 되어있고, 자동 매매 Flag 도 Enable 되어있을 때
        if (self.code_auto_flag.get(stock_code) and self.auto_trade_flag):

            # 체결 Count 저장
            if (self.trans_cnt.get(stock_code)):
                self.trans_cnt[stock_code] += 1
            else:
                self.trans_cnt[stock_code] = 1

            if (make_amount > 0):
                self.trans_data[stock_code][0] += make_amount
            else:
                self.trans_data[stock_code][1] += abs(make_amount)

            # 시간 차이 계산
            diff_time = self.getDiffTime(stock_code, make_time)

            # 최우선 매수 호가 저장
            if (self.top_buy_price.get(stock_code)):
                #self.top_buy_price[stock_code] += first_buy_price
                self.top_buy_price[stock_code].append(first_buy_price)
            else:
                #self.top_buy_price[stock_code] = first_buy_price
                self.top_buy_price[stock_code] = [first_buy_price]

            # 체결강도 저장
            if (self.stdev_strong.get(stock_code)):
                self.stdev_strong[stock_code].append(make_strong)
            else:
                self.stdev_strong[stock_code] = [make_strong]

            # 모니터링 시간이 threshold_make_time 을 넘겼을 때 Rule Check
            if (diff_time > threshold_make_time):

                # 매수세를 확인하기 위한
                if (self.trans_data[stock_code][1] == 0):
                    bull_power = 0
                else:
                    bull_power = (self.trans_data[stock_code][0] / self.trans_data[stock_code][1])

                strong_arr = numpy.array(self.stdev_strong.get(stock_code))

                # 체결강도 표준 편차, 1보다 작은 것으로 (편차가 작은)
                stdev_strong = numpy.std(strong_arr)

                # 체결 강도가 커지면 매수세가 높음
                diff_strong = strong_arr[-1] - strong_arr[0]

                # 최우선 매수 호가 평균 , 1보다 크다는 것은 매수호가가 올라간 게 1개라도 있다는 것
                top_buy_array = numpy.array(self.top_buy_price.get(stock_code))
                top_buy_avg = numpy.mean(top_buy_array)
                #top_buy_avg = self.top_buy_price.get(stock_code) / self.trans_cnt.get(stock_code)

                # 현재 저가와 최우선 매수호가 사이의 변동값
                # 1이면 저가와 최우선 매수호가가 계속 같았던 것이고
                # 1보다 높으면 최우선 매수호가가 올라가는 중

                div_avg_low = top_buy_avg / low_price

                print(str(datetime.today()))
                print("Checking[%s]:cnt[%d],bull_power[%s],diff_time[%d],stdev[%s],diff_strong[%f],top_buy_avg[%s],div_avg_low[%s]"
                      % (stock_code, self.trans_cnt[stock_code], str(bull_power), diff_time, str(stdev_strong), diff_strong, str(top_buy_avg), str(div_avg_low)))

                # 진짜 Rule Check
                if ((self.trans_cnt.get(stock_code) > threshold_make_cnt) and
                        (bull_power >= threshold_make_amount) and
                        (div_avg_low > threshold_div_avg_low) and
                        (diff_strong > 0) and (diff_strong < threshold_diff_strong) and
                        (stdev_strong < threshold_stdev_strong)):

                    buy_order_price = 0

                    if ((first_sell_price - first_buy_price) > step_price):
                        buy_order_price = first_buy_price + step_price
                    else:
                        buy_order_price = first_sell_price

                    buy_cnt = self.getBuyCnt(current_price, buy_def_price)

                    print("매수주문!!! :" + stock_code)
                    print("매수 주문[%s], 가격:[%d], 수량[%d], CNT[%d], BULL[%f], diff_time[%d], diff_strong[%f]"
                                         % (stock_code, buy_order_price, buy_cnt, self.trans_cnt[stock_code], bull_power, diff_time, diff_strong))

                    self.log_edit.append("매수 주문[%s], 가격:[%d], 수량[%d], CNT[%d], BULL[%f], diff_time[%d], diff_strong[%f]"
                                         % (stock_code, buy_order_price, buy_cnt, self.trans_cnt[stock_code], bull_power, diff_time, diff_strong))

                    if(not self.simulation_flag):
                        self.testAutoBuy(stock_code, 1, str(buy_order_price), str(buy_cnt))
                        self.f_log.write("매수 주문[%s], 가격:[%d], 수량[%d], CNT[%d], BULL[%f], diff_time[%d], diff_strong[%f]\n"
                                         % (stock_code, buy_order_price, buy_cnt, self.trans_cnt[stock_code], bull_power, diff_time, diff_strong))
                        self.f_log.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")

                    else:
                        # Simulation 때는 바로 사는 것으로
                        if (self.opw00018Data['stocks']):
                            retention_cnt = int(self.opw00018Data['stocks'][0][2])
                            retention_price = int(self.opw00018Data['stocks'][0][3])
                            total_cnt = retention_cnt + int(buy_cnt)
                            avg_price = int(
                                ((retention_price * retention_cnt) + (buy_order_price * int(buy_cnt))) / total_cnt)
                            list_data = ["A" + stock_code, "SIMULATION", str(total_cnt), str(avg_price)]
                            self.opw00018Data = {'accountEvaluation': [], 'stocks': []}
                            self.opw00018Data['stocks'].append(list_data)

                        else:  # empty
                            list_data = ["A" + stock_code, "SIMULATION", buy_cnt, str(buy_order_price)]
                            self.opw00018Data['stocks'].append(list_data)

                        self.f_sim.write("============================================================\n" +
                                     "[" + split_data[0] + "][BUY ]:LINE[" + str(self.csv_row_cnt) +
                                     "]:\tCODE[" + stock_code + "]:\tCNT[" +
                                     str(self.trans_cnt.get(stock_code)) + "]:\tBULL[" +
                                     str(bull_power) + "]:\tDIFF_T[" + str(diff_time) +
                                     "]:\tORDER_PRICE[" + str(buy_order_price) + "]:\t" +
                                     "TOP_BUY[" + str(div_avg_low) + "]:\t" +
                                     "DIFF_STR[" + str(diff_strong) + "]:\t" +
                                     "STDEV[" + str(stdev_strong) + "]\n" +
                                     "============================================================\n")


                else:
                    print(str(datetime.today()))
                    print("S================================================================")
                    print("CODE[%s]:CON1[%s],CON2[%s],CON3[%s],CON4[%s],CON5[%s],CON6[%s]" %
                                         ( stock_code,
                                            (self.trans_cnt.get(stock_code) > threshold_make_cnt),
                                           (bull_power >= threshold_make_amount),
                                           (div_avg_low > threshold_div_avg_low),
                                           (diff_strong > 0),
                                           (diff_strong < threshold_diff_strong),
                                           (stdev_strong < threshold_stdev_strong)
                                           ) )

                    print("Code[%s]:CON1:ARG1[%d]:ARG2[%d]" % (stock_code, self.trans_cnt.get(stock_code), threshold_make_cnt))
                    print("Code[%s]:CON2:ARG1[%f]:ARG2[%d]" % (stock_code, bull_power, threshold_make_amount))
                    print("Code[%s]:CON3:ARG1[%f]:ARG2[%d]" % (stock_code, div_avg_low, threshold_div_avg_low))
                    print("Code[%s]:CON4:ARG1[%f]:ARG2[%d]" % (stock_code, diff_strong, 0))
                    print("Code[%s]:CON5:ARG1[%f]:ARG2[%d]" % (stock_code, diff_strong, threshold_diff_strong))
                    print("Code[%s]:CON6:ARG1[%f]:ARG2[%d]" % (stock_code, stdev_strong, threshold_stdev_strong))

                    print("E================================================================")


                # 초기화
                self.code_auto_flag[stock_code] = False
                self.trans_cnt[stock_code] = 0
                self.trans_data[stock_code] = [0, 0]
                self.stdev_strong.clear()
                self.top_buy_price.clear()

        # Sell
        if (self.auto_trade_flag):
            for stock_list in self.opw00018Data['stocks']:

                # 잔고 조회 후에 stock 이 존재하면
                if (stock_list[0] == ("A" + stock_code)):
                    # 매입가 대비 1% 가 오른 현재 가격이면 매도 주문
                    bought_price = int(stock_list[3])
                    if ( ((bought_price * profit_rate) <= current_price) or
                            ((bought_price * loss_rate) >= current_price)  ):

                        self.log_edit.append("매도[%s]: 현재가[%d] - 매입가[%d] = [%d]" %
                                             (stock_code,  current_price, bought_price, int(current_price-bought_price)) )

                        #self.f_log.write("매도[%s]: 현재가[%d] - 매입가[%d] = [%d]\n" %
                        #                     (stock_code,  current_price, bought_price, int(current_price-bought_price)))

                        if ((bought_price * loss_rate) >= current_price):
                            self.f_log.write("[손절]=")
                        else:
                            self.f_log.write("[수익]=")

                        sell_order_price = 0

                        if ((first_sell_price - first_buy_price) > step_price):
                            sell_order_price = first_buy_price + step_price
                        else:
                            sell_order_price = first_buy_price

                        if (not self.simulation_flag):

                            # 기존에 매도 주문 내역이 없으면 바로 매도 주문
                            if (not self.sell_order_list.get(str("A" + stock_code))):
                                self.testAutoBuy(stock_code, 2, str(sell_order_price), stock_list[2])
                                self.sell_order_list[str("A" + stock_code)] = int(stock_list[2])
                                self.log_edit.append("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                     ", 수량: " + str(stock_list[2]))
                                self.f_log.write("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                     ", 수량: " + str(stock_list[2]) + "\n")
                                self.f_log.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")

                            # 기존에 매도 주문 내역이 있고, 매도 주문을 낼 수 있는 잔량이 있으면 매도 주문
                            elif ((int(stock_list[2]) - self.sell_order_list[str("A" + stock_code)]) > 0):
                                self.testAutoBuy(stock_code, 2, str(sell_order_price), stock_list[2])
                                self.sell_order_list[str("A" + stock_code)] = self.sell_order_list[str("A" + stock_code)] +\
                                                                              int(stock_list[2])
                                self.log_edit.append("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                     ", 수량: " + str(stock_list[2]))
                                self.f_log.write("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                 ", 수량: " + str(stock_list[2]) + "\n")
                                self.f_log.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")

                            # 매도 할 수 있는 잔고가 없을 때
                            else:
                                print("매도 할 수 있는 잔고가 없습니다.")
                                self.log_edit.append("매도 잔고 없음: " + stock_code)

                        else:
                            # simulation 때
                            print("Sell[%s]count[%s]" % (stock_code, str(stock_list[2])))
                            self.log_edit.append("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                 ", 수량: " + str(stock_list[2]))

                            self.f_sim.write("============================================================\n" +
                                         "[" + split_data[0] + "][SELL]:LINE[" + str(self.csv_row_cnt) +
                                         "]:\tCODE[" + stock_code + "]:" +
                                         "\tPRICE[" + str(sell_order_price) + "]:" +
                                         "\tAMOUNT[" + str(stock_list[2]) + "]:" +
                                         "\tPROFIT[" + str(sell_order_price - int(stock_list[3])) + "]:" +
                                         "\n" + "============================================================\n")

                            del self.opw00018Data['stocks'][:]

                # count  #stock_list[2]
                # 매입가 #stock_list[3]

    def checkCondition_rule_bull(self, data_list):
        """
            새로운 룰
            - 매수, 매도 호가의 차이 크기 가 특정 시점이 될 때
            - 매수세를 확인하여 매수, 시뮬레이션 결과를 바탕으로
         """

        if (len(data_list) == 0 or len(data_list) < 23):
            print("Empty Data List")
            return

        if (data_list[0] == "index"):
            print("first row")
            return

        """
        Data Format
        ['007390', '+31000', '+900', '+2.99', '23063', '714', '+61', 
         '+31000', '+31000', '+31000', '090001', '2', '-9080814', '+31000', 
         '+30950', '-277626313250', '-0.25', '0.04', '103', '14.70', '2', '16410', '0']
       """

        # Buy
        stock_code = data_list[0]
        current_price = abs(int(data_list[1]))
        make_amount = int(data_list[6])
        make_time = data_list[10]
        low_price = abs(int(data_list[9]))
        first_sell_price = abs(int(data_list[13]))
        first_buy_price = abs(int(data_list[14]))
        make_strong = abs(float(data_list[19]))

        simul_date = ""
        if(self.simulation_flag):
            stock_code = data_list[23]
            current_price = abs(int(data_list[2]))
            make_amount = int(data_list[7])
            make_time = data_list[1]
            low_price = abs(int(data_list[12]))
            first_sell_price = abs(int(data_list[5]))
            first_buy_price = abs(int(data_list[6]))
            make_strong = abs(float(data_list[19]))
            simul_date = data_list[0]

            split_data = re.split(" ", simul_date)
            if (self.before_simul_date != split_data[0]):
                self.code_auto_flag[stock_code] = False

                if(self.lowest_price.get(stock_code)):
                    del self.lowest_price[stock_code]

                self.trans_cnt[stock_code] = 0
                self.trans_data[stock_code] = [0, 0]
                self.stdev_strong.clear()
                self.top_buy_price.clear()
                self.before_simul_date = split_data[0]


        # 체결시간 9시 전이면 return
        if (abs(int(make_time)) < 90000):
            print("[before AM.9]")
            return

        # 기본 매수량
        buy_cnt = 1

        # 매수시 주문 기준 금액 (10만원)
        buy_def_price = 100000

        # 수익률 0.8%
        #profit_rate = 1.008
        profit_rate = 1.0 + abs(float(self.profit_edit.text()) / 100)

        # 손절매 -3%
        #loss_rate = 0.97
        loss_rate = 1.0 - abs(float(self.loss_edit.text()) / 100)

        # 체결 list 건수가 아래 이상일 때
        threshold_make_cnt = 100

        # Step Level 이 특정 Level 로 변경된 후 기다리는 시간 (초)
        threshold_make_time = 30

        # 호가 단위 금액을 저장하기 위한
        step_price = self.getStepPrice(stock_code, current_price)

        # 최우선 매도 호가 - 최우선 매수 호가 : step_level 로 비교
        diff_sell_buy = first_sell_price - first_buy_price


        # 각 코드 별 시뮬레이션으로 값을 가지고 있음.
        step_price_level = self.buy_rule[stock_code][0]

        # 체결강도(매수/매도)(매수세:bull_power) 의 비율이 아래 이상일 때
        threshold_make_amount = self.buy_rule[stock_code][1]

        # 최우선 매도 호가와 최우선 매수 호가 차이가 지정된 level 보다 같거나 높을 때 Enable Flag
        if(diff_sell_buy >= (step_price * step_price_level)):
            self.code_auto_flag_rule_bull[stock_code] = True
            self.check_trans_time_rule_bull[stock_code] = make_time
            self.trans_data_rule_bull[stock_code] = [0, 0]

        if( self.code_auto_flag_rule_bull.get(stock_code) ):

            # 매수/매도 체결량 저장
            if(make_amount > 0):
                self.trans_data_rule_bull[stock_code][0] += make_amount
            else:
                self.trans_data_rule_bull[stock_code][1] += abs(make_amount)

            # 시간 차이 계산
            diff_time = self.getDiffTime_rule_bull(stock_code, make_time)

            # 모니터링 시간이 threshold_make_time 을 넘겼을 때 Rule Check
            if (diff_time > threshold_make_time):

                # 매수세를 확인하기 위한
                if (self.trans_data_rule_bull[stock_code][1] == 0):
                    bull_power = 0
                else:
                    bull_power = (self.trans_data_rule_bull[stock_code][0] / self.trans_data_rule_bull[stock_code][1])

                # 매수세가 특정 이상일 때
                if ((bull_power >= threshold_make_amount)):
                    buy_order_price = 0

                    if ((first_sell_price - first_buy_price) > step_price):
                        buy_order_price = first_buy_price + step_price
                    else:
                        buy_order_price = first_sell_price

                    buy_cnt = self.getBuyCnt(current_price, buy_def_price)

                    print("매수주문!!! :" + stock_code)
                    print("매수 주문[%s], 가격:[%d], 수량[%d], BULL[%f], diff_time[%d], set_bull[%d]"
                          % (stock_code, buy_order_price, buy_cnt, bull_power, diff_time, threshold_make_amount))

                    self.log_edit.append("매수 주문[%s], 가격:[%d], 수량[%d], BULL[%f], diff_time[%d], set_bull[%d]"
                                         % (stock_code, buy_order_price, buy_cnt, bull_power, diff_time, threshold_make_amount))

                    if (not self.simulation_flag):
                        self.testAutoBuy(stock_code, 1, str(buy_order_price), str(buy_cnt))
                        self.f_log.write(
                            "매수 주문[%s], 가격:[%d], 수량[%d], BULL[%f], diff_time[%d], set_bull[%d] \n"
                            % (stock_code, buy_order_price, buy_cnt, bull_power, diff_time, threshold_make_amount))
                        self.f_log.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")

                    else:
                        # Simulation 때는 바로 사는 것으로
                        if (self.opw00018Data['stocks']):
                            retention_cnt = int(self.opw00018Data['stocks'][0][2])
                            retention_price = int(self.opw00018Data['stocks'][0][3])
                            total_cnt = retention_cnt + int(buy_cnt)
                            avg_price = int(
                                ((retention_price * retention_cnt) + (buy_order_price * int(buy_cnt))) / total_cnt)
                            list_data = ["A" + stock_code, "SIMULATION", str(total_cnt), str(avg_price)]
                            self.opw00018Data = {'accountEvaluation': [], 'stocks': []}
                            self.opw00018Data['stocks'].append(list_data)

                        else:  # empty
                            list_data = ["A" + stock_code, "SIMULATION", buy_cnt, str(buy_order_price)]
                            self.opw00018Data['stocks'].append(list_data)

                        self.f_sim.write("============================================================\n" +
                                         "[" + split_data[0] + "][BUY ]:LINE[" + str(self.csv_row_cnt) +
                                         "]:\tCODE[" + stock_code + "]:\t" +
                                         "BULL[" +
                                         str(bull_power) + "]:\tDIFF_T[" + str(diff_time) +
                                         "]:\tORDER_PRICE[" + str(buy_order_price) + "]:\t\n" +
                                         "============================================================\n")
                else:
                    print(str(datetime.today()))
                    print("S================================================================")
                    print("CODE[%s]:CON1[%s]" %
                                         ( stock_code, (bull_power >= threshold_make_amount) ) )

                    print("Code[%s]:CON1:ARG1[%f]:ARG2[%f]" % (stock_code, bull_power, threshold_make_amount))
                    print("E================================================================")

                # 초기화
                self.code_auto_flag_rule_bull[stock_code] = False
                self.trans_data_rule_bull[stock_code] = [0, 0]


        # Sell
        if (self.auto_trade_flag):
            for stock_list in self.opw00018Data['stocks']:

                # 잔고 조회 후에 stock 이 존재하면
                if (stock_list[0] == ("A" + stock_code)):
                    # 매입가 대비 1% 가 오른 현재 가격이면 매도 주문
                    bought_price = int(stock_list[3])
                    if ( ((bought_price * profit_rate) <= current_price) or
                            ((bought_price * loss_rate) >= current_price)  ):

                        self.log_edit.append("매도[%s]: 현재가[%d] - 매입가[%d] = [%d]" %
                                             (stock_code,  current_price, bought_price, int(current_price-bought_price)) )

                        #self.f_log.write("매도[%s]: 현재가[%d] - 매입가[%d] = [%d]\n" %
                        #                     (stock_code,  current_price, bought_price, int(current_price-bought_price)))

                        if ((bought_price * loss_rate) >= current_price):
                            self.f_log.write("[손절]=")
                        else:
                            self.f_log.write("[수익]=")

                        sell_order_price = 0

                        if ((first_sell_price - first_buy_price) > step_price):
                            sell_order_price = first_buy_price + step_price
                        else:
                            sell_order_price = first_buy_price

                        if (not self.simulation_flag):

                            # 기존에 매도 주문 내역이 없으면 바로 매도 주문
                            if (not self.sell_order_list.get(str("A" + stock_code))):
                                self.testAutoBuy(stock_code, 2, str(sell_order_price), stock_list[2])
                                self.sell_order_list[str("A" + stock_code)] = int(stock_list[2])
                                self.log_edit.append("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                     ", 수량: " + str(stock_list[2]))
                                self.f_log.write("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                     ", 수량: " + str(stock_list[2]) + "\n")
                                self.f_log.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")

                            # 기존에 매도 주문 내역이 있고, 매도 주문을 낼 수 있는 잔량이 있으면 매도 주문
                            elif ((int(stock_list[2]) - self.sell_order_list[str("A" + stock_code)]) > 0):
                                self.testAutoBuy(stock_code, 2, str(sell_order_price), stock_list[2])
                                self.sell_order_list[str("A" + stock_code)] = self.sell_order_list[str("A" + stock_code)] +\
                                                                              int(stock_list[2])
                                self.log_edit.append("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                     ", 수량: " + str(stock_list[2]))
                                self.f_log.write("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                 ", 수량: " + str(stock_list[2]) + "\n")
                                self.f_log.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")

                            # 매도 할 수 있는 잔고가 없을 때
                            else:
                                print("매도 할 수 있는 잔고가 없습니다.")
                                self.log_edit.append("매도 잔고 없음: " + stock_code)

                        else:
                            # simulation 때
                            print("Sell[%s]count[%s]" % (stock_code, str(stock_list[2])))
                            self.log_edit.append("매도 주문: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                 ", 수량: " + str(stock_list[2]))

                            self.f_sim.write("============================================================\n" +
                                         "[" + split_data[0] + "][SELL]:LINE[" + str(self.csv_row_cnt) +
                                         "]:\tCODE[" + stock_code + "]:" +
                                         "\tPRICE[" + str(sell_order_price) + "]:" +
                                         "\tAMOUNT[" + str(stock_list[2]) + "]:" +
                                         "\tPROFIT[" + str(sell_order_price - int(stock_list[3])) + "]:" +
                                         "\n" + "============================================================\n")

                            del self.opw00018Data['stocks'][:]

                # count  #stock_list[2]
                # 매입가 #stock_list[3]

    def testAutoBuy(self, stock_code, order_type, price, amount):

        type = {1: "신규매수", 2: "신규매도", 3: "매수취소", 4: "매도취소", 5: "매수정정", 6: "매도정정"}

        self.log_edit.append(str(datetime.today()) + " 주문유형:" + type[order_type] + ", " + stock_code + "," + price + "," + amount)
        self.f_log.write(str(datetime.today()) + " 주문유형:" + type[order_type] + ", " + stock_code + "," + price + "," + amount + "\n")
        self.sendOrder("testorder", "1002", self.account_num, order_type, stock_code, int(amount), abs(int(price)), "00", "")


    def receiveRealData(self, code, realType, realData):
        """
        실시간 데이터 수신 이벤트

        실시간 데이터를 수신할 때 마다 호출되며,
        setRealReg() 메서드로 등록한 실시간 데이터도 이 이벤트 메서드에 전달됩니다.
        getCommRealData() 메서드를 이용해서 실시간 데이터를 얻을 수 있습니다.

        :param code: string - 종목코드
        :param realType: string - 실시간 타입(KOA의 실시간 목록 참조)
        :param realData: string - 실시간 데이터 전문
        """

        try:

            if realType not in RealType.REALTYPE:
                return

            data = []

            if code != "":
                data.append(code)
                codeOrNot = code
            else:
                codeOrNot = realType

            #print(realType)
            if realType == '주식체결' :
                if (self.db_flag) :
                    ohlcv = {'날짜': [], '체결시간(HHMMSS)': [], '체결가': [], '전일대비': [], '등락율': [],
                                  '최우선매도호가': [], '최우선매수호가': [], '체결량': [], '누적체결량': [],
                                  '누적거래대금': [], '시가': [], '고가': [], '저가': [], '전일대비기호': [],
                                  '전일거래량대비(계약,주)': [], '거래대금증감': [], '전일거래량대비(비율)': [],
                                  '거래회전율': [], '거래비용': [], '체결강도': [], '시가총액(억)': [],
                                  '장구분': [], 'KO접근도': []}

                for fid in sorted(RealType.REALTYPE[realType].keys()):
                    value = self.getCommRealData(codeOrNot, fid)

                    if (self.db_flag):
                        ohlcv[RealType.REALTYPE[realType][fid]].append(value)

                    data.append(value)


                # Rule Check for automation trade
                if(self.auto_trade_flag):
                    #self.checkCondition(data)
                    self.checkCondition_rule_bull(data)

                if (self.db_flag):
                    ohlcv['날짜'].append(str(datetime.today()))
                    self.df = pd.DataFrame(ohlcv, columns=[
                        '체결시간(HHMMSS)', '체결가', '전일대비', '등락율', '최우선매도호가', '최우선매수호가',
                        '체결량', '누적체결량', '누적거래대금', '시가', '고가', '저가', '전일대비기호',
                        '전일거래량대비(계약,주)', '거래대금증감', '전일거래량대비(비율)', '거래회전율',
                        '거래비용', '체결강도', '시가총액(억)', '장구분', 'KO접근도'], index=ohlcv['날짜'])

                    self.df.to_sql(codeOrNot, self.conn, if_exists='append')

                    for fid in sorted(RealType.REALTYPE[realType].keys()):
                        del ohlcv[RealType.REALTYPE[realType][fid]][:]
                    del ohlcv['날짜'][:]

            elif realType == "잔고" :
                value_list = []
                for fid in sorted(RealType.REALTYPE[realType].keys()):
                    value = self.getCommRealData(codeOrNot, fid)

                    value_list.append(value)
                print("!!!!! 잔고 !!!!!")
                print(value_list)

        except Exception as e:
            print(e)

    def getCommRealData(self, code, fid):
        """
        실시간 데이터 획득 메서드

        이 메서드는 반드시 receiveRealData() 이벤트 메서드가 호출될 때, 그 안에서 사용해야 합니다.

        :param code: string - 종목코드
        :param fid: - 실시간 타입에 포함된 fid
        :return: string - fid에 해당하는 데이터
        """
        if not (isinstance(code, str)
                and isinstance(fid, int)):
            raise ParameterTypeError()

        value = self.kiwoom_api.dynamicCall("GetCommRealData(QString, int)", code, fid)

        return value

    def setRealReg(self, screenNo, codes, fids, realRegType):
        """
        실시간 데이터 요청 메서드

        종목코드와 fid 리스트를 이용해서 실시간 데이터를 요청하는 메서드입니다.
        한번에 등록 가능한 종목과 fid 갯수는 100종목, 100개의 fid 입니다.
        실시간등록타입을 0으로 설정하면, 첫 실시간 데이터 요청을 의미하며
        실시간등록타입을 1로 설정하면, 추가등록을 의미합니다.

        실시간 데이터는 실시간 타입 단위로 receiveRealData() 이벤트로 전달되기 때문에,
        이 메서드에서 지정하지 않은 fid 일지라도, 실시간 타입에 포함되어 있다면, 데이터 수신이 가능하다.

        :param screenNo: string
        :param codes: string - 종목코드 리스트(종목코드;종목코드;...)
        :param fids: string - fid 리스트(fid;fid;...)
        :param realRegType: string - 실시간등록타입(0: 첫 등록, 1: 추가 등록)
        """


        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return
            #self.commConnect()
            #raise KiwoomConnectError()

        if not (isinstance(screenNo, str)
                and isinstance(codes, str)
                and isinstance(fids, str)
                and isinstance(realRegType, str)):
            raise ParameterTypeError()

        print("실시간 데이터 요청:" + codes)
        self.kiwoom_api.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                         screenNo, codes, fids, realRegType)

        #result = ""
        #result = " 실시간체결정보 받기 시작: " + codes
        #self.log_edit.append(result)
        #self.listWidget.addItems(widget_list)

    def setRealRemove(self, screenNo, code):
        """
        실시간 데이터 중지 메서드

        setRealReg() 메서드로 등록한 종목만, 이 메서드를 통해 실시간 데이터 받기를 중지 시킬 수 있습니다.

        :param screenNo: string - 화면번호 또는 ALL 키워드 사용가능
        :param code: string - 종목코드 또는 ALL 키워드 사용가능
        """

        if not self.getConnectState():
            print("로그인 후 사용하세요")
            self.log_edit.append("로그인 후 사용하세요.")
            return

        if not (isinstance(screenNo, str)
                and isinstance(code, str)):
            raise ParameterTypeError()

        print("실시간 데이터 요청 중지:" + code)
        self.kiwoom_api.dynamicCall("SetRealRemove(QString, QString)", screenNo, code)

        #result = ""
        #result = " 실시간체결정보 받기 중지: " + code

        #self.log_edit.append(result)
        #self.listWidget.addItems(widget_list)

    def GetServerGubun(self):
        """
        서버구분 정보를 반환한다.
        리턴값이 "1"이면 모의투자 서버이고, 그 외에는 실서버(빈 문자열포함).

        :return: string
        """

        ret = self.kiwoom_api.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "" )
        return ret

    def commGetData(self, trCode, realType, requestName, index, key):
        """
        데이터 획득 메서드

        receiveTrData() 이벤트 메서드가 호출될 때, 그 안에서 조회데이터를 얻어오는 메서드입니다.
        getCommData() 메서드로 위임.

        :param trCode: string
        :param realType: string - TR 요청시 ""(빈문자)로 처리
        :param requestName: string - TR 요청명(commRqData() 메소드 호출시 사용된 requestName)
        :param index: int
        :param key: string
        :return: string
        """

        return self.getCommData(trCode, requestName, index, key)

    def getCommData(self, trCode, requestName, index, key):
        """
        데이터 획득 메서드

        receiveTrData() 이벤트 메서드가 호출될 때, 그 안에서 조회데이터를 얻어오는 메서드입니다.

        :param trCode: string
        :param requestName: string - TR 요청명(commRqData() 메소드 호출시 사용된 requestName)
        :param index: int
        :param key: string - 수신 데이터에서 얻고자 하는 값의 키(출력항목이름)
        :return: string
        """

        if not (isinstance(trCode, str)
                and isinstance(requestName, str)
                and isinstance(index, int)
                and isinstance(key, str)):
            raise ParameterTypeError()

        data = self.kiwoom_api.dynamicCall("GetCommData(QString, QString, int, QString)",
                                trCode, requestName, index, key)
        return data.strip()

    def changeFormat(self, data, percent=0):

        if percent == 0:
            d = int(data)
            formatData = '{:-d}'.format(d)

        elif percent == 1:
            f = int(data) / 100
            formatData = '{:-,.2f}'.format(f)

        elif percent == 2:
            f = float(data) / 100
            formatData = '{:-,.2f}'.format(f)

        return formatData

    def setInputValue(self, key, value):
        """
        TR 전송에 필요한 값을 설정한다.

        :param key: string - TR에 명시된 input 이름
        :param value: string - key에 해당하는 값
        """

        if not (isinstance(key, str) and isinstance(value, str)):
            raise ParameterTypeError()

        self.kiwoom_api.dynamicCall("SetInputValue(QString, QString)", key, value)

    def commRqData(self, requestName, trCode, inquiry, screenNo):
        """
        키움서버에 TR 요청을 한다.

        조회요청메서드이며 빈번하게 조회요청시, 시세과부하 에러값 -200이 리턴된다.

        :param requestName: string - TR 요청명(사용자 정의)
        :param trCode: string
        :param inquiry: int - 조회(0: 조회, 2: 남은 데이터 이어서 요청)
        :param screenNo: string - 화면번호(4자리)
        """

        if not self.getConnectState():
            raise KiwoomConnectError()

        if not (isinstance(requestName, str)
                and isinstance(trCode, str)
                and isinstance(inquiry, int)
                and isinstance(screenNo, str)):
            raise ParameterTypeError()

        returnCode = self.kiwoom_api.dynamicCall("CommRqData(QString, QString, int, QString)", requestName, trCode, inquiry,
                                      screenNo)

        if returnCode != ReturnCode.OP_ERR_NONE:
            raise KiwoomProcessingError("commRqData(): " + ReturnCode.CAUSE[returnCode])


        # 루프 생성: receiveTrData() 메서드에서 루프를 종료시킨다.
        #self.requestLoop = QEventLoop()
        #self.requestLoop.exec_()

    def receiveMsg(self, screenNo, requestName, trCode, msg):
        """
        수신 메시지 이벤트

        서버로 어떤 요청을 했을 때(로그인, 주문, 조회 등), 그 요청에 대한 처리내용을 전달해준다.

        :param screenNo: string - 화면번호(4자리, 사용자 정의, 서버에 조회나 주문을 요청할 때 이 요청을 구별하기 위한 키값)
        :param requestName: string - TR 요청명(사용자 정의)
        :param trCode: string
        :param msg: string - 서버로 부터의 메시지
        """

        #self.msg += requestName + ": " + msg + "\r\n\r\n"
        print(requestName + " :" +  trCode + " :" + msg)

    def getRepeatCnt(self, trCode, requestName):
        """
        서버로 부터 전달받은 데이터의 갯수를 리턴합니다.(멀티데이터의 갯수)

        receiveTrData() 이벤트 메서드가 호출될 때, 그 안에서 사용해야 합니다.

        키움 OpenApi+에서는 데이터를 싱글데이터와 멀티데이터로 구분합니다.
        싱글데이터란, 서버로 부터 전달받은 데이터 내에서, 중복되는 키(항목이름)가 하나도 없을 경우.
        예를들면, 데이터가 '종목코드', '종목명', '상장일', '상장주식수' 처럼 키(항목이름)가 중복되지 않는 경우를 말합니다.
        반면 멀티데이터란, 서버로 부터 전달받은 데이터 내에서, 일정 간격으로 키(항목이름)가 반복될 경우를 말합니다.
        예를들면, 10일간의 일봉데이터를 요청할 경우 '종목코드', '일자', '시가', '고가', '저가' 이러한 항목이 10번 반복되는 경우입니다.
        이러한 멀티데이터의 경우 반복 횟수(=데이터의 갯수)만큼, 루프를 돌면서 처리하기 위해 이 메서드를 이용하여 멀티데이터의 갯수를 얻을 수 있습니다.

        :param trCode: string
        :param requestName: string - TR 요청명(commRqData() 메소드 호출시 사용된 requestName)
        :return: int
        """

        if not (isinstance(trCode, str)
                and isinstance(requestName, str)):
            raise ParameterTypeError()

        count = self.kiwoom_api.dynamicCall("GetRepeatCnt(QString, QString)", trCode, requestName)
        return count

    def opwDataReset(self):
        """ 잔고 및 보유종목 데이터 초기화 """
        self.opw00001Data = 0
        #self.opw00018Data = {'accountEvaluation': [], 'stocks': []}
        self.opw00007Data = {'orderList': []}

    def receiveTrData(self, screenNo, requestName, trCode, recordName, inquiry,
                      deprecated1, deprecated2, deprecated3, deprecated4):
        """
        TR 수신 이벤트

        조회요청 응답을 받거나 조회데이터를 수신했을 때 호출됩니다.
        requestName과 trCode는 commRqData()메소드의 매개변수와 매핑되는 값 입니다.
        조회데이터는 이 이벤트 메서드 내부에서 getCommData() 메서드를 이용해서 얻을 수 있습니다.

        :param screenNo: string - 화면번호(4자리)
        :param requestName: string - TR 요청명(commRqData() 메소드 호출시 사용된 requestName)
        :param trCode: string
        :param recordName: string
        :param inquiry: string - 조회('0': 남은 데이터 없음, '2': 남은 데이터 있음)
        """
        print("receiveTrData 실행: ", screenNo, requestName, trCode, recordName, inquiry)

        # 주문번호와 주문루프
        self.orderNo = self.commGetData(trCode, "", requestName, 0, "주문번호")

        self.inquiry = inquiry

        if requestName == "예수금상세현황요청":
            deposit = self.commGetData(trCode, "", requestName, 0, "예수금")
            deposit = self.changeFormat(deposit)
            self.opw00001Data = deposit
            print("예수금: " + self.opw00001Data)
            self.log_edit.append(" 예수금: " + self.opw00001Data)

            demand_amount = self.commGetData(trCode, "", requestName, 0, "주문가능금액")
            demand_amount = self.changeFormat(demand_amount)

            print("주문가능금액: " + demand_amount)
            self.log_edit.append(" 주문가능금액: " + demand_amount)

        elif requestName == "계좌평가잔고내역요청":

            # data reset
            self.opw00018Data = {'accountEvaluation': [], 'stocks': []}

            # 계좌 평가 정보
            accountEvaluation = []
            keyList = ["총매입금액", "총평가금액", "총평가손익금액", "총수익률(%)", "추정예탁자산"]
            account_info_str_list = " 총매입금액\t총평가금액\t총평가손익\t총수익률(%)\t추정예탁자산"

            account_info_list = ""
            for key in keyList:
                value = self.commGetData(trCode, "", requestName, 0, key)

                if key.startswith("총수익률"):
                    value = self.changeFormat(value, 2)
                else:
                    value = self.changeFormat(value)

                account_info_list += value + "\t"

                accountEvaluation.append(value)

            self.opw00018Data['accountEvaluation'] = accountEvaluation

            self.account_info_edit.clear()
            self.account_info_edit.append(account_info_str_list)
            self.account_info_edit.append(account_info_list + "\n")

            # 보유 종목 정보
            cnt = self.getRepeatCnt(trCode, requestName)
            keyList = [ "종목번호", "종목명", "보유수량", "매입가", "현재가", "평가손익", "수익률(%)"]

            stock_str_list = " 종목번호\t종목명\t보유수량\t매입가\t현재가\t평가손익\t수익률(%)"
            #self.account_info_edit.clear()
            self.account_info_edit.append(stock_str_list)

            for i in range(cnt):
                stock = []

                stock_info_list = ""
                for key in keyList:
                    value = self.commGetData(trCode, "", requestName, i, key)
                    if key.startswith("수익률"):
                        value = self.changeFormat(value, 2)
                    elif key != "종목명" and key != "종목번호":
                        value = self.changeFormat(value)
                    stock_info_list = stock_info_list + value + "\t"
                    stock.append(value)

                self.account_info_edit.append(stock_info_list)
                self.opw00018Data['stocks'].append(stock)

            self.account_info_date_label.setText(str(datetime.today()))

        elif requestName == "계좌별주문체결내역상세요청":
            # data reset
            self.opw00007Data = {'orderList': []}

            value = self.commGetData(trCode, "", requestName, 0, "출력건수")

            if(value is ""):
                cnt = 0
            else:
                cnt = int(value)

            # 체결 정보
            keyList = ["주문번호", "종목번호", "주문구분", "주문수량", "주문단가", "확인수량", "체결수량", "체결단가", "주문잔량"]

            trans_str_list = " 주문번호\t종목번호\t주문구분\t주문수량\t주문단가\t확인수량\t체결수량\t체결단가\t주문잔량"
            self.transaction_info_edit.clear()
            self.transaction_info_edit.append(trans_str_list)

            self.opwDataReset()

            self.sell_order_list.clear()
            for i in range(cnt):
                orderList = []

                trans_info_list = ""
                for key in keyList:
                    value = self.commGetData(trCode, "", requestName, i, key)

                    if not (key == "주문번호" or key == "종목번호" or key == "주문구분"):
                        value = self.changeFormat(value)

                    orderList.append(value)
                    trans_info_list = trans_info_list + value + "\t"

                self.transaction_info_edit.append(trans_info_list)
                self.opw00007Data['orderList'].append(orderList)

                # TODO: different between real server and virtual server
                if(orderList[2] == "현금매도"):
                    # 종목 번호: orderList[1]
                    # 주문 잔량: orderList[8]
                    if (self.sell_order_list.get(orderList[1])):
                        self.sell_order_list[orderList[1]] += int(orderList[8])
                    else:
                        self.sell_order_list[orderList[1]] = int(orderList[8])

            print(self.opw00007Data)
            print(self.sell_order_list)
            self.transaction_date_label.setText(str(datetime.today()))

        elif requestName == "저가근접조회":
            print("저가근접조회!!!")

            stock_amount = len(self.opw00018Data['stocks'])
            cnt = self.getRepeatCnt(trCode, requestName)

            temp_list = self.realtimeList

            self.btn_total_real_stop_clicked()

            for stock_list in self.opw00018Data['stocks']:
                self.set_real_start(stock_list[0][1:])

            if (stock_amount + cnt > 100):
                cnt = 100 - stock_amount

            for i in range(cnt):
                value = self.commGetData(trCode, "", requestName, i, "종목코드")
                self.set_real_start(value)

            if(len(self.realtimeList) < 100):
                for code in self.kospi_100:
                    self.set_real_start(code)

            print("저가근접 List Count: %d" % (cnt))
            print("실시간종목 Count: %d" % (len(self.realtimeList)))

        elif requestName == "고가근접조회":
            print("고가근접조회!!!")

            stock_amount = len(self.opw00018Data['stocks'])
            cnt = self.getRepeatCnt(trCode, requestName)

            temp_list = self.realtimeList

            self.btn_total_real_stop_clicked()

            for stock_list in self.opw00018Data['stocks']:
                self.set_real_start(stock_list[0][1:])

            if (stock_amount + cnt > 100):
                cnt = 100 - stock_amount

            for i in range(cnt):
                value = self.commGetData(trCode, "", requestName, i, "종목코드")
                self.set_real_start(value)

            if(len(self.realtimeList) < 100):
                for code in self.kospi_100:
                    self.set_real_start(code)

            print("고가근접 List Count: %d" % (cnt))
            print("실시간종목 Count: %d" % (len(self.realtimeList)))


    def getChejanData(self, fid):
        """
        주문접수, 주문체결, 잔고정보를 얻어오는 메서드

        이 메서드는 receiveChejanData() 이벤트 메서드가 호출될 때 그 안에서 사용해야 합니다.

        :param fid: int
        :return: string
        """

        if not isinstance(fid, int):
            raise ParameterTypeError()

        cmd = 'GetChejanData("%s")' % fid
        data = self.kiwoom_api.dynamicCall(cmd)
        return data

    def receiveChejanData(self, gubun, itemCnt, fidList):
        """
        주문 접수/확인 수신시 이벤트

        주문요청후 주문접수, 체결통보, 잔고통보를 수신할 때 마다 호출됩니다.

        :param gubun: string - 체결구분('0': 주문접수/주문체결, '1': 잔고통보, '3': 특이신호)
        :param itemCnt: int - fid의 갯수
        :param fidList: string - fidList 구분은 ;(세미콜론) 이다.
        """

        fids = fidList.split(';')
        print("[receiveChejanData]")
        print("gubun: ", gubun, "itemCnt: ", itemCnt, "fidList: ", fidList)
        print("========================================")

        print("[ 구분: ", self.getChejanData(913) if '913' in fids else '잔고통보', "]")

        if(self.getChejanData(913) == "체결"):

            # accept amount
            #self.getChejanData(911)

            # stock code
            code = self.getChejanData(9001)
            amount = int(self.getChejanData(911))
            order_num = self.getChejanData(9203)

            self.log_edit.append("체결 통보 : " + code + ", 주문번호: " + order_num + ", 체결량: " + str(amount))
            self.btn_query_account_clicked()
            self.btn_query_order_clicked()

            # 체결된 수량 만큼 sell_order_list 에서 뺌
            #if(self.sell_order_list.get(code)):
            #    self.sell_order_list[code] = self.sell_order_list[code] - amount
            #    print("Sell Order List!!")
            #    print(self.sell_order_list)

        self.f_log.write(self.getChejanData(913) + "\n")
        for fid in fids:
            print(FidList.CHEJAN[int(fid)] if int(fid) in FidList.CHEJAN else fid, ": ", self.getChejanData(int(fid)))

            if int(fid) in FidList.CHEJAN:
                log_data = FidList.CHEJAN[int(fid)] + ": " + self.getChejanData(int(fid)) + "\n"
                self.f_log.write(log_data)

            #self.f_log.write(FidList.CHEJAN[int(fid)] if int(fid) in FidList.CHEJAN else fid, ": ", self.getChejanData(int(fid)))
            #log = FidList.CHEJAN[int(fid)] +  ": " + self.getChejanData(int(fid))

        self.f_log.write("==========================================\n")
        self.f_log.flush()
        print("========================================")


    def sendOrder(self, requestName, screenNo, accountNo, orderType, code, qty, price, hogaType, originOrderNo):

        """
        주식 주문 메서드

        sendOrder() 메소드 실행시,
        OnReceiveMsg, OnReceiveTrData, OnReceiveChejanData 이벤트가 발생한다.
        이 중, 주문에 대한 결과 데이터를 얻기 위해서는 OnReceiveChejanData 이벤트를 통해서 처리한다.
        OnReceiveTrData 이벤트를 통해서는 주문번호를 얻을 수 있는데, 주문후 이 이벤트에서 주문번호가 ''공백으로 전달되면,
        주문접수 실패를 의미한다.

        :param requestName: string - 주문 요청명(사용자 정의)
        :param screenNo: string - 화면번호(4자리)
        :param accountNo: string - 계좌번호(10자리)
        :param orderType: int - 주문유형(1: 신규매수, 2: 신규매도, 3: 매수취소, 4: 매도취소, 5: 매수정정, 6: 매도정정)
        :param code: string - 종목코드
        :param qty: int - 주문수량
        :param price: int - 주문단가
        :param hogaType: string - 거래구분(00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 그외에는 api 문서참조)
        :param originOrderNo: string - 원주문번호(신규주문에는 공백, 정정및 취소주문시 원주문번호르 입력합니다.)
        """

        if not self.getConnectState():
            raise KiwoomConnectError()

        if not (isinstance(requestName, str)
                and isinstance(screenNo, str)
                and isinstance(accountNo, str)
                and isinstance(orderType, int)
                and isinstance(code, str)
                and isinstance(qty, int)
                and isinstance(price, int)
                and isinstance(hogaType, str)
                and isinstance(originOrderNo, str)):
            raise ParameterTypeError()

        returnCode = self.kiwoom_api.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                      [requestName, screenNo, accountNo, orderType, code, qty, price, hogaType,
                                       originOrderNo])

        if returnCode != ReturnCode.OP_ERR_NONE:
            raise KiwoomProcessingError("sendOrder(): " + ReturnCode.CAUSE[returnCode])


if __name__ == "__main__":

    app = QApplication(sys.argv)

    try:
        w_kiwoom = StockWindow()
        w_kiwoom.show()

    except Exception as e:
        print(e)

    sys.exit(app.exec_())

