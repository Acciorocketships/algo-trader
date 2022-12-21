from AlgoTrader.Algo import Algo
from AlgoTrader.Manager import Manager
from AlgoTrader.AlpacaData import AlpacaData
import ta
import datetime

class Strategy(Algo):

	def init(self):
		self.set_schedule({"second": 30, "minute": 30, "hour": "13", "day_of_week": "mon-fri"})

	def run(self):
		price = self.quote(symbol="SPY")
		print("running time: {time}, price: {price}".format(time=self.datetime, price=price))


def backtest():
	data = AlpacaData(start=60, symbols=["SPY"])
	manager = Manager(data)
	algo = Strategy()
	manager.add_algo(algo)
	manager.backtest(start=60)

if __name__ == '__main__':
	backtest()