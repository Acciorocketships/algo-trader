import pandas as pd
import numpy as np
import quantstats as qs

class Logger:

	def __init__(self):
		self.value = []
		self.benchmark = []
		self.value_times = []
		self.benchmark_times = []
		self.returns = None
		self.benchmark_returns = None

	def append(self, val, time, benchmark=False):
		if benchmark:
			self.benchmark.append(val)
			self.benchmark_times.append(pd.Timestamp(time))
		else:
			self.value.append(val)
			self.value_times.append(pd.Timestamp(time))

	def calc_returns(self):
		self.value = np.array(self.value)
		self.benchmark = np.array(self.benchmark)
		self.returns = (self.value[1:] / self.value[:-1]) - 1
		self.benchmark_returns = (self.benchmark[1:] / self.benchmark[:-1]) - 1
		self.returns = pd.Series(self.returns, index=pd.Index(self.value_times[1:]), name="Algo")
		self.benchmark_returns = pd.Series(self.benchmark_returns, index=pd.Index(self.benchmark_times[1:]), name="Benchmark")


	def report(self, filename="report.html"):
		if self.returns is None:
			self.calc_returns()
		qs.reports.html(self.returns, self.benchmark_returns, output=filename)

		
	def metrics(self):
		metrics = {}
		if self.returns is None:
			self.calc_returns()
		metrics['sharpe'] = qs.stats.sharpe(self.returns)
		metrics['sortino'] = qs.stats.sortino(self.returns)
		greeks = qs.stats.greeks(self.returns, self.benchmark_returns)
		metrics['alpha'] = greeks['alpha']
		metrics['beta'] = greeks['beta']
		metrics['cagr'] = qs.stats.cagr(self.returns)
		metrics['max drawdown'] = qs.stats.max_drawdown(self.returns)
		metrics['avg win'] = qs.stats.avg_win(self.returns)
		metrics['avg loss'] = qs.stats.avg_loss(self.returns)
		metrics['win rate'] = qs.stats.win_rate(self.returns)
		metrics['total return'] = qs.stats.comp(self.returns)
		return metrics