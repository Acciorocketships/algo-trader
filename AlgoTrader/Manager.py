import datetime
import pytz
import code
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from AlgoTrader.AlpacaData import AlpacaData
from AlgoTrader.Broker import BacktestBroker, AlpacaBroker
from AlgoTrader.Logger import Logger
from AlgoTrader.Util import next_runtime, equals_runtime, convert_trigger_timezone, build_trigger, trading_day_offset


class Manager:

	timezone = pytz.timezone('America/New_York')

	def __init__(self, data):
		self.data = data
		self.algos = []
		self.broker = None
		self.logger = Logger()
		self.datetime = None
		self.scheduler = BackgroundScheduler()
		self.scheduler.configure(timezone=Manager.timezone)
		self.jobs = {}
	

	def init_broker(self, backtest=False, **kwargs):
		if backtest:
			self.broker = BacktestBroker(**kwargs)
		else:
			self.broker = AlpacaBroker(**kwargs)
		for algo in self.algos:
			algo.set_broker(self.broker)


	def add_algo(self, algo, live=False):
		if algo.data is None:
			algo.set_data_source(self.data)
		if algo.broker is None:
			algo.set_broker(self.broker)
		self.algos.append(algo)
		if live:
			trigger = convert_trigger_timezone(algo.trigger, Manager.timezone)
			job = self.scheduler.add_job(self.run_algo_live, trigger, kwargs={'algo': algo})
			self.jobs[algo] = job


	def stop_algo(self, algo):
		job = self.jobs[algo]
		job.remove()


	def remove_algo(self, algo):
		self.stop_algo(algo)
		del self.algos[algo]


	def log_state(self):
		value = self.broker.get_value(self.datetime)['value']
		benchmark_value = self.data.quote("SPY", self.datetime)
		self.logger.append(value, self.datetime)
		self.logger.append(benchmark_value, self.datetime, benchmark=True)


	def run_algo_live(self, algo):
		self.datetime = datetime.datetime.now().astimezone(Manager.timezone)
		# print("{time}: Running {algo}".format(time=self.datetime, algo=algo.__class__.__name__))
		algo.run_wrapper(time=self.datetime, update=True)


	def backtest(self, start=datetime.datetime(2021,3,1), end=datetime.datetime.now(), log_schedule=[{"minute": "30", "hour": "9", "day_of_week": "mon-fri"}]):
		self.init_broker(backtest=True, data=self.data)
		log_trigger = build_trigger(log_schedule)
		algo_trigger = OrTrigger([algo.trigger for algo in self.algos])
		trigger = OrTrigger([algo_trigger, log_trigger])
		logging = isinstance(log_schedule, dict) or len(log_schedule) > 0
		if isinstance(start, int) and not isinstance(end, int):
			start = trading_day_offset(end, -start)
		if not isinstance(start, int) and isinstance(end, int):
			end = trading_day_offset(start, end)
		self.datetime = start
		while self.datetime < end:
			for algo in self.algos:
				if equals_runtime(algo.trigger, self.datetime):
					print(self.datetime)
					time = Manager.timezone.localize(self.datetime)
					self.broker.check_limit_orders(time=time)
					algo.run_wrapper(time=time, update=False)
			if logging and equals_runtime(log_trigger, self.datetime):
				self.log_state()
			self.datetime = next_runtime(trigger, self.datetime)
		metrics = self.logger.metrics()
		for metric, value in metrics.items():
			print("{metric}: {value:.3f}".format(metric=metric, value=value))
		self.logger.report()
		return metrics


	def run(self, paper=False, log_schedule=[{"minute": "30", "hour": "9", "day_of_week": "mon-fri"}]):
		self.init_broker(backtest=False, paper=paper)
		self.datetime = datetime.datetime.now().astimezone(Manager.timezone)
		for algo in self.algos:
			trigger = convert_trigger_timezone(algo.trigger, Manager.timezone)
			job = self.scheduler.add_job(self.run_algo_live, trigger, kwargs={'algo': algo})
			self.jobs[algo] = job
		log_trigger = convert_trigger_timezone(build_trigger(log_schedule), Manager.timezone)
		job = self.scheduler.add_job(self.log_state, log_trigger)
		self.jobs['logger'] = job
		self.start()
		self.interact()


	def start(self):
		self.scheduler.start()


	def stop(self):
		for algo in self.jobs.keys():
			self.stop_algo(algo)
		self.scheduler.shutdown(wait=True)


	def pause(self):
		self.scheduler.pause()


	def resume(self):
		self.scheduler.resume()


	def interact(self):
		code.interact(local=locals())




