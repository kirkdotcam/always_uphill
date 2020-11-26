from libs.strategy import Strategy
import libs.logs as logs
import time

log_object = logs.Log()
strat = Strategy(log=log_object, prediction_horizon=10)
log_object.log_message("starting system")

while True:
    result = strat.execute()
    log_object.log_trade(result['lasttrade'],result['newposition'],result['newsize'])
    time.sleep(10)


