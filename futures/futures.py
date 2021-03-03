#!/usr/bin/env python3

import math
import time
from datetime import datetime
import numpy 
import click
from client import *

from binance.exceptions import BinanceAPIException, BinanceOrderException

client = get_client()
@click.group() 
def cli():
    pass

@cli.command()
def account_balance(): 
    balance = client.futures_account_balance()
    for i in range( len(balance) ):
        if  float(balance[i]['balance'])!=0.0:
            print( balance[i]['asset'], 'balance', balance[i]['balance'], 'available', balance[i]['withdrawAvailable'] ) 

@cli.command()
def account_info():
    balance = client.futures_account_balance() 
    print( balance[0]['asset'], 'balance', balance[0]['balance'], 'available', balance[0]['withdrawAvailable'] )     
    base_balance = balance[0]['withdrawAvailable']
    
    account = client.futures_account()
    positions = account['positions']
    for i in range(len(positions)):
        if float(positions[i]['entryPrice'])>0 :
            print(positions[i]['symbol'], positions[i]['leverage'] + 'x,',
                  positions[i]['positionSide'] + ',',
                  'quantity:', positions[i]['positionAmt'] +',', 
                  'entry price:', positions[i]['entryPrice'] + ',',
                  'unrealized PNL:', positions[i]['unrealizedProfit'] + ',',
                  'maint margin:', positions[i]['maintMargin'] )
            
    
@cli.command()
@click.argument('dualSidePosition') 
@click.argument('symbol') 
def account_transfer():
    client.futures_account_transfer(dualSidePosition=dualSidePosition, symbol=symbol)

@cli.command()
def change_leverage():
    client.futures_change_leverage() 

@cli.command()
@click.argument('symbol') 
def account_trades(symbol):
    client.futures_account_trades(symbol=symbol) 

@cli.command()
def all_orders():
    orders = client.futures_get_all_orders()
    for i in range(len(orders)):
        if orders[i]['status']=='NEW':
            print(orders[i]['symbol'], orders[i]['positionSide'],
                  orders[i]['type'], orders[i]['side'],
                  'price', orders[i]['price'],
                  'quantity', orders[i]['origQty']) 
    
@cli.command()
@click.argument('symbol') 
def open_order(symbol):
    print('open orders')
    orders = client.futures_get_open_orders(symbol=symbol)
    for i in range(len(orders)):
        print(orders[i]['symbol'], orders[i]['positionSide'], orders[i]['type'], orders[i]['side'], orders[i]['price'], orders[i]['origQty']) 

    
@cli.command()
def cancel_all():
    print('cancel_all_open_orders')
    client.futures_cancel_all_open_orders() 

@cli.command()
@click.argument('side') 
@click.argument('position') 
@click.argument('order_type') 
@click.argument('symbol') 
@click.option('--test','-t', default=False, is_flag=True) 
@click.option('--percentage', '-p', default=1, type=float) 
@click.option('--mark_per', '-m', default=0.001, type=float) 
@click.option('--stop_per', '-s', default=0.005, type=float) 
@click.option('--target_per', '-x', default=0.025, type=float) 
@click.option('--target_qty_per', '-q', default=1, type=float) 
@click.option('--leverage', '-l', type=int) 

def make_order(side, position, order_type, symbol, leverage, test, percentage, mark_per, stop_per, target_per, target_qty_per):     
    balance = client.futures_account_balance() 
    print( balance[0]['asset'], 'balance', balance[0]['balance'], 'available', balance[0]['withdrawAvailable'] )     
    base_balance = balance[0]['withdrawAvailable']
    
    account = client.futures_account()
    positions = account['positions']
    for i in range(len(positions)):
        if positions[i]['symbol']==symbol and positions[i]['positionSide'] == position and positions[i]['positionAmt']:
            print(positions[i]['symbol'], positions[i]['leverage'] + 'x,',
                  positions[i]['positionSide'] + ',',
                  'quantity:', positions[i]['positionAmt'] +',', 
                  'entry price:', positions[i]['entryPrice'] + ',',
                  'unrealized PNL:', positions[i]['unrealizedProfit'] + ',',
                  'maint margin:', positions[i]['maintMargin'] )
            
            asset_quantity = positions[i]['positionAmt']
            
    mark_info = client.futures_mark_price(symbol=symbol) 
    mark_price = float(mark_info['markPrice'])
    
    position_info = client.futures_position_information(symbol=symbol)
    if position =='LONG':
        print('margin type:', position_info[0]['marginType']+',',
              'leverage:', position_info[0]['leverage']+',',
              'liquidationPrice', position_info[0]['liquidationPrice'])
        leverage = float( position_info[0]['leverage'] )
        
    elif position=='SHORT':
        print('margin type:', position_info[1]['marginType']+',',
              'leverage:', position_info[1]['leverage']+',',
              'liquidationPrice', position_info[1]['liquidationPrice'])
        leverage = float( position_info[1]['leverage'] )
        
    else:
        print('margin type:', position_info['marginType']+',',
              'leverage:', position_info['leverage']+',',
              'liquidationPrice', position_info['liquidationPrice'])
        leverage = float( position_info['leverage'] )
        
    exchange_info = client.futures_exchange_info()["symbols"] 
    sym_info = list(filter(lambda dum: dum['symbol'] == symbol, exchange_info))[0] 
    filters = sym_info['filters'] 
    
    tick_size = float( list(filter(lambda dum: dum['filterType'] == 'PRICE_FILTER', filters))[0]['tickSize'] )
    step_size = float( list(filter(lambda dum: dum['filterType'] == 'LOT_SIZE', filters))[0]['stepSize'] )
        
    print(symbol, 'mark price:', float_precision(float(mark_info['markPrice']), tick_size) +',',
          'last funding rate:', str(round(float(mark_info['lastFundingRate'])*100,4))+'%,',
          'countdown', convert(int(mark_info['nextFundingTime'] )/1000 - time.time() ) )
        
    # price
    if position=='LONG':
        price = float( float(mark_price) *  (1 - mark_per ) ) 
    else: 
        price = float( float(mark_price) *  (1 + mark_per ) ) 
        
    price = float( float_precision(price, tick_size) ) 
        
    # quantity 
    if side=='OPEN': 
        quantity = float(base_balance) * float(percentage)/float(price)*0.9995 * leverage
            
    else: 
        quantity = float(asset_quantity) * float(percentage) * 0.9995
        
    quantity = float( float_precision(quantity, step_size) ) 
    
    if position=='SHORT': 
        stop_per = - stop_per 
        target_per = - target_per 
        
    # stops and targets 
    stopPrice = float(float_precision(price*(1-stop_per), tick_size)) 
    targetPrice = float(float_precision(price*(1+target_per), tick_size))
    targetQty =  float(float_precision(quantity*target_qty_per, step_size)) 
    
    cost = float_precision(price*quantity/leverage, tick_size) 
    loss = float_precision( (price-stopPrice)*quantity, tick_size) 
    profit = float_precision( (targetPrice-price)*targetQty, tick_size)
    
    # orders 
    try:
        if test:
            print('################################################') 
            print('TEST ORDER:', side, position, order_type, symbol, '%dx' % int(leverage) ) 
            print('################################################') 
            
            if order_type=='LIMIT':
                print('LIMIT', 'price', price, 'quantity', quantity, 'cost', cost)
                
            elif order_type=='MARKET':
                print('MARKET', 'price', price, 'quantity', quantity, 'cost', cost) 
                
            elif 'STOP_MARKET' in order_type : 
                print('STOP_MARKET', 'price', stopPrice, 'loss', loss)
                
            elif 'TAKE_PROFIT' in order_type: 
                print('TAKE_PROFIT', 'price', targetPrice, 'quantity', targetQty, 'profit', profit)
                
            elif order_type=='TPSL':
                print('LIMIT', 'price', price, 'quantity', quantity, 'cost', cost)
                print('STOP_MARKET', 'price', stopPrice, 'loss', loss)                
                print('TAKE_PROFIT', 'price', targetPrice, 'quantity', targetQty, 'profit', profit)
                
            elif order_type=='PUMP':
                
                entryPrice = float(client.futures_mark_price(symbol=symbol)['markPrice'])
                currentPrice = entryPrice 
                stopPrice = float(float_precision(currentPrice*(1-stop_per), tick_size)) 
                targetPrice = float(float_precision(currentPrice*(1+target_per), tick_size))
                
                print('MARKET', 'price', currentPrice, 'quantity', quantity, 'cost', cost) 
                
                if position=='LONG':
                    while currentPrice<targetPrice and currentPrice>stopPrice: 
                        currentPrice = float(client.futures_mark_price(symbol=symbol)['markPrice'])
                        
                        print('stop', stopPrice, 'price', currentPrice, 'target', targetPrice,
                              'PNL', round( (currentPrice-float(entryPrice)) * quantity, 2),
                              '(', round( (currentPrice/float(entryPrice)-1) * quantity, 2), '%)', end='\r') 
                    
                        if currentPrice>=targetPrice: 
                            stopPrice = float(float_precision(currentPrice*(1-stop_per), tick_size)) 
                            targetPrice = float(float_precision(currentPrice*(1+target_per), tick_size))
                            
                    print('') 
                    if currentPrice>=targetPrice : 
                        print('TAKE_PROFIT, PNL', round( (currentPrice-float(entryPrice)) * quantity, 2) ,
                              '(', round( (currentPrice/float(entryPrice)-1) * quantity, 2), '%)' ) 
                    else:
                        print('STOP_MARKET, PNL', round( (currentPrice-float(entryPrice)) * quantity, 2) ,
                              '(', round( (currentPrice/float(entryPrice)-1) * quantity, 2), '%)' ) 
                else:
                    while currentPrice>targetPrice and currentPrice<stopPrice: 
                        currentPrice = float(client.futures_mark_price(symbol=symbol)['markPrice'])
                        
                        print('stop', stopPrice, 'price', currentPrice, 'target', targetPrice,
                              'PNL', round( (currentPrice-float(entryPrice)) * quantity, 2),
                              '(', round( (currentPrice/float(entryPrice)-1)* quantity, 2), '%)', end='\r')                         
                    
                        if currentPrice<=targetPrice: 
                            stopPrice = float(float_precision(currentPrice*(1-stop_per), tick_size)) 
                            targetPrice = float(float_precision(currentPrice*(1+target_per), tick_size))
                            
                    print('') 
                    if currentPrice>=targetPrice : 
                        print('TAKE_PROFIT, PNL', round( (currentPrice-float(entryPrice))*quantity, 2) ,
                              '(', round( (currentPrice/float(entryPrice)-1) *quantity, 2), '%)' ) 
                    else:
                        print('STOP_MARKET, PNL', round( (currentPrice-float(entryPrice))*quantity, 2) ,
                              '(', round( (currentPrice/float(entryPrice)-1)*quantity, 2), '%)' )                 
        else:
            
            print('################################################') 
            print('LIVE ORDER:', side, position, order_type, symbol) 
            print('################################################')
            
            side = openCloseToBuySell(side, position) 
            
            if order_type=='LIMIT':
                print('LIMIT', 'price', price, 'quantity', quantity, 'cost', cost)
                
                client.futures_create_order(symbol=symbol,side=side, positionSide=position,
                                            type='LIMIT', timeInForce='GTC', priceProtect=True,
                                            price=price, quantity=quantity)
            elif order_type=='MARKET':
                print('MARKET', 'price', price, 'quantity', quantity, 'cost', cost) 
                
                client.futures_create_order(symbol=symbol, side=side, positionSide=position,
                                            type='MARKET', quantity=quantity) 
                
            elif 'STOP_MARKET' in order_type : 
                side = openCloseToBuySell('CLOSE', position)
                
                print('STOP_MARKET', 'price', stopPrice, 'loss', loss)
                                                
                client.futures_create_order(symbol=symbol, side=side, positionSide=position,
                                            type='STOP_MARKET', stopPrice=stopPrice,
                                            priceProtect='True', workingType='MARK_PRICE', closePosition='TRUE') 
                
            elif 'TAKE_PROFIT' in order_type: 
                side = openCloseToBuySell('CLOSE', position)
                
                print('TAKE_PROFIT', 'price', targetPrice, 'quantity', targetQty, 'profit', profit)                
                
                client.futures_create_order(symbol=symbol,side='SELL', positionSide=position,
                                            type='LIMIT', timeInForce='GTC', price=targetPrice, quantity=targetQty) 
                
            elif order_type=='TPSL': 
                print('LIMIT', 'price', price, 'quantity', quantity, 'cost', cost)
                                
                order = client.futures_create_order(symbol=symbol,side=side, positionSide=position,
                                                    type='LIMIT', timeInForce='GTC', priceProtect=True,
                                                     price=price, quantity=quantity) 
                
                orderId = order['orderId']
                status = order['status']
                
                while status!='FILLED':
                    status = client.futures_get_order(symbol=symbol, orderId=orderId)['status'] 
                    
                if status=='FILLED': 
                    print('Order filled')
                    
                    side = openCloseToBuySell('CLOSE', position) 
                    
                    print('STOP_MARKET', 'price', stopPrice, 'loss', loss)
                    
                    client.futures_create_order(symbol=symbol, side=side, positionSide=position,
                                                type='STOP_MARKET', stopPrice=stopPrice,
                                                priceProtect='True', workingType='MARK_PRICE', closePosition='TRUE') 
                        
                    print('TAKE_PROFIT', 'price', targetPrice, 'quantity', targetQty, 'profit', profit) 
                    
                    client.futures_create_order(symbol=symbol,side=side, positionSide=position,
                                                type='LIMIT', timeInForce='GTC', price=targetPrice, quantity=targetQty) 
                        
            elif 'PUMP' in order_type:
                
                entryPrice = float(client.futures_mark_price(symbol=symbol)['markPrice'])
                currentPrice = entryPrice
                stopPrice = float(float_precision(currentPrice*(1-stop_per), tick_size)) 
                targetPrice = float(float_precision(currentPrice*(1+target_per), tick_size))
                
                print('MARKET', 'price', currentPrice, 'quantity', quantity, 'cost', cost) 
                
                client.futures_create_order(symbol=symbol, side=side, positionSide=position,
                                            type='MARKET', quantity=quantity)
                
                if position=='LONG':
                    while currentPrice<targetPrice and currentPrice>stopPrice: 
                        currentPrice = float(client.futures_mark_price(symbol=symbol)['markPrice'])
                        
                        print('stop', stopPrice, 'price', currentPrice, 'target', targetPrice,
                              'PNL', round( (currentPrice-float(entryPrice))*quantity, 2),
                              '(', round( (currentPrice/float(entryPrice)-1)*quantity, 2), '%)', end='\r')                         
                        
                        if currentPrice>=targetPrice: 
                            stopPrice = float(float_precision(currentPrice*(1-stop_per), tick_size)) 
                            targetPrice = float(float_precision(currentPrice*(1+target_per), tick_size)) 
                        
                    print('') 
                    side = openCloseToBuySell('CLOSE', position) 
                    
                    client.futures_create_order(symbol=symbol, side=side, positionSide=position,
                                                type='MARKET', quantity=quantity)  
                    
                    if currentPrice>=targetPrice : 
                        print('TAKE_PROFIT price', currentPrice,'percentage', round( (currentPrice/float(entryPrice)-1)*100, 2) ) 
                    else:
                        print('STOP_MARKET price', currentPrice, 'percentage', round( (currentPrice/float(entryPrice)-1) *100, 2) ) 
                        
                else:
                    while currentPrice>targetPrice and currentPrice<stopPrice: 
                        currentPrice = float(client.futures_mark_price(symbol=symbol)['markPrice'])
                        
                        print('stop', stopPrice, 'price', currentPrice, 'target', targetPrice,
                              'PNL', round( (currentPrice-float(entryPrice))*quantity, 2),
                              '(', round( (currentPrice/float(entryPrice)-1)*quantity, 2), '%)', end='\r')                         
                        
                        if currentPrice<=targetPrice: 
                            stopPrice = float(float_precision(currentPrice*(1-stop_per), tick_size)) 
                            targetPrice = float(float_precision(currentPrice*(1+target_per), tick_size)) 
                        
                    print('') 
                    side = openCloseToBuySell('CLOSE', position) 
                    
                    client.futures_create_order(symbol=symbol, side=side, positionSide=position,
                                                type='MARKET', quantity=quantity)                 
                                        
                    if currentPrice<=targetPrice : 
                        print('TAKE_PROFIT, PNL', round( (currentPrice-float(entryPrice))*quantity, 2) ,
                              '(', round( (currentPrice/float(entryPrice)-1)*quantity, 2), '%)' ) 
                    else:
                        print('STOP_MARKET, PNL', round( currentPrice-float(entryPrice), 2) ,
                              '(', round( (currentPrice/float(entryPrice)-1)*quantity, 2), '%)' ) 
                    
    except BinanceAPIException as error: 
        print(error) 
        
    except BinanceOrderException as error: 
        print(error) 

if __name__ == '__main__': 
    cli() 
