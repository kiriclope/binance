import os 
import math
from binance.client import Client

def get_client():
    # use testnet to backtest
    # api_key = os.environ.get('testnet_api') 
    # api_secret = os.environ.get('testnet_secret') 
    
    # binance spot 
    api_key = os.environ.get('binance_api') 
    api_secret = os.environ.get('binance_secret') 
    
    # print(api_key)
    # print(api_secret)
    
    client = Client(api_key, api_secret)
    
    # for spot testnet 
    # client.API_URL = 'https://testnet.binance.vision/api'
    
    # for future testnet 
    # client.API_URL = 'https://testnet.binancefuture.com'
    
    client = Client(api_key, api_secret) 
    
    return client

def float_precision(f, n): 
    n = int(math.log10(1 / float(n)))
    f = math.floor(float(f) * 10 ** n) / 10 ** n
    f = "{:0.0{}f}".format(float(f), n)
    return str(int(f)) if int(n) == 0 else f

def convert(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
      
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def openCloseToBuySell(side, position):
    if side=='OPEN':
        if position=='LONG':
            side='BUY'
        else:
            side='SELL'
    else:
        if position=='LONG':
            side='SELL'
        else:
            side='BUY'
            
    return side 
