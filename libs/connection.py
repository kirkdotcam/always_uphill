import krakenex
import os

kkey = os.getenv("KRAKEN_KEY")
ksecret = os.getenv("KRAKEN_SECRET")

api = krakenex.API(kkey,ksecret)