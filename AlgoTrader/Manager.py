import datetime
from AlgoTrader.AlpacaData import AlpacaData
from AlgoTrader.Broker import BacktestBroker, AlpacaBroker
from AlgoTrader.Logger import Logger
from AlgoTrader.Util import next_runtime, equals_runtime
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger


class Manager:

	def __init__(self, data):
		self.data = data
		self.algos = []
		self.broker = None
		self.logger = Logger()
		self.datetime = datetime.datetime.now()
	

	def init_broker(self, backtest=False, **kwargs):
		if backtest:
			self.broker = BacktestBroker(**kwargs)
		else:
			self.broker = AlpacaBroker(**kwargs)
		for algo in self.algos:
			algo.set_broker(self.broker)


	def add_algo(self, algo):
		algo.set_data_source(self.data)
		algo.set_broker(self.broker)
		self.algos.append(algo)


	def backtest(self, start=datetime.datetime(2021,3,1), end=datetime.datetime.now(), logschedule=["30 9 * * *"]):
		self.init_broker(backtest=True, data=self.data)
		log_trigger = OrTrigger([CronTrigger.from_crontab(cron) for cron in logschedule])
		algo_trigger = OrTrigger([algo.trigger for algo in self.algos])
		trigger = OrTrigger([algo_trigger, log_trigger])
		self.datetime = start
		while self.datetime < end:
			for algo in self.algos:
				if equals_runtime(algo.trigger, self.datetime):
					algo.datetime = self.datetime
					algo.run()
			if equals_runtime(log_trigger, self.datetime):
				self.log_state()
			self.datetime = next_runtime(trigger, self.datetime)
		metrics = self.logger.metrics()
		for metric, value in metrics.items():
			print("{metric}: {value:.3f}".format(metric=metric, value=value))
		self.logger.report()


	def log_state(self):
		self.broker.update_value(self.datetime)
		value = self.broker.value
		benchmark_value = self.data.quote("SPY", self.datetime)
		self.logger.append(value, self.datetime)
		self.logger.append(benchmark_value, self.datetime, benchmark=True)





