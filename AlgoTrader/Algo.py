from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
import datetime
import pytz
import pandas as pd
from AlgoTrader.Util import is_trading_day, build_trigger


class Algo:

	def __init__(self, *args, **kwargs):
		self.datetime = None
		self.data = None
		self.broker = None
		self.next_runtime = None
		self.set_schedule([{"second": "30", "minute": "30", "hour": "13", "day_of_week": "mon-fri"}])
		self.init(*args, **kwargs)


	def set_schedule(self, schedule):
		self.trigger = build_trigger(schedule)


	def set_data_source(self, data):
		self.data = data


	def set_broker(self, broker):
		self.broker = broker


	def quote(self, symbol):
		return self.data.quote(symbol=symbol, time=self.datetime)


	def get_data(self, symbol, datatype, length):
		data = self.data.get(symbol, datatype=datatype, end=self.datetime, length=length)
		if datatype == "open":
			data.index = pd.Index([d.replace(hour=13, minute=30) for d in data.index])
		# This timedelta allows us to get data 10 minutes into the future (we can see 20:00 close data even if we run at 19:50)
		# This is needed so we can get real-time data if we choose to run near market close
		lookup = pd.Timestamp(self.datetime.replace(tzinfo=data.index.tz) + datetime.timedelta(minutes=10))
		last_idx = data.index.get_indexer([lookup], method='pad')[0]
		return data[:last_idx+1]


	def order(self, symbol, amount, limit=None, stop=None):
		self.broker.order(symbol=symbol, amount=amount, limit=limit, stop=stop, time=self.datetime)


	def order_target_percent(self, symbol, percent, limit=None, stop=None):
		self.broker.order_target_percent(symbol=symbol, percent=percent, limit=limit, stop=stop, time=self.datetime)


	def cancel_orders(self, symbol=None):
		self.broker.cancel_orders(symbol)


	def run_wrapper(self, time=None, update=True):
		self.datetime = time
		if update and not self.data.live:
			self.data.update_symbols()
		self.run()


	def init(self):
		pass

	def run(self):
		pass


if __name__ == '__main__':
	from AlgoTrader.AlpacaData import AlpacaData
	start_date = datetime.datetime(2021,6,1,19,55)
	end_date = datetime.datetime(2021,8,20,15,0)
	warmup = 20
	data = AlpacaData(start=start_date-datetime.timedelta(days=warmup), end=end_date, symbols=["SPY"])
	algo = Algo()
	algo.data = data
	algo.datetime = start_date
	x = algo.get_data("SPY", "close", length=10)
	breakpoint()