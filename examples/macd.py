from AlgoTrader.Algo import Algo
from AlgoTrader.Manager import Manager
from AlgoTrader.AlpacaData import AlpacaData
import ta
import datetime

class MACDstrategy(Algo):

	def init(self):
		self.set_schedule({"second": 5, "minute": 30, "hour": 13, "day_of_week": "mon-fri"})

	def run(self):
		hist = self.get_data("SPY", datatype="open", length=50)
		macd = ta.trend.macd_diff(hist, window_slow=26, window_fast=12, window_sign=9)[-1]
		if macd > 0:
			self.order_target_percent("SPY", 1.0)
		else:
			self.order_target_percent("SPY", 0.0)
			self.cancel_orders("SPY")

if __name__ == '__main__':
	end_date = datetime.datetime(2021,8,20)
	length = 200
	warmup = 60
	data = AlpacaData(start=length+warmup, end=end_date, symbols=["SPY"])
	manager = Manager(data)
	algo = MACDstrategy()
	manager.add_algo(algo)
	manager.backtest(start=length, end=end_date)