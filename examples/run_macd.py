from AlgoTrader.Algo import Algo
from AlgoTrader.Manager import Manager
from AlgoTrader.AlpacaData import AlpacaData
from macd import MACDstrategy

data = AlpacaData(start=30, timeframe='day', symbols=["SPY"], live=True)
manager = Manager(data)
algo = MACDstrategy()
manager.add_algo(algo)
manager.run()