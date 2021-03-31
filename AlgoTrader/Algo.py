from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
import datetime
import pytz
from AlgoTrader.Util import is_trading_day


class Algo:

	timezone = pytz.timezone('America/New_York')

	def __init__(self, *args, **kwargs):
		self.datetime = None
		self.data = None
		self.next_runtime = None
		self.set_schedule(["* 9-16 * * *"])
		self.init(*args, **kwargs)


	def set_schedule(self, schedule):
		self.schedule = schedule
		self.trigger = OrTrigger([CronTrigger.from_crontab(cron) for cron in schedule])


	def set_data_source(self, data):
		self.data = data


	def set_broker(self, broker):
		self.broker = broker


	def get_data(self, symbol, length=1, days=None, datatype='open'):
		return self.data.get(symbol, length=length, start=days, end=self.datetime)[datatype]


	def order(self, symbol, amount):
		self.broker.order(symbol=symbol, amount=amount, time=self.datetime)


	def order_target_percent(self, symbol, percent):
		self.broker.order_target_percent(symbol=symbol, percent=percent, time=self.datetime)


	def init(self):
		pass

	def run(self):
		pass


	# def run_event(self):
	# 	self.datetime = datetime.datetime.now()
	# 	self.run()
	# 	# log? update data?