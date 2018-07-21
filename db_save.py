import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3

#TR_REQ_TIME_INTERVAL = 0.2
TR_REQ_TIME_INTERVAL = 2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10003_req":
            self._opt10003(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10003(self, rqname, trcode):
        i = 0
        time = self._comm_get_data(trcode, "", rqname, i, "시간")
        cur_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
        cur_volume = self._comm_get_data(trcode, "", rqname, i, "체결거래량")
        sum_volume = self._comm_get_data(trcode, "", rqname, i, "누적거래량")
        strong = self._comm_get_data(trcode, "", rqname, i, "체결강도")

        print(time + " " + cur_price + " " + cur_volume + " " + sum_volume + " " + strong)

        self.ohlcv['time'].append(time)
        self.ohlcv['cur_price'].append(int(cur_price))
        self.ohlcv['cur_volume'].append(int(cur_volume))
        self.ohlcv['sum_volume'].append(int(sum_volume))
        self.ohlcv['strong'].append(float(strong))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    kiwoom.ohlcv = {'time': [], 'cur_price': [], 'cur_volume': [], 'sum_volume': [], 'strong': [] }

    # 네이처셀 : 007390
    # FSN : 214270
    # KD : 044180
    # 광림: 014200
    code = "214270"

    # opt10003 TR 요청
    for i in range(1):
        kiwoom.set_input_value("종목코드", code)
        kiwoom.comm_rq_data("opt10003_req", "opt10003", 0, "0101")
        time.sleep(TR_REQ_TIME_INTERVAL)

    df = pd.DataFrame(kiwoom.ohlcv, columns=['cur_price', 'cur_volume', 'sum_volume', 'strong'], index=kiwoom.ohlcv['time'])

    print(df.head())

    con = sqlite3.connect("c:/kiwoom_db/test_stock.db")
    #df.to_sql('039490', con, if_exists='replace')
    df.to_sql(code, con, if_exists='append')