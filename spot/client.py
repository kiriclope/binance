import os 
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
