import websocket,json,pprint, talib, numpy

from binance.client import Client
from binance.enums import *
import config
import datetime
from helpers import *
import time
import os
import threading
from history import *
from indicators import *
from hedge_long import *

from hedge_short import *



class Manager():
    def __init__(self):
        #setups
        self.vers = "hedge"
        self.TRADE_SYMBOL = "DOGEUSDT"
        self.long_shares = 0
        self.HISTORY_INTERVAL=Client.KLINE_INTERVAL_1MINUTE
        self.TRADE_INTERVAL = "1m"
        self.MIN_SHARES = 1000
        self.EMA1_WINDOW = 3
        self.tp = .005

        self.foo_email = "3102796480@tmomail.net"
        self.alex_email = "3235594184@vtext.com"

        self.SOCKET = f'wss://stream.binance.com:9443/ws/{self.TRADE_SYMBOL.lower()}@kline_{self.TRADE_INTERVAL}'

        self.client = Client(config.API_KEY,config.API_SECRET, tld='us')

        self.running_profit = 0
        self.trades_updated = []

        self.financials = {}
        #bars
        self.close = 0
        self.barCount =0
        self.CANDLES = []
        self.closes =[]
        #RT
        self.tick_price = 0

        #account
        
        self.account_start_balance = 0
        
        #bot_account
        self.bot_start_balance = 0
        self.bot_end_balance = 0
        self.bot_running_profit = 0
        self.bot_final_profit = 0



        

    def update(self,close_):
        self.set_close(close_)

        #GET and PRINT BALANCES
        self.get_current_balance(self.get_close())

        self.set_financials(self.get_close())
        self.write_finanicials_to_file("financials.txt",self.create_shares_to_open_row())

    def balances(self,close_):
        free_USDT = self.get_USDT_balance("USDT")
        doge_in_USDT = self.get_USDT_balance("DOGE")
        free_USD = self.get_USDT_balance("USD")

        print(f'DOGE balance {self.get_USDT_balance("DOGE")}')
        print(f'USDT balance {self.get_USDT_balance("USDT")}')
        print(f'APROX TOTAL USD VALUE {free_USD+free_USDT+(doge_in_USDT*close_)}')

        print(f'profit since 12:57 {free_USD+free_USDT+(doge_in_USDT*close_)-28902}')

        
    def account_running_profit(self,close_):
        free_USDT = self.get_USDT_balance("USDT")
        doge_in_USDT = self.get_USDT_balance("DOGE")
        free_USD = self.get_USDT_balance("USD")

        # print(f'DOGE balance {self.get_USDT_balance("DOGE")}')
        # print(f'USDT balance {self.get_USDT_balance("USDT")}')
        # print(f'APROX TOTAL USD VALUE {free_USD+free_USDT+(doge_in_USDT*close_)}')

        # print(f'profit since 12:57 {free_USD+free_USDT+(doge_in_USDT*close_)-28902}')
    def get_account_start_balance():
        pass



    def set_close(self,close):
        self.close = close
    def get_close(self):
        return self.close 

    def set_financials(self,close):
        self.financials = {"short_shares":self.get_open_short_shares(),"long_shares":self.get_open_long_shares(),"diff":self.get_diff(self.get_open_long_shares(),self.get_open_short_shares())}

    def get_diff(self,a,b):
        diff = a-b #longs-shorts
        return diff
    
    def get_financials(self):
        return self.financials

    def get_longs_to_buy(self):
        financials = self.get_financials()
        diff = financials["diff"]
        short_shares = financials["short_shares"]
        long_shares = financials["long_shares"]
        longs_to_buy = 0
        if diff < 0:
            longs_to_buy = abs(diff)
            return longs_to_buy
        else:
            return self.MIN_SHARES
    
    def get_shorts_to_buy(self):
        financials = self.get_financials()
        diff = financials["diff"]
        short_shares = financials["short_shares"]
        long_shares = financials["long_shares"]
        shorts_to_buy = 0
        if diff > 0:
            shorts_to_buy = abs(diff)
            return shorts_to_buy
        else:
            return self.MIN_SHARES
    

        #fintec logic
    def get_short_losses(self,close):
        self.read_list_from_file("hedge_TRADES.txt") #???
        closed_IDs = []
        only_1_IDs = []
        idss = []
        loss = 0
        losses = []
        if len(self.trades_updated) >0:
            for i in range(len(self.trades_updated)):
                idss.append(self.trades_updated[i]["ID"])
            for y in range(len(idss)):
                if idss.count(self.trades_updated[y]["ID"]) ==1:
                     only_1_IDs.append(self.trades_updated[y])
            for trade in only_1_IDs: #loop in reverse
                if trade["short"] ==1 and trade["open"] ==1:
                    loss = trade["entry_price"] - close
                    losses.append(loss)
        return sum(losses)
    
    def get_long_losses(self,close):
        self.read_list_from_file("hedge_TRADES.txt") #???
        closed_IDs = []
        only_1_IDs = []
        idss = []
        loss = 0
        losses = []
        if len(self.trades_updated) >0:
            for i in range(len(self.trades_updated)):
                idss.append(self.trades_updated[i]["ID"])
            for y in range(len(idss)):
                if idss.count(self.trades_updated[y]["ID"]) ==1:
                     only_1_IDs.append(self.trades_updated[y])
            for trade in only_1_IDs: #loop in reverse
                if trade["long"] ==1 and trade["open"] ==1:
                    loss = close - trade["entry_price"]  
                    losses.append(loss)
        
        return sum(losses)
    
    def get_long_wins(self,close):
        self.read_list_from_file("hedge_TRADES.txt") #???
        closed_IDs = []
        only_1_IDs = []
        idss = []
        win = 0
        wins = []
        if len(self.trades_updated) >0:
            for i in range(len(self.trades_updated)):
                if self.trades_updated[i]["long"]==1 and self.trades_updated[i]["closed"] == 1:
                    wins.append(self.trades_updated[i]["profit"])
        return sum(wins)
    
    def get_short_wins(self,close):
        self.read_list_from_file("hedge_TRADES.txt") #???
        closed_IDs = []
        only_1_IDs = []
        idss = []
        win = 0
        wins = []
        if len(self.trades_updated) >0:
            for i in range(len(self.trades_updated)):
                if self.trades_updated[i]["short"]==1 and self.trades_updated[i]["closed"] == 1:
                    wins.append(self.trades_updated[i]["profit"])
        return sum(wins)

    def get_current_balance(self,close):
        total_wins = self.get_long_wins(close) + self.get_short_wins(close)
        print(f'TOTAL_WINS:{total_wins}')
        total_losses = self.get_short_losses(close) + self.get_long_losses(close)
        print(f'TOTAL LOSS: {total_losses}')

        balance = total_wins + total_losses
        print(f'BALANCE   : {balance}')
        return balance

    def get_stake_balance(self,close):
        pass
    def get_stake(self):
        pass
    def get_USDT_balance(self,symbol):
        symbol_position = client.get_asset_balance(asset=symbol)
        
        balance = float(symbol_position["free"]) - float(symbol_position["locked"])
        return balance




    
    
    def get_open_short_shares(self):
        self.read_list_from_file("hedge_TRADES.txt") #???
        closed_IDs = []
        only_1_IDs = []
        idss = []
        shares = 0
        total_shares = []
        if len(self.trades_updated) >0:
            for i in range(len(self.trades_updated)):
                idss.append(self.trades_updated[i]["ID"])
            for y in range(len(idss)):
                if idss.count(self.trades_updated[y]["ID"]) ==1:
                     only_1_IDs.append(self.trades_updated[y])
            for trade in only_1_IDs: #loop in reverse
                if trade["short"] ==1 and trade["open"] ==1:
                    shares = trade["shares"]
                    total_shares.append(shares)
        return sum(total_shares)

    def get_open_long_shares(self):
        self.read_list_from_file("hedge_TRADES.txt") #???
        closed_IDs = []
        only_1_IDs = []
        idss = []
        shares = 0
        total_shares = []
        if len(self.trades_updated) >0:
            for i in range(len(self.trades_updated)):
                idss.append(self.trades_updated[i]["ID"])
            for y in range(len(idss)):
                if idss.count(self.trades_updated[y]["ID"]) ==1:
                     only_1_IDs.append(self.trades_updated[y])
            for trade in only_1_IDs: #loop in reverse
                if trade["long"] ==1 and trade["open"] ==1:
                    shares = trade["shares"]
                    total_shares.append(shares)
                    # print(f'ID: {trade["ID"]} tp: {trade["tp_price"]}')
        return sum(total_shares)

    def create_shares_to_open_row(self):
        shares_to_open = {"date":datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), "longs_to_buy":self.get_longs_to_buy(),"shorts_to_buy":self.get_shorts_to_buy()}
        return shares_to_open

    def print_shit(self,close=0):
        pass
        # print("were live")
        
    def is_file_empty_3(self,file_name):
    #""" Check if file is empty by reading first character in it"""
    # open ile in read mode
        with open(file_name, 'r') as read_obj:
            # read first character
            one_char = read_obj.read(1)
            # if not fetched then file is empty
            if not one_char:
                return True
            else:
                return False

    def write_list_to_file(self,name,trade_execution):
        # places = ['Berlin', 'Cape Town', 'Sydney', 'Moscow']

        FILE = open(f'{name}',"a")
        
        FILE.writelines('%s\n' % trade_execution)
        FILE.close()

    def write_finanicials_to_file(self,name,data):
        # places = ['Berlin', 'Cape Town', 'Sydney', 'Moscow']

        FILE = open(f'{name}',"a")
        
        FILE.writelines('%s\n' % data)
        FILE.close()

    def read_list_from_file(self,name):
        name =name

        
        if self.is_file_empty_3(name) == False:

            FILE = open(name, 'r')
            temp_array = []
            
            for line in FILE:
                # remove linebreak which is the last character of the string
                item = line[:-1]

                #add item to the list
                temp_array.append(item)
            
            temp_array = [eval(item) for item in temp_array]
            self.trades_updated = temp_array
            temp_array = []

            
            FILE.close()
            return self.trades_updated

    def on_open(self,ws):
        print(' open sesame')
        

    def on_close(self,ws):
        print('closed connection')


    def on_message(self,ws,message):
        
        try:    

            json_message = json.loads(message)
            candle = json_message['k']
            is_candle_closed = candle['x']
            close = float(candle['c'])
            tick_price = float(candle['c'])

            ##RT
            
            # print(self.CANDLES[-10:-1])
            # print(f'How much Doge can I buy {self.get_USDT_balance("USDT")/close}')

            # full_value = self.get_USDT_balance("USDT") * close + self.get_USDT_balance("USDT") 
            # print(f'{full_value} is about FULL VALUE ')
            # print(f'half of full value in doge {(full_value/2)/self.get_USDT_balance("DOGE") }')


            ###BAR CLOSSES
            if is_candle_closed:
                self.barCount +=1
                #record data
                if self.barCount >= 0:
                    self.CANDLES.append({"date": milsToDateTime(json_message['E']), "close":float(candle['c']),"open":float(candle['o']),"high":float(candle['h']),"low":float(candle['l']),"volume":float(candle["v"]),"EMA1":0})
                    self.closes.append(float(close))

                    #add EMA1
                    EMA1 = indicators.EMA("EMA3",self.closes,history.EMA1_WINDOW)
                
                    if EMA1 > 0:
                        self.CANDLES[-1]["EMA1"] = EMA1
                    # print("Updated BAR CANDLES and closes")
                    print(f'date: {self.CANDLES[-1]["date"]} close: {self.CANDLES[-1]["close"]} EMA1: {self.CANDLES[-1]["EMA1"]}')


                #run MANAGER
                self.update(self.CANDLES[-1]["close"])

                #hedge_long
                hedge_long = Hedge()
                hedge_long.MIN_SHARES = self.MIN_SHARES
                hedge_long.tp = self.tp
                hedge_long.hedge_strat(self.CANDLES[-1]["close"],self.CANDLES[-1]["EMA1"])
                #hedge_short
                hedge_short = Hedge_Short()
                hedge_short.MIN_SHARES = self.MIN_SHARES
                hedge_short.tp = self.tp
                hedge_short.hedge_strat_short(self.CANDLES[-1]["close"],self.CANDLES[-1]["EMA1"])

                self.balances(self.CANDLES[-1]["close"])

                print("open long shares",self.get_open_long_shares())
                print("open short shares",self.get_open_short_shares())
       


            
                # time.sleep(2)
                
                

        except Exception as e:
            print("THERE IS AN ERROR",e)

    def bot_thread(self):
        self.CANDLES = self.CANDLES_from_history()
        print("created CANDLES From history")

        #ints
        history = History()
        indicators = Indicators()
        

        


        #START
        ws = websocket.WebSocketApp(self.SOCKET, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message)

        ws.run_forever()
    def start_bot_on_thread(self):
        x = threading.Thread(target=self.bot_thread)
        x.start()

    def CANDLES_from_history(self):
        history = History()
        indicators = Indicators()
        history.set_CANDLES()
        #add Props
        history.closes = []
        history.EMA1_WINDOW = 3

        #locals
        CANDLES = history.get_CANDLES()
        closes = history.closes

        #append history.closes

        for i in range(len(CANDLES)):
            closes.append(CANDLES[i]["close"])
            
            EMA1 = indicators.EMA("EMA3",closes,history.EMA1_WINDOW)
            CANDLES[i]["EMA1"] = EMA1
        
        
        CANDLES.pop(-1)
        closes.pop(-1)
        print("popping out bad bar success!")
        
        self.closes = closes

        return CANDLES






    #instet EMA
    # history.insert_col_n_rows("EMA1",EMA1)


# for candle in CANDLES:
#     print(candle["date"],candle["EMA1"])

#THE MANAGER

manager = Manager()

manager.start_bot_on_thread()

# longs = Longs()
# longs.CANDLES = CANDLES_from_history()
# longs.start_bot_on_thread()



