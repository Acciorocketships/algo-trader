from AlgoTrader.Algo import Algo
from AlgoTrader.Manager import Manager
from AlgoTrader.AlpacaData import AlpacaData
import ta
import datetime

class Strategy(Algo):

	def init(self):
		self.set_schedule({"second": 5, "minute": "*", "hour": "9-16", "day_of_week": "mon-fri"})

	def run(self):
		price = self.get_data(symbol="SPY", length=1)
		print("running time: {time}, price: {price}".format(time=self.datetime, price=price))


def backtest():
	data = AlpacaData(start=60, timeframe='day', symbols=["SPY"], live=False)
	manager = Manager(data)
	algo = Strategy()
	manager.add_algo(algo)
	manager.backtest(start=60)


def live():
	data = AlpacaData(start=1, timeframe='minute', symbols=["SPY"], live=True)
	manager = Manager(data)
	algo = Strategy()
	manager.add_algo(algo)
	manager.run(paper=True, log_schedule={"minute": "*"})

if __name__ == '__main__':
	backtest()