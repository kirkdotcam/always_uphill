from datetime import datetime
from pathlib import Path

class Log():
    def __init__(self, file="./logs.txt"):
        self.filepath = Path(file)
        self.logfile = open(self.filepath,"a", 1)
        self.allowed_action = ["TRADE", "DECISION","MODEL", "GENERAL"]
        
    def message(self, action, contents):
        if action not in self.allowed_action:
            print(f"invalid log action {action}")
            return

        content = " ".join(str(item) for item in contents)
        self.logfile.writelines(f"{datetime.now()}   {action}  {content}\n")

    def log_trade(self, last_trade, new_position, new_size):
        self.message("TRADE", [last_trade, new_position, new_size])

    def log_decision(self,action,pair,pred_return, horizon):
        self.message("DECISION",[action,pair,pred_return, horizon])

    def log_model(self, cycle, model_num, train_time):
        self.message("MODEL",[cycle,model_num, train_time])

    def log_message(self,text):
        self.message("GENERAL", [text])
        

