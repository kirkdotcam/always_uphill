from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import arma_order_select_ic


def find_order(data):

    result = arma_order_select_ic(data["close"]).bic_min_order
    return (result[0],1,result[1])

def make_model(data, order=None):
    
    if order is None:
        order=find_order(data)
    model = ARIMA(data["close"], order=order)
    fitmodel = model.fit()
    return fitmodel

def make_forecast(model, steps=60):
    return model.forecast(steps=steps)[-1]

