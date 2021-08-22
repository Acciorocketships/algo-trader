from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
import datetime
import pytz
from AlgoTrader.Util import is_trading_day, build_trigger


class Algo:

	def __init__(self, *args, **kwargs):
		self.datetime = None
		self.data = None
		self.broker = None
		self.next_runtime = None
		self.set_schedule([{"second": 5, "minute": 30, "hour": 9, "day_of_week": "mon-fri"}])
		self.init(*args, **kwargs)


	def set_schedule(self, schedule):
		self.trigger = build_trigger(schedule)


	def set_data_source(self, data):
		self.data = data


	def set_broker(self, broker):
		self.broker = broker


	def get_data(self, symbol, length=1, days=None):
		if self.data.timeframe == 'minute':
			return self.data.get(symbol, length=length, start=days, end=self.datetime)['open']
		elif self.data.timeframe == 'day':
			if self.datetime.time() < datetime.time(15,55):
				open_day_prices = self.data.get(symbol, length=length, start=days, end=self.datetime)['open']
				open_day_prices.index = [ts.replace(hour=9, minute=30) for ts in open_day_prices.index]
				return open_day_prices
			else:
				close_day_prices = self.data.get(symbol, length=length, start=days, end=self.datetime)['close']
				close_day_prices.index = [ts.replace(hour=16, minute=0) for ts in close_day_prices.index]
				return close_day_prices



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


	# def run_event(self):
	# 	self.datetime = datetime.datetime.now()
	# 	self.run()
	# 	# log? update data?