#! /usr/bin/python

import UserVariables
import cbpro
import pandas as pd
import scipy
import scipy.stats
import sys
import time

coin = UserVariables.coin
duration = UserVariables.duration
secret = UserVariables.secret
passphrase = UserVariables.passphrase
key = UserVariables.key
auth_client = cbpro.AuthenticatedClient(key, secret, passphrase)
public_client = cbpro.PublicClient()

def getData():
    historical = pd.DataFrame(public_client.get_product_historic_rates(coin))
    historical.columns=["Date", "Open", "High", "Low", "Close", "Volume"]
    historical.sort_values(by='Date', ascending=True, inplace=True)
    return historical

def act():
    data = getData()
    lr = scipy.stats.linregress(data["Date"].tolist(), data["Close"].tolist())
    global slope
    slope  = lr.slope
    global rSquared
    rSquared = lr.rvalue**2
    if slope > 0:
        return "buy"
    elif slope < 0:
        return "sell"
    else:
        return "hold"

def quant(action):
    if action == "buy":
	print("rSquared: " + str(rSquared))
	print("slope: " + str(slope))
	if rSquared*slope > 1:
	    print("buy: 1")
	    return 1
        else:
	    print("buy: " + str(rSquared*slope))
	    return rSquared*slope
    elif action == "sell":
	print("rSquared: " + str(rSquared))
	print("slope: " + str(slope))
	if rSquared*slope < -1:
	    print("sell: 1")
	    return 1
	else:
	    print("sell: " + str(-1 * rSquared * slope))
	    return -1 * rSquared * slope

def execute():
    action = act()
    accounts = auth_client.get_accounts()    
    cash_value = 0
    for i, dic in enumerate(accounts):
        if dic["currency"] == "USD":
            cash_value = dic["available"]
    if cash_value < UserVariables.minimum_threshold:
        sys.exit("Coinbase account too low on cash! only $" + str(cash_value) + " left in account")
    
    if action == "buy":
        quantity = float(quant("buy")) * float(cash_value)
        current = public_client.get_product_ticker(product_id=coin)["price"]
        if quantity > 0:
            auth_client.buy(price=current, size=quantity, order_type='limit', product_id=coin)
            print("bought " + str(quantity) + " " + coin + " at $" + str(current))
	else:
	    print("quantity to buy was " + str(quantity))
    elif action == "sell":
        coin_value = 0
        for i, dic in enumerate(accounts):
            if dic["currency"] == coin:
                coin_value = dic["available"]
        quantity = float(quant("sell")) * float(coin_value)
        current = public_client.get_product_ticker(product_id=coin)["price"]
        if quantity > 0:
            auth_client.sell(price=current, size=quantity, order_type='limit', product_id=coin)
            print("sold " + str(quantity) + " " + coin + " at $" + str(current))
	else:
	    print("quantity to sell was " + str(quantity))

def main():
    while True:
        execute()
        time.sleep(duration)

if __name__ == "__main__":
    main()
