import builtins
import json
from binance_interface import binanceInterface
from datetime import datetime
import pandas as pd
import time
import math
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

#Binance Config
file = open('API_CREDENTIALS.json',)
API_CREDENTIALS = json.load(file)

api_key = API_CREDENTIALS['api_key']
api_secret = API_CREDENTIALS['api_secret']

# Firebase Config
def init_firebase():
    cred = credentials.Certificate("./firebase-credentials.json")
    databaseURL = "https://snow-integrated-labs-default-rtdb.firebaseio.com/"
    firebase_admin.initialize_app(cred, {
        'databaseURL':databaseURL
        })

init_firebase()
script_fb_path = "/snow-ecosystem/binance_price_anomaly"

binance = binanceInterface(api_key, api_secret)

def conduz_operacao(binance, position_size, ativo, dict_precos_entrada, ammount_each_buy):

    script_fb_path = "/snow-ecosystem/binance_price_anomaly"
    diff_entradas = dict_precos_entrada["end_buy_price"] - dict_precos_entrada["start_buy_price"] 
    second_buy = dict_precos_entrada["start_buy_price"] + diff_entradas/2
    third_buy = dict_precos_entrada["end_buy_price"]
    precos_compra = [second_buy, third_buy]

    current_date = str(pd.Timestamp.utcnow())[0:10]
    new_date = current_date

    while current_date == new_date:
        ## Checa se está em algum preço de compra
        if len(precos_compra) > 0:
            perc_queda = binance.get_last_ticker_perc_low(ativo)
            if perc_queda > precos_compra[0]:

                ### Todo: Entra na Operação
                ammount_to_be_used = ammount_each_buy[0]
                ammount_to_buy = ammount_to_be_used / binance.get_ativo_price(ativo)
                ammount_to_buy = math.floor(ammount_to_buy * 100)/100.0
                ammount_each_buy = ammount_each_buy[1:]

                try:
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)
                except:
                    time.sleep(15)
                    binance.init_client()
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)

                try:
                    db.reference("{}/operacoes/".format(script_fb_path)).push().set(buy_order)
                except:
                    time.sleep(30)
                    init_firebase()
                    db.reference("{}/operacoes/".format(script_fb_path)).push().set(buy_order)

                precos_compra = precos_compra[1:]
                position_size += ammount_to_buy * 0.9985

        time.sleep(15)
        new_date = str(pd.Timestamp.utcnow())[0:10]
        try:
            db.reference("{}/last_refresh_time/".format(script_fb_path)).set(str(pd.Timestamp.utcnow()))
        except:
            time.sleep(30)
            init_firebase()
            db.reference("{}/last_refresh_time/".format(script_fb_path)).set(str(pd.Timestamp.utcnow()))


    return position_size



running = db.reference("{}/running/".format(script_fb_path)).get()

while running:

    # Firebase params
    try:
        lista_ativos = db.reference("{}/lista_ativos/".format(script_fb_path)).get()
        ammount_each_buy = db.reference("{}/ammount_each_buy/".format(script_fb_path)).get()
    except:
        time.sleep(30)
        init_firebase()
        lista_ativos = db.reference("{}/lista_ativos/".format(script_fb_path)).get()
        ammount_each_buy = db.reference("{}/ammount_each_buy/".format(script_fb_path)).get()
        
    should_refresh_params = False
    db.reference("{}/should_refresh_params/".format(script_fb_path)).set(should_refresh_params)

    # Strategy Variables
    watchlist = []
    dict_buy_threshold = {}
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

    try:
        db.reference("{}/pontos_de_entrada/".format(script_fb_path)).set(dict_buy_threshold)
    except:
        time.sleep(30)
        init_firebase()
        db.reference("{}/pontos_de_entrada/".format(script_fb_path)).set(dict_buy_threshold)

    current_date = str(pd.Timestamp.utcnow())[0:10]
    time_to_enter_threshold = current_date + " 20"
    new_date = current_date

    while (current_date == new_date) and (running) and (not should_refresh_params):

        current_time = str(pd.Timestamp.utcnow())

        for ativo in watchlist:
            perc_queda = binance.get_last_ticker_perc_low(ativo)
            if (perc_queda > dict_buy_threshold[ativo]["start_buy_price"]) and (not em_operacao) and (current_time < time_to_enter_threshold):
                ### Todo: Entra na Operação
                ammount_to_be_used = ammount_each_buy[0]
                ammount_to_buy = ammount_to_be_used / binance.get_ativo_price(ativo)
                ammount_to_buy = math.floor(ammount_to_buy * 100)/100.0
                ammount_each_buy = ammount_each_buy[1:]

                try:
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)
                except:
                    time.sleep(15)
                    binance.init_client()
                    buy_order = binance.send_buy_order(ativo, ammount_to_buy)
                
                try:
                    db.reference("{}/operacoes/".format(script_fb_path)).push().set(buy_order)
                except:
                    time.sleep(30)
                    init_firebase()
                    db.reference("{}/operacoes/".format(script_fb_path)).push().set(buy_order)
                
                position_size += ammount_to_buy * 0.9985
                em_operacao = True
                position_size = conduz_operacao(binance, position_size, ativo, dict_buy_threshold[ativo], ammount_each_buy)
                ativo_operacao = ativo
                

        time.sleep(15)
        new_date = str(pd.Timestamp.utcnow())[0:10]
        try:
            db.reference("{}/last_refresh_time/".format(script_fb_path)).set(str(pd.Timestamp.utcnow()))
            running = db.reference("{}/running/".format(script_fb_path)).get()
            should_refresh_params = db.reference("{}/should_refresh_params/".format(script_fb_path)).get()
        except:
            time.sleep(30)
            init_firebase()
            db.reference("{}/last_refresh_time/".format(script_fb_path)).set(str(pd.Timestamp.utcnow()))
            running = db.reference("{}/running/".format(script_fb_path)).get()
            should_refresh_params = db.reference("{}/should_refresh_params/".format(script_fb_path)).get()


    # Todo: Se tiver com posição aberta, fechar.
    if em_operacao:
        position_size = math.floor(position_size * 100)/100.0
        try:
            sell_order = binance.send_sell_order(ativo_operacao, position_size)
        except:
            time.sleep(15)
            binance.init_client()
            sell_order = binance.send_sell_order(ativo_operacao, position_size)

        try:
            db.reference("{}/operacoes/".format(script_fb_path)).push().set(sell_order)
        except:
            time.sleep(30)
            init_firebase()
            db.reference("{}/operacoes/".format(script_fb_path)).push().set(sell_order)

    em_operacao = False
    
    binance.init_client()


db.reference("{}/running/".format(script_fb_path)).set(True)