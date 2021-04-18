from AlgoTrader.Algo import Algo
from AlgoTrader.Manager import Manager
from AlgoTrader.AlpacaData import AlpacaData
import ta
import datetime

class MACDstrategy(Algo):

	def init(self):
		self.set_schedule(["30 9 * * *"])

	def run(self):
		hist = self.get_data("SPY", days=20)
		if self.data.timeframe == 'minute':
			hist = hist.at_time(datetime.time(9,30))
		macd = ta.trend.macd_diff(hist, window_slow=10, window_fast=5, window_sign=3)[-1]
		if macd > 0:
			self.order_target_percent("SPY", 1.0, stop=-0.06)
		else:
			self.order_target_percent("SPY", 0.0)
			self.cancel_orders("SPY")

if __name__ == '__main__':
	data = AlpacaData(start=datetime.datetime(2017,11,1), end=datetime.datetime(2021,4,1), timeframe='day', symbols=["SPY"], live=False)
	manager = Manager(data)
	algo = MACDstrategy()
	manager.add_algo(algo)
	manager.backtest(start=datetime.datetime(2018,1,1), end=datetime.datetime(2021,4,1))