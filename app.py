from libs.strategy import Strategy
import time

strat = Strategy()


while True:
    result = strat.execute()
    with open("ledger.txt","a") as file:
        file.write(f"{result['lasttrade']},{result['newposition']},{result['newsize']}\n")
    # time.sleep(10)


