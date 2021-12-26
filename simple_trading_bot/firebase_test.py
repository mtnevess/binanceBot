
from time import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd

cred = credentials.Certificate("./snow-integrated-labs-firebase-credentials.json")
databaseURL = "https://snow-integrated-labs-default-rtdb.firebaseio.com/"
firebase_admin.initialize_app(cred, {
	'databaseURL':databaseURL
	})


script_fb_path = "/snow-ecosystem/binance_price_anomaly"

ammount_each_buy = db.reference("{}/ammount_each_buy/".format(script_fb_path)).get()
print(ammount_each_buy)

lista_ativos = db.reference("{}/lista_ativos/".format(script_fb_path)).get()
print(lista_ativos)

running = db.reference("{}/running/".format(script_fb_path)).get()
print(running)

db.reference("{}/last_refresh_time/".format(script_fb_path)).set(str(pd.Timestamp.utcnow()))

should_refresh_params = db.reference("{}/should_refresh_params/".format(script_fb_path)).get()
print(should_refresh_params)

date = str(pd.Timestamp.utcnow())[0:11]
date2 = date + "20"
time_and_date = str(pd.Timestamp.utcnow())[0:13]
print(time_and_date < date2)