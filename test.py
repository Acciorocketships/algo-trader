from Algo import Algo
from Manager import Manager
from AlpacaData import AlpacaData
import ta
import datetime

class MACDstrategy(Algo):

	def init(self):
		self.set_schedule(["31 9 * * *"])

	def run(self):
		hist = self.get_data("SPY", days=20)
		day_prices = hist.at_time(datetime.time(9,30))
		macd = ta.trend.macd_diff(day_prices, window_slow=10, window_fast=5, window_sign=3)[-1]
		if macd > 0:
			self.order_target_percent("SPY", 1.0)
		else:
			self.order_target_percent("SPY", 0.0)

if __name__ == '__main__':
	data = AlpacaData(start=datetime.datetime(2017,11,20), end=datetime.datetime(2018,3,15), timeframe='minute', symbols=["SPY"], live=False)
	manager = Manager(data)
	algo = MACDstrategy()
	manager.add_algo(algo)
	manager.backtest(start=datetime.datetime(2018,1,1), end=datetime.datetime(2018,3,15))