import pandas as pd
from libs.connection import api as k

def get_pair(pair):
    params={
        "pair":pair,
    }
    ohlc = k.query_public("OHLC",params)
    df = pd.DataFrame(ohlc["result"][pair])
    df.columns = ["time","open","high","low","close","vwap","vol","count"]
    df.time=pd.to_datetime(df.time, unit="s")
    df.set_index("time", inplace=True)
    df = df.astype('float')
    return df

def get_prices(neighbor_ids):
    """
        Returns:
            dict(neighbor_id:OHLCV)
    """
    prices =  [get_pair(pair) for pair in neighbor_ids]

    return dict(zip(neighbor_ids,prices))
