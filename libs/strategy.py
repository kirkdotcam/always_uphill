from libs.connection import api as k
import libs.arima as arima
import libs.prices as prices
import libs.signals as signals
import libs.actions as actions
import libs.logs as logs
from datetime import datetime
import time
import networkx as nx
import pandas as pd
import warnings

class Strategy():
    def __init__(self, 
    position=None,
    size=100, 
    log=logs.Log(),
    prediction_horizon=60,
    horizon_growth = 1,
    cycle_time=0):
        try:
            self.pairs = k.query_public("AssetPairs")["result"]
        except:
            raise Exception("couldn't grab pairs")
        
        self.position = position
        if position is None:
            self.position = "ZUSD"

        self.G = nx.Graph()
        self.size = size
        edges = [(pair["base"],pair["quote"]) for pair in self.pairs.values()]
        self.G.add_edges_from(edges)
        self.log = log
        self.cycle = 0
        self.cycle_time = cycle_time
        self._horizon = prediction_horizon #static value to reset to
        self.horizon = self._horizon
        
        self.horizon_growth = horizon_growth if horizon_growth <=60 else 60
        
        
        

    # scan for neighbors
    def neighborScan(self, position=None, graph=None):

        if position is None:
            position = self.position
        if graph is None:
            graph = self.G
        
        neighpair = [pair for pair in self.pairs if position in pair]
        
        return [pair for pair in neighpair if ".d" not in pair]

    # model all neighbors
    def build_models(self, prices_list):
        models = []
        modelnum = 0
        self.cycle += 1
        
        for price in prices_list:

            modelnum += 1
            start = datetime.now()
            models.append(arima.make_model(price))
            end = datetime.now()

            train_time = (end-start).total_seconds()
            train_msg = f"⚡ model {modelnum} took {train_time} seconds"
            self.log.log_model(self.cycle,modelnum,train_time)
            print(train_msg)
        return models

        # return [arima.make_model(price) for price in prices_list]

    def get_forecasts(self, model_list):
        """
            Returns:
                dict(pair_id, forecast_value)
        """
        return {model[0]: arima.make_forecast(model[1], self.horizon) for model in model_list}
        
    # if short sma higher, flag positive
    # if predicted higher, flag positive

    def signal_compile(self, ohlcs, forecast):
        lastpri = signals.get_last_prices(ohlcs)

        lastpri["prediction"] = lastpri.pair.apply(lambda x: forecast[x])

        def invert_base(row):
            """ to compare apples to apples, 
            currency of interest must be the quote
            instead of the base in the pair
            """
            if row["prediction"] == 0:
                return row

            if self.pairs[row.pair]["base"] != self.position:
                row["last_price"] **= -1
                row["prediction"] **= -1
            return row
        
        lastpri = lastpri.apply(invert_base, axis="columns", result_type="broadcast")
        signals.generate_ewma_cross_sig(ohlcs, lastpri)
        signals.generate_prediction_sig(lastpri)

        lastpri["sigsum"] = lastpri.sma_sig + lastpri.pred_signal
        lastpri.to_csv("./last_prices.csv")
        return lastpri[["pair","sigsum","pred_return"]]

    

    # if both positive, ready to trade
    # if multiple ready to trade, take highest projected return
    # else, wait 10 mins and try again
    def trade_decision(self, signals_df, forecasts):

        entry = signals_df[signals_df["sigsum"] == 2]
        
        if entry.shape[0] == 0:
            return "HOLD"

        
        high = entry.sort_values("pred_return").iloc[0]
        # check if trade is larger than fees (use static fee val for now)
        if high.pred_return < 0.26:
            print(f"waiting on {high.pair} with predicted value of {high.pred_return} in {self.horizon} minutes")
            self.horizon += self.horizon_growth
            print(f"increasing horizon by {self.horizon_growth} minutes")
            self.log.log_decision("HOLD",high.pair,high.pred_return, self.horizon)
            return "HOLD"
        else:
            print(f"buying {high.pair} with predicted value of {high.pred_return} in {self.horizon} minutes")
            self.log.log_decision("TRADE",high.pair,high.pred_return, self.horizon)
            return high.pair
 

    def trade_action(self, decision="HOLD"):
        if decision == "HOLD":
            return (self.size, self.position)
        else:

            response = actions.trade(decision, self.size)

            mult = float(response["result"][decision]["c"][0])
            
            pairdatum = self.pairs[decision]
            if pairdatum["base"]==self.position:
                self.position = pairdatum["quote"]
            else:
                self.position = pairdatum["base"]
                mult **= -1

            self.size = mult * self.size

            self.horizon = self._horizon #reset back to base value
            return (self.size, self.position)
            

    def execute(self):
        print("starting execution cycle")
        neighbors = self.neighborScan()

        ohlcs = prices.get_prices(neighbors, logger)

        print(f"building {len(ohlcs)} models")
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            models=self.build_models(ohlcs.values())
        
        model_list = zip(neighbors,models)
        forecasts = self.get_forecasts(model_list)

        sig_df = self.signal_compile(ohlcs,forecasts)

        decision = self.trade_decision(sig_df, forecasts)

        result = self.trade_action(decision)

        self.log.log_trade(decision, result[1], result[0])

        return {
            "lasttrade":decision,
            "newposition":result[1],
            "newsize":result[0]
        }
        

