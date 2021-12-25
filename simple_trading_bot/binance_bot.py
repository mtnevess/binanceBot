import json
from binance_interface import binanceInterface

file = open('API_CREDENTIALS.json',)
API_CREDENTIALS = json.load(file)

api_key = API_CREDENTIALS['api_key']
api_secret = API_CREDENTIALS['api_secret']

binance = binanceInterface(api_key, api_secret)

binance.get_balance()
binance.get_all_prices(["ADAUSDT", "SOLUSDT", "FTMUSDT", "VETUSDT"])
binance.get_last_ticker()

binance.get_last_n_tickers("ETHUSDT", days=365)

