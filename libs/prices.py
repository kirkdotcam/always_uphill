import pandas as pd
import time
from libs.connection import api as k

def get_pair(pair, logger):
    params={
        "pair":pair,
    }

    call = "PENDING"
    tries = 0
    while call == "PENDING":
        try:
            ohlc = k.query_public("OHLC",params)
            call = "SUCCESS"
        except:
            if logger:
                logger.log_fault("NTWRK REQ", "Network request failed")

            if tries >= 3:
                print("too many network request errors, exiting program.")
                exit()

            print("network request failed, trying again")
            time.sleep(0.3)
            tries +=1

    df = pd.DataFrame(ohlc["result"][pair])
    df.columns = ["time","open","high","low","close","vwap","vol","count"]
    df.time=pd.to_datetime(df.time, unit="s")
    df.set_index("time", inplace=True)
    df = df.astype('float')
    return df

def get_prices(neighbor_ids, logger):
    """
        Returns:
            dict(neighbor_id:OHLCV)
    """
    prices =  [get_pair(pair, logger) for pair in neighbor_ids]

    return dict(zip(neighbor_ids,prices))
