from libs.connection import api as k
import libs.arima as arima
import libs.prices as prices
import libs.signals as signals
import libs.actions as actions
from datetime import datetime
import networkx as nx
import pandas as pd
import warnings

class Strategy():
    def __init__(self, position=None, size=100):
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
        
        

    # scan for neighbors
    def neighborScan(self, position=None, graph=None):

        if position is None:
            position = self.position
        if graph is None:
            graph = self.G
        
        neighbors = list(graph.neighbors(position))
        neighpair = [pair for pair in self.pairs if position in pair]
        
        return [pair for pair in neighpair if ".d" not in pair]

    # model all neighbors
    def build_models(self, prices_list):

        models = [arima.make_model(price) for price in prices_list]

        return models

    def get_forecasts(self, neighborpositions,models):
        forecasts = [arima.make_forecast(model) for model in models]

        return {pair:forecast for pair,forecast in zip(neighborpositions,forecasts)}    

        
    # if short sma higher, flag positive
    # if predicted higher, flag positive

    def signal_compile(self, ohlcs, forecast):
        lastpri = signals.get_last_prices(ohlcs)
        sma = signals.generate_sma_cross_sig(ohlcs)
        pred = signals.generate_prediction_sig(ohlcs, forecast)

        sigs = pd.concat([lastpri,sma,pred], axis="columns", join="inner")
        sigs["sigsum"] = sigs.sma_sig + sigs.pred_signal
        return sigs[["pair","sigsum","pred_return"]]

    

    # if both positive, ready to trade
    # if multiple ready to trade, take highest projected return
    # else, wait 10 mins and try again
    def trade_decision(self, signals_df):

        entry = signals_df[signals_df["sigsum"] == 2]
        
        if entry.shape[0] == 0:
            return "wait"

        
        high = entry.sort_values("pred_return").iloc[0]
        if high.pred_return < 0:
            return "wait"
        else:
            print(f"buying {high.pair}")
            return high.pair


        

    def trade_action(self, decision="wait"):
        if decision == "wait":
            return (self.size, self.position)
        else:
            self.log_trade(decision)
            response = actions.trade(decision, self.size)
            mult = response["result"][decision]["c"][0]
            self.size = float(mult) * self.size
            
            pairdatum = self.pairs[decision]
            if pairdatum["base"]==self.position:
                self.position = pairdatum["quote"]
            else:
                self.position = pairdatum["base"]

            return (self.size, self.position)
            

    def log_trade(self,pair):
        with open("./log.txt","a") as file:
            file.writelines(f"{pair},{datetime.now()}\n")

    def execute(self):
        print("starting execution cycle")
        neighbors = self.neighborScan()
        ohlcs = prices.get_prices(neighbors)
        models = None
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            models=self.build_models(ohlcs.values())

        forecast = self.get_forecasts(neighbors,models)

        sig_df = self.signal_compile(ohlcs,forecast)

        decision = self.trade_decision(sig_df)

        result = self.trade_action(decision)
        
        return {
            "lasttrade":decision,
            "newposition":result[1],
            "newsize":result[0]
        }
        

