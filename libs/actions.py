from libs.connection import api as k

def trade(ticker,size):
    params = {"pair":ticker}
    response = k.query_public("Ticker",data=params)

    return response