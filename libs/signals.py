import pandas as pd

def make_neighbor_df(neighbors):
    df = pd.DataFrame(neighbors)
    df.columns = ["pair"]
    return df

def get_last_prices(prices_dict):
    last_prices = [(price[0],price[1].iloc[-1]["close"]) for price in prices_dict.items()]
    df = pd.DataFrame(last_prices)
    df.columns=["pair","last_price"]
    return df

def generate_prediction_sig(last_prices_df):
    df=last_prices_df
    df["pred_return"] = (df.prediction-df.last_price)/df.last_price
    df["pred_signal"] = (df.pred_return > 0).astype(int)
    return df[["prediction","pred_return","pred_signal"]]


def generate_ewma_cross_sig(prices_dict, last_prices_df, short=5, long=10):

    df = last_prices_df

    sig_dict = {}
    for pair,prices in prices_dict.items():
        prices["sma_short"] = prices.close.ewm(halflife=short).mean()
        prices["sma_long"] = prices.close.ewm(halflife=long).mean()
        prices["signal"] =(prices.sma_short > prices.sma_long).astype(int)
        sig_dict[pair] = prices.signal.iloc[-1]
    
    df["sma_sig"] = df.pair.apply(lambda x: sig_dict[x])
    return df["sma_sig"]

    

    

    

