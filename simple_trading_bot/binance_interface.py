from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance import AsyncClient, DepthCacheManager, BinanceSocketManager
import time
import pandas as pd
from tabulate import tabulate

class binanceInterface:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.init_client()
        self.watchlist = ["ADAUSDT", "ETHUSDT", "SOLUSDT", "FTMUSDT", "VETUSDT"]
        self.__refresh_server_time()
        
    def init_client(self):
        try:
            self.client = Client(self.api_key, self.api_secret)
        except:
            time.sleep(60)
            self.client = Client(self.api_key, self.api_secret)

    def get_balance(self):
        account = self.client.get_account()
        list_balance = [item for item in account['balances'] if item['locked'] > '0.00000000' or item['free'] > '0.00000000']
        account['balances'] = list_balance

        for i in range(len(list_balance)):
            to_print = "{} - {}: (free: {}) - (locked: {})".format(i+1, list_balance[i]['asset'], list_balance[i]['free'], list_balance[i]['locked'])
            print(to_print)

    def get_available_USDT(self):
        account = self.client.get_account()
        account_usdt = [item for item in account["balances"] if item['asset'] == "USDT"][0]
        return float(account_usdt['free'])

    def get_ativo_price(self, ativo):
        response = self.client.get_symbol_ticker(symbol=ativo)
        return float(response['price'])

    def get_all_prices(self, lista=[]):
        dict_all_prices = self.client.get_all_tickers() 
        counter = 1
        dict_prices = {}
        for item in dict_all_prices:
            if item['symbol'] in lista:
                print("{}. {} - {}".format(counter, item['symbol'], item['price']))
                counter += 1

    def add_to_watchlist(self, lista=[]):
        self.watchlist += [item for item in lista if item not in self.watchlist]

    def get_last_ticker_perc_low(self, ativo):

        last_candle = self.client.get_historical_klines(ativo, AsyncClient.KLINE_INTERVAL_1DAY, "1 day ago UTC")[0]
        if last_candle[4] < last_candle[1]:
            low_perc_diff = (abs(float(last_candle[1]) - float(last_candle[4])) / float(last_candle[1])) * 100
        else:
            low_perc_diff = 0

        return low_perc_diff
        

        # print(last_candle)
        # print("Time diff: {}".format(self.server_time - last_candle[0]))
        # print("Price diff: {}".format(float(last_candle[4]) - float(last_candle[1])))
        # perc_diff = ((float(last_candle[4]) / float(last_candle[1])) - 1) * 100
        # print("Price perc diff: {:.2f}%".format(perc_diff))
        '''
        [
            [
                1499040000000,      // Open time
                "0.01634790",       // Open
                "0.80000000",       // High
                "0.01575800",       // Low
                "0.01577100",       // Close
                "148976.11427815",  // Volume
                1499644799999,      // Close time
                "2434.19055334",    // Quote asset volume
                308,                // Number of trades
                "1756.87402397",    // Taker buy base asset volume
                "28.46694368",      // Taker buy quote asset volume
                "17928899.62484339" // Ignore.
            ]
            ]
        '''
        
    def __refresh_server_time(self):
        self.server_time = int(self.client.get_server_time()["serverTime"])


    def get_last_n_tickers(self, ativo, days=1):
        self.__refresh_server_time()

        if days == 1:
            days_str = "1 day ago UTC"
        else:
            days_str = "{} days ago UTC".format(days)

        candles = self.client.get_historical_klines(ativo, AsyncClient.KLINE_INTERVAL_1DAY, days_str)

        data = {"ativo": [],
                "open_time": [],
                "open_price": [],
                "high_price": [],
                "low_price": [],
                "close_price":[],
                "volume": [],
                "close_time": [],
                "quote_asset_volume": [],
                "number_of_trades": [],
                "taker_buy_base_asset_volume": [],
                "taker_buy_quote_asset_volume": [],
                "ignore": []}

        for candle in candles:
            data["ativo"] += [ativo]
            data["open_time"] += [candle[0]]
            data["open_price"] += [float(candle[1])]
            data["high_price"] += [float(candle[2])]
            data["low_price"] += [float(candle[3])]
            data["close_price"] += [float(candle[4])]    
            data["volume"] += [float(candle[5])]
            data["close_time"] += [float(candle[6])]
            data["quote_asset_volume"] += [float(candle[7])]
            data["number_of_trades"] += [candle[8]]
            data["taker_buy_base_asset_volume"] += [float(candle[9])]
            data["taker_buy_quote_asset_volume"] += [float(candle[10])]
            data["ignore"] += [float(candle[11])]

        df = pd.DataFrame.from_dict(data)
        df['bearish'] = (df['open_price'] > df['close_price'])
        df['max_loss_diaria'] = (abs(df['open_price'] - df['low_price']) / df['open_price']) * 100
        df['percentual_recuperado'] = (abs(df['close_price'] - df['low_price']) / df['open_price']) * 100
        df['loss'] = ((df['open_price'] - df['close_price']) / df['open_price']) * 100

        df = df[df['bearish']]
        df = df[df['max_loss_diaria'] > df['max_loss_diaria'].quantile(.95)]

        print(tabulate(df[['ativo', 'open_price', 'low_price', 'close_price', 'bearish', 'loss', 'max_loss_diaria', 'percentual_recuperado']], headers = 'keys', tablefmt = 'psql'))


    def get_buy_threshold(self, ativo, days=1, percent_days_considerable_return=0.7, considerable_return_threshold=5):
        self.__refresh_server_time()

        if days == 1:
            days_str = "1 day ago UTC"
        else:
            days_str = "{} days ago UTC".format(days)

        candles = self.client.get_historical_klines(ativo, AsyncClient.KLINE_INTERVAL_1DAY, days_str)

        data = {"ativo": [],
                "open_time": [],
                "open_price": [],
                "high_price": [],
                "low_price": [],
                "close_price":[],
                "volume": [],
                "close_time": [],
                "quote_asset_volume": [],
                "number_of_trades": [],
                "taker_buy_base_asset_volume": [],
                "taker_buy_quote_asset_volume": [],
                "ignore": []}
                
        for candle in candles[:-1]:
            data["ativo"] += [ativo]
            data["open_time"] += [candle[0]]
            data["open_price"] += [float(candle[1])]
            data["high_price"] += [float(candle[2])]
            data["low_price"] += [float(candle[3])]
            data["close_price"] += [float(candle[4])]    
            data["volume"] += [float(candle[5])]
            data["close_time"] += [float(candle[6])]
            data["quote_asset_volume"] += [float(candle[7])]
            data["number_of_trades"] += [candle[8]]
            data["taker_buy_base_asset_volume"] += [float(candle[9])]
            data["taker_buy_quote_asset_volume"] += [float(candle[10])]
            data["ignore"] += [float(candle[11])]

        df = pd.DataFrame.from_dict(data)
        df['bearish'] = (df['open_price'] > df['close_price'])
        df['max_loss_diaria'] = (abs(df['open_price'] - df['low_price']) / df['open_price']) * 100
        df['percentual_recuperado'] = (abs(df['close_price'] - df['low_price']) / df['open_price']) * 100
        df['loss'] = ((df['open_price'] - df['close_price']) / df['open_price']) * 100

        df = df[df['bearish']]
        df = df[df['max_loss_diaria'] > df['max_loss_diaria'].quantile(.95)]

        print(tabulate(df[['ativo', 'open_price', 'low_price', 'close_price', 'bearish', 'loss', 'max_loss_diaria', 'percentual_recuperado']], headers = 'keys', tablefmt = 'psql'))

        lowest = min(df['max_loss_diaria'].tolist())
        highest = max(df['max_loss_diaria'].tolist())

        list_percents = df['percentual_recuperado'].tolist()
        list_interesting_percents = [item for item in list_percents if item > considerable_return_threshold]
        should_trade_this_one = ((len(list_interesting_percents) / len(list_percents)) > percent_days_considerable_return)

        return lowest, highest, should_trade_this_one
        

    def send_buy_order(ativo, qtde, comission=0.001):

        buy_order_market = client.create_order(symbol=ativo,
                                                side='BUY',
                                                type='MARKET',
                                                quantity=qtde)


        return buy_order_market

        #f = open("OpAberta.txt", "w")
        #f.write(str(buy_order_market))
        #f.close()

    def send_sell_order(ativo, qtde, comission=0.001):

        sell_order_market = client.create_order(symbol=ativo,
                                                side='SELL',
                                                type='MARKET',
                                                quantity=qtde)

        return sell_order_market



