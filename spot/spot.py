#!/usr/bin/env python3

import math 
import click
from client import get_client
from binance.exceptions import BinanceAPIException, BinanceOrderException 

client = get_client() 

@click.command() 
@click.argument('side') 
@click.argument('order_type') 
@click.argument('symbol') 
@click.option('--test','-t', default=False, is_flag=True) 
@click.option('--percentage', '-p', default=1, type=float) 
@click.option('--mrk_per', '-m', default=0, type=float) 

def make_order(side, order_type, symbol, test, percentage, mrk_per):
    
    if symbol.endswith('USDT'): 
        asset = symbol[:-4]
        base = 'USDT' 
    else: # BTC or BNB 
        asset = symbol[:-3]
        base = symbol[-3:]
        
    asset_balance = client.get_asset_balance(asset=asset) 
    base_balance = client.get_asset_balance(asset=base) 
    current_price = client.get_symbol_ticker(symbol=symbol)
    
    print(asset_balance)    
    print(base_balance) 
    print(current_price)
    
    price = float(current_price['price']) * ( 1 + float(mrk_per) ) 
        
    if side=='BUY':
        quantity = float(base_balance['free']) * float(percentage)/float(price)*0.9995
    else:
        quantity = float(asset_balance['free']) * float(percentage)*0.9995 
        
    filters = client.get_symbol_info(symbol)['filters']
    tick_size = float( list(filter(lambda dum: dum['filterType'] == 'PRICE_FILTER', filters))[0]['tickSize'] )
    step_size = float( list(filter(lambda dum: dum['filterType'] == 'LOT_SIZE', filters))[0]['stepSize'] )
    
    def float_precision(f, n): 
        n = int(math.log10(1 / float(n)))
        f = math.floor(float(f) * 10 ** n) / 10 ** n
        f = "{:0.0{}f}".format(float(f), n)
        return str(int(f)) if int(n) == 0 else f
    
    quantity = float( float_precision(quantity, step_size) ) 
    price = float_precision(price, tick_size) 
    
    try:
        if test: 
            print('test order:', side, order_type, 'symbol', symbol, 'price', price, 'quantity', quantity, 'cost', float(price)*quantity) 
            if order_type == 'MARKET': 
                client.create_test_order(symbol=symbol, side=side, type=order_type, quantity=quantity) 
                
            elif 'LIMIT' in order_type: 
                if 'STOP' in order_type: 
                    
                    if side=='BUY': 
                        stopPrice = float_precision( float(price)*0.9999, tick_size) 
                    else: 
                        stopPrice = float_precision( float(price)*1.0001, tick_size) 
                        
                    client.create_test_order(symbol=symbol, side=side, type='STOP_LOSS_LIMIT', timeInForce='GTC',
                                        stopPrice = stopPrice, price=price, quantity=quantity) 
                else: 
                    client.create_test_order(symbol=symbol, side=side, type='LIMIT', timeInForce='GTC',
                                             price=price , quantity=quantity)
                    
            elif 'PUMP' in order_type:
                client.create_test_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity)
                
                stop_price = float(price)*0.9999 
                current_price = float(client.get_symbol_ticker(symbol=symbol)['price']) 
                target_price = float(price)*1.0001 
                
                while current_price<target_price and current_price>=stop_price: 
                    current_price = float(client.get_symbol_ticker(symbol=symbol)['price']) 
                    print('stop', stop_price, 'price', current_price, 'target', target_price, end='\r') 
                    print('')
                    
                    if current_price>=target_price:
                        stop_price = target_price 
                        target_price = target_price*1.25 
                                        
                client.create_test_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity)
                
                if current_price>=target_price : 
                    print('take profit at', current_price,'percentage', round( (current_price/float(price)-1)*100, 2) ) 
                else:
                    print('stop loss at', current_price, 'percentage', round( (current_price/float(price)-1) *100, 2) ) 
                
        else: 
            print('live order:', side, order_type, 'symbol', symbol, 'price', price, 'quantity', quantity)
            
            if order_type == 'MARKET': 
                order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
                
            elif 'LIMIT' in order_type: 
                if 'STOP' in order_type: 
                    
                    if side=='BUY': 
                        stopPrice = float_precision( float(price)*0.95, tick_size) 
                    else: 
                        stopPrice = float_precision( float(price)*1.25, tick_size) 
                        
                    client.create_order(symbol=symbol, side=side, type='STOP_LOSS_LIMIT', timeInForce='GTC',
                                        stopPrice = stopPrice, price=price, quantity=quantity) 
                else:
                    client.create_order(symbol=symbol, side=side, type='LIMIT', timeInForce='GTC',
                                        price=price , quantity=quantity) 
                    
            elif 'PUMP' in order_type:
                client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity) 
                
                stop_price = float(price)*0.95 
                current_price = float(client.get_symbol_ticker(symbol=symbol)['price']) 
                target_price = float(price)*1.25 
                
                while current_price<target_price and current_price>=stop_price: 
                    current_price = float(client.get_symbol_ticker(symbol=symbol)['price']) 
                    print('stop', stop_price, 'price', current_price, 'target', target_price, end='\r') 
                    print('')
                    
                    if current_price>=target_price: 
                        stop_price = target_price 
                        target_price = target_price*1.05 
                        
                client.create_order(symbol=symbol, side='SELL', type='MARKET', quantity=quantity) 
                
                if current_price>=target_price : 
                    print('take profit at', current_price,'percentage', round( (current_price/float(price)-1)*100, 2) ) 
                else:
                    print('stop loss at', current_price, 'percentage', round( (current_price/float(price)-1) *100, 2) ) 
                    
    except BinanceAPIException as error:
        print(error) 
        
    except BinanceOrderException as error:
        print(error) 
        
if __name__ == '__main__':
    make_order() 
    
