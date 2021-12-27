import json
from binance_interface import binanceInterface
from datetime import datetime
import pandas as pd
import time
import math

file = open('API_CREDENTIALS.json',)
API_CREDENTIALS = json.load(file)

api_key = API_CREDENTIALS['api_key']
api_secret = API_CREDENTIALS['api_secret']

lista_ativos = ["ADAUSDT", "SOLUSDT", "ETHUSDT", "LUNAUSDT", "FTMUSDT", "DOGEUSDT", "SHIBUSDT"]

binance = binanceInterface(api_key, api_secret)

print(binance.get_last_ticker_perc_low("VETUSDT"))

# order = binance.client.create_test_order(
#     symbol='ADAUSDT',
#     side='BUY',
#     type='MARKET',
#     quantity=25)

# USDT = binance.get_available_USDT()
# print(USDT)
# print(binance.get_ativo_price("ADAUSDT"))

# print(order)


# perc_each_buy = [0.5, 0.25, 0.25]
# ativo = "ADAUSDT"

# available_USDT = binance.get_available_USDT() - 5 # 5 é a margem de segurança
# percent_to_be_used = perc_each_buy[0]
# ammount_to_be_used = available_USDT * percent_to_be_used
# ammount_to_buy = ammount_to_be_used / binance.get_ativo_price(ativo)
# ammount_to_buy = math.floor(ammount_to_buy * 100)/100.0
# perc_each_buy = perc_each_buy[1:]
# perc_each_buy = [item/(1-percent_to_be_used) for item in perc_each_buy]

# print(ammount_to_buy)
# print(perc_each_buy)