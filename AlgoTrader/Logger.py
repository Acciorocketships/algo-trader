import pandas as pd
import quantstats as qs

class Logger:

	def __init__(self):
		self.value = pd.Series(dtype=float)
		self.benchmark = pd.Series(dtype=float)
		self.returns = None
		self.benchmark_returns = None

	def append(self, val, time, benchmark=False):
		newval = pd.Series([val], index=[pd.Timestamp(time)])
		if benchmark:
			self.benchmark = self.benchmark.append(newval)
		else:
			self.value = self.value.append(newval)

	def calc_returns(self):
		self.returns = (self.value[1:] / self.value[:-1].values) - 1
		self.benchmark_returns = (self.benchmark[1:] / self.benchmark[:-1].values) - 1

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