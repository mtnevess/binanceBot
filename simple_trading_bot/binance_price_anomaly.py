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


# Settings
lista_ativos = ["ADAUSDT", "SOLUSDT", "ETHUSDT", "LUNAUSDT", "FTMUSDT", "AVAXUSDT", "HBARUSDT", "VETUSDT", "DOTUSDT"]
perc_each_buy_cte = [0.5, 0.25, 0.25]

binance = binanceInterface(api_key, api_secret)

def conduz_operacao(binance, position_size, ativo, buy_order, dict_precos_entrada, perc_each_buy):

    diff_entradas = dict_precos_entrada["end_buy_price"] - dict_precos_entrada["start_buy_price"] 
    second_buy = dict_precos_entrada["start_buy_price"] + diff_entradas/2
    third_buy = dict_precos_entrada["end_buy_price"]
    precos_compra = [second_buy, third_buy]

    while current_date == new_date:
        ## Checa se está em algum preço de compra
        if len(precos_compra) > 0:
            perc_queda = binance.get_last_ticker_perc_low(ativo)
            if perc_queda > precos_compra[0]:

                available_USDT = binance.get_available_USDT() - 5 # 5 é a margem de segurança
                percent_to_be_used = perc_each_buy[0]
                ammount_to_be_used = available_USDT * percent_to_be_used
                ammount_to_buy = ammount_to_be_used / binance.get_ativo_price(ativo)
                ammount_to_buy = math.floor(ammount_to_buy * 100)/100.0
                perc_each_buy = perc_each_buy[1:]
                perc_each_buy = [item/(1-percent_to_be_used) for item in perc_each_buy]

                try:
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)
                except:
                    time.sleep(15)
                    binance.init_client()
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)

                precos_compra = precos_compra[1:]
                position_size += ammount_to_buy * 0.9985

        time.sleep(15)
        new_date = str(pd.Timestamp.utcnow())[0:10]

    return position_size



running = True

while running:

    watchlist = []

    dict_buy_threshold = {}
    perc_each_buy = perc_each_buy_cte
    position_size = 0
    em_operacao = False
    ativo_operacao = ""

    for ativo in lista_ativos:
        lowest, highest, should_trade_this_one = binance.get_buy_threshold(ativo, days=365)
        if should_trade_this_one:
            dict_buy_threshold[ativo] = {}
            dict_buy_threshold[ativo]["start_buy_price"] = lowest
            dict_buy_threshold[ativo]["end_buy_price"] = highest
            watchlist += [ativo]

    current_date = str(pd.Timestamp.utcnow())[0:10]
    new_date = current_date

    while current_date == new_date:

        for ativo in watchlist:
            perc_queda = binance.get_last_ticker_perc_low(ativo)
            if (perc_queda > dict_buy_threshold[ativo]["start_buy_price"]) and not em_operacao:
                ### Todo: Entra na Operação
                available_USDT = binance.get_available_USDT() - 5 # 5 é a margem de segurança
                percent_to_be_used = perc_each_buy[0]
                ammount_to_be_used = available_USDT * percent_to_be_used
                ammount_to_buy = ammount_to_be_used / binance.get_ativo_price(ativo)
                ammount_to_buy = math.floor(ammount_to_buy * 100)/100.0
                perc_each_buy = perc_each_buy[1:]
                perc_each_buy = [item/(1-percent_to_be_used) for item in perc_each_buy]

                try:
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)
                except:
                    time.sleep(15)
                    binance.init_client()
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)
                
                position_size += ammount_to_buy * 0.9985
                em_operacao = True
                position_size = conduz_operacao(binance, position_size, ativo, buy_order, dict_buy_threshold[ativo], perc_each_buy)
                ativo_operacao = ativo
                

        time.sleep(15)
        new_date = str(pd.Timestamp.utcnow())[0:10]
        print(str(pd.Timestamp.utcnow()))



    # Todo: Se tiver com posição aberta, fechar.
    if em_operacao:
        position_size = math.floor(position_size * 100)/100.0
        try:
            sell_order = binance.send_sell_order(ativo_operacao, position_size)
        except:
            time.sleep(15)
            binance.init_client()
            sell_order = binance.send_sell_order(ativo_operacao, position_size)
    em_operacao = False
    
    binance.init_client()

