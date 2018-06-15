# -*- coding: utf-8 -*-

from __future__ import division
import csv
import sys
import re
from datetime import datetime

class StockClass():
    def __init__(self):

        # 메시지
        self.msg = ""
        self.screenNo = "6002"
        self.realtimeList = []

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

        # 최저가 저장을 위한
        self.lowest_price = {}

        # 자동매매 Flag (코드별)
        self.code_auto_flag = {}

        # 자동매매 Flag
        self.auto_trade_flag = True

        # 체결강도 차이를 위해
        self.before_stock_data = {}

        # 매수호가가 한단계 올라갔을 때 시점의 체결 count 체크를 위한
        self.trans_cnt = {}

        # 매수세 체크를 위해 Flag 가 시작된 시간 저장을 위한
        self.check_trans_time = {}

        # 체결 count 가 만족할 때 매수/매도 세를 저장하기 위한
        # trans_data[stock_code][0] = 매수체결량
        # trans_data[stock_code][0] = 매도체결량
        self.trans_data = {}

        # Sell order list
        self.sell_order_list = {}

        # kospi list
        self.kospi_code_list = []

        # kosdaq list
        self.kosdaq_code_list = []


        file_name = str(datetime.now().strftime('%Y%m%d')) + ".txt"
        self.f = open(file_name, "w")

        self.csv_row_cnt = 0

        self.before_date = ""

    def checkCondition(self, data_list):
        self.csv_row_cnt += 1
        if (len(data_list) == 0 or len(data_list) < 23):
            print("empty")
            return

        if(data_list[0] == "index"):
            print("first row")
            return

        split_data = re.split(" ", data_list[0])
        if(self.before_date != split_data[0]):
            self.before_date = split_data[0]
            self.lowest_price.clear()
            print("=============================================")
            print("Clear lowest price")
            print("=============================================")


        #체결시간 9시 전이면 return
        if(abs(int(data_list[1])) < 90000):
            print("[before am 9]")
            return

        buy_cnt = "10"

        # 1% 수익 목표
        profit_rate = 1.01

        # 체결강도 차이가 0.1 이상일 때 주문
        diff_strong = 0.1

        # 매수 호가가 최저보다 한단계 위 일때 그 전 체결 주문이 100개 이상
        threshold_cnt = 100

        # 위의 threshold_cnt 를 만족하고 그 구간 체결강도(매수/매도) 가 몇 이상일 때
        threshold_amount = 2

        threshold_time = 60

        # Buy
        stock_code = "000660"
        current_price = abs(int(data_list[2]))
        low_price = abs(int(data_list[12]))
        first_sell_price = abs(int(data_list[5]))
        first_buy_price = abs(int(data_list[6]))
        strong = abs(float(data_list[19]))
        trans_amount = int(data_list[7])
        trans_time = data_list[1]

        # 처음 들어온 Data 는 before_stock_data 가 없으므로..
        # 이 if 는 각 Stock Code 마다 한번 씩만
        if (not self.before_stock_data.get(stock_code)):
            self.before_stock_data[stock_code] = data_list

        # 체결강도
        before_strong = abs(float(self.before_stock_data[stock_code][19]))

        # 호가단위 금액 저장을 위한
        step_price = 0

        if (low_price < 1000):
            step_price = 1
        elif (low_price < 5000):
            step_price = 5
        elif (low_price < 10000):
            step_price = 10
        elif (low_price < 50000):
            step_price = 50
        elif (low_price < 100000):
            step_price = 100
        elif (low_price < 500000):
            if(stock_code in self.kospi_code_list):
                step_price = 500
            else:
                step_price = 100
        elif (low_price < 1000000):
            if (stock_code in self.kospi_code_list):
                step_price = 1000
            else:
                step_price = 100

        # 최저가 값이 없을 때 현재 저가 를 저장
        if (not self.lowest_price.get(stock_code)):
            print("Change Lowest price, because empty list")
            self.lowest_price[stock_code] = low_price
            if(not self.code_auto_flag.get(stock_code)):
                print("\t Flag Enable[Empty]:" + stock_code)
            print("Change lowest price location [%d]" % self.csv_row_cnt)
            self.code_auto_flag[stock_code] = True
            self.trans_cnt[stock_code] = 0

            # trans_data[stock_code][0] = 매수체결량
            # trans_data[stock_code][1] = 매도체결량

            self.trans_data[stock_code] = [0, 0]
            self.check_trans_time[stock_code] = trans_time
            return

        # 체결가 = 저가 일 때,
        if (current_price == low_price):

            # 기존에 최저가 보다 낮은 저가가 나왔을 때 최저가 변경
            if (self.lowest_price[stock_code] > low_price):
                print("Change lowest price : " + str(low_price))
                if (not self.code_auto_flag.get(stock_code)):
                    print("\t Flag Enable[found lowest] :"+ stock_code)
                print("Change lowest price location [%d]" % self.csv_row_cnt)
                self.code_auto_flag[stock_code] = True
                self.lowest_price[stock_code] = low_price
                self.trans_cnt[stock_code] = 0
                self.trans_data[stock_code] = [0, 0]
                self.check_trans_time[stock_code] = trans_time

        # 자동 매수 Check Flag 가 Enable 되어있으면 최우선 매수 호가가 한단계 위이고, 체결강도 차이가 0보다 클 때
        # 매수 함
        if (self.code_auto_flag.get(stock_code) and self.auto_trade_flag):
            # 체결 count 저장
            if(self.trans_cnt.get(stock_code)):
                self.trans_cnt[stock_code] = int(self.trans_cnt[stock_code]) + 1
            else :
                self.trans_cnt[stock_code] = 1

            if(trans_amount > 0):
                self.trans_data[stock_code][0] = self.trans_data[stock_code][0] + trans_amount
            else:
                self.trans_data[stock_code][1] = self.trans_data[stock_code][1] + abs(trans_amount)

            # 최우선 매수 호가가 최저가 보다 한단계 위일 때
            if ((self.lowest_price[stock_code] == low_price) and
                    ((self.lowest_price[stock_code] + step_price) == first_buy_price)):

                bull_power = (self.trans_data[stock_code][0] / self.trans_data[stock_code][1])

                # 시간 차이 계산
                before_hour = int(self.check_trans_time[stock_code][:2])
                before_min = int(self.check_trans_time[stock_code][2:4])
                before_sec = int(self.check_trans_time[stock_code][4:])

                current_hour = int(trans_time[:2])
                current_min = int(trans_time[2:4])
                current_sec = int(trans_time[4:])

                diff_time = ((current_hour * 3600) + (current_min * 60) + current_sec) - \
                            ((before_hour * 3600) + (before_min * 60) + before_sec)

                print("one step first buy! - checking condition [%d]" % self.csv_row_cnt)
                print("\tcnt[%d], bull_power[%s], diff_time[%d]" % (self.trans_cnt.get(stock_code),
                                                                    str(bull_power), diff_time))

                if((self.trans_cnt.get(stock_code) > threshold_cnt) and
                       bull_power >= threshold_amount and
                        diff_time >= threshold_time):
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print("Buy!!! bull_power: " + str(bull_power) +
                          ", diff_time: " + str(diff_time))
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                    #print("Buy!!!!!!")

                    buy_order_price = 0
                    if ((first_sell_price - first_buy_price) > step_price):
                        buy_order_price = first_buy_price + step_price
                    else:
                        buy_order_price = first_sell_price

                    #self.testAutoBuy(stock_code, 1, str(buy_order_price), buy_cnt)

                    print("BUY order: " + stock_code + ", row: " + str(self.csv_row_cnt) +
                          ", price: " + str(buy_order_price) +
                                         ", trans_cnt: " + str(self.trans_cnt[stock_code]) + ", bull_power: " +
                                         str(bull_power))
                    print("Check Flag Disable :" + stock_code)

                    self.f.write("[" + split_data[0] + "][BUY ]:LINE[" + str(self.csv_row_cnt) +
                                 "]:\tCODE[" + stock_code + "]:\tCNT[" +
                                 str(self.trans_cnt.get(stock_code)) + "]:\tBULL[" +
                                 str(bull_power) + "]:\tDIFF_T[" + str(diff_time) +
                                 "]:\tPRICE[" + str(buy_order_price) + "]\n")

                    if(self.opw00018Data['stocks']):
                        retention_cnt = int(self.opw00018Data['stocks'][0][2])
                        retention_price = int(self.opw00018Data['stocks'][0][3])
                        total_cnt = retention_cnt+ int(buy_cnt)
                        avg_price = int(((retention_price * retention_cnt) + (buy_order_price * int(buy_cnt))) / total_cnt)
                        list_data = ["A"+stock_code, "SIMULATION", str(total_cnt), str(avg_price)]
                        self.opw00018Data = {'accountEvaluation': [], 'stocks': []}
                        self.opw00018Data['stocks'].append(list_data)
                        #self.opw00018Data['stocks'] = [stock_code, "SIMULATION", str(total_cnt), str(avg_price)]

                    else: # empty
                        list_data = ["A"+stock_code, "SIMULATION", buy_cnt, str(buy_order_price)]
                        #self.opw00018Data['stocks'] = list_data
                        self.opw00018Data['stocks'].append(list_data)

                        #self.opw00018Data['stocks'] = [stock_code, "SIMULATION", buy_cnt, str(buy_order_price)]

                    #print(self.opw00018Data['stocks'])

                # 초기화
                self.code_auto_flag[stock_code] = False
                self.trans_cnt[stock_code] = 0
                self.trans_data[stock_code] = [0, 0]

                #print("Check strong difference")
                #print("Strong: " + str(strong) + ", Before_strong: " + str(before_strong) + " = " +
                      #str(strong - before_strong))

                # 체결 강도 차이가 diff_strong 보다 클 때
                #if ((strong - before_strong) > diff_strong):

        self.before_stock_data[stock_code] = data_list
        #print(self.lowest_price)

        # Sell
        if(self.auto_trade_flag):

            for stock_list in self.opw00018Data['stocks']:
                # 잔고 조회 후에 stock 이 존재하면

                if (stock_list[0] == ("A" + stock_code)):
                    # 매입가 대비 1% 가 오른 현재 가격이면 매도 주문
                    if ((int(stock_list[3]) * profit_rate) <= current_price ):
                        print("1% Increase: " + stock_code)
                        sell_order_price = 0

                        if ((first_sell_price - first_buy_price) > step_price):
                            sell_order_price = first_buy_price + step_price
                        else:
                            sell_order_price = first_buy_price

                        # 기존에 매도 주문 내역이 없으면 바로 매도 주문
                        if(not self.sell_order_list.get(str("A" + stock_code))):
                            #self.testAutoBuy(stock_code, 2, str(first_sell_price), stock_list[2])
                            self.sell_order_list[str("A" + stock_code)] = int(stock_list[2])
                            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            print("Sell!!! current_price: " + str(current_price))
                            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                            print("Sell order: " + stock_code + ", row: " + str(self.csv_row_cnt) +
                                  ", Price: " + str(sell_order_price) +
                                                 ", amount: " + stock_list[2])
                            #print("[Sell] :" + stock_code + "\n")
                            #print("[Sell]!!!!!" + stock_code + ", " + str(sell_order_price) + "," + stock_list[2])
                            #print( self.sell_order_list)
                            print(str(self.sell_order_list))
                            self.f.write("[" + split_data[0] +"][SELL]:LINE[" + str(self.csv_row_cnt) +
                                 "]:\tCODE[" + stock_code + "]:" +
                                    "\tPRICE[" + str(sell_order_price) + "]:" +
                                    "\tAMOUNT[" + stock_list[2] + "]:" +
                                    "\tPROFIT[" + str(sell_order_price-int(stock_list[3])) + "]:" +
                                    "\n")

                            # 무조건 체결된다고 보고...
                            self.sell_order_list[str("A" + stock_code)] -= int(stock_list[2])
                            self.opw00018Data = {'accountEvaluation': [], 'stocks': []}
                            print(str(self.sell_order_list))

                        # 기존에 매도 주문 내역이 있고, 매도 주문을 낼 수 있는 잔량이 있으면 매도 주문
                        elif ( (int(stock_list[2]) - self.sell_order_list[str("A" + stock_code)]) > 0):
                            #self.testAutoBuy(stock_code, 2, str(first_sell_price), stock_list[2])
                            self.sell_order_list[str("A" + stock_code)] = self.sell_order_list[str("A" + stock_code)] + int(stock_list[2])
                            print("Sell order: " + stock_code + ", 가격: " + str(sell_order_price) +
                                                 ", 수량: " + stock_list[2])

                            #print("[Sell]!!!!!" + stock_code + ", " + str(sell_order_price) + "," + stock_list[2])
                            print(str(self.sell_order_list) + "\n")

                        # 매도 할 수 있는 잔고가 없을 때
                        else:
                            print("매도 할 수 있는 잔고가 없습니다.")
                            print("매도 잔고 없음: " + stock_code)

                # count  #stock_list[2]
                # 매입가 #stock_list[3]


if __name__ == "__main__":

    try:
        c_main = StockClass()

    except Exception as e:
        print(e)


    print("Number of arguments: ", len(sys.argv), "arguments")
    print("Arguments List: ", str(sys.argv))

    filename = "C:/Users/User/Desktop/시세/Data/000660.csv"

    if(len(sys.argv) == 2):
        filename = sys.argv[1]

    f = open(filename, "r")
    rdr = csv.reader(f)

    for line in rdr:
#        print(line)
        c_main.checkCondition(line)

    f.close()

