from libs.strategy import Strategy
import libs.logs as logs
import time

log_object = logs.Log()
strat = Strategy(log=log_object, prediction_horizon=8, horizon_growth=3)
log_object.log_message("starting system")

while True:
    result = strat.execute()
    time.sleep(strat.cycle_time)


