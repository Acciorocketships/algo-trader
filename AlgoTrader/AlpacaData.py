import alpaca_trade_api as tradeapi
import datetime
import pandas as pd
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
import json
from AlgoTrader.Util import get_api, timeframe_to_timedelta, trading_day_offset
from AlgoTrader.Logger import Logger

class AlpacaData:

	timezone = pytz.timezone('America/New_York')

	def __init__(self, symbols=["SPY"], timeframe='minute',
						start=0, end=datetime.datetime.now(),
						live=False, callbacks=[], schedule=["* 9-16 * * *"]):

		self.api = get_api(paper=True)

		self.calc_start_end(start, end)
		self.timeframe = timeframe
		self.symbols = symbols
		self.data = {symbol: None for symbol in symbols}

		if start != 0:
			self.load_symbols(symbols)

		self.live = live
		self.trigger = OrTrigger([CronTrigger.from_crontab(cron, timezone=AlpacaData.timezone) for cron in schedule])
		self.scheduler = BackgroundScheduler()
		self.scheduler.configure(timezone=AlpacaData.timezone)
		self.callbacks = callbacks
		if self.live:
			self.start_live()


	def calc_start_end(self, start, end):
		# If start/end are datetimes, then they are directly set
		# If one of them is an int, then it is that number of trading days before/after the other
		# For example, if start is 10 and end is datetime.datetime(2021,3,5), then start will be whatever date
		#		that makes the interval start-end 10 trading days long.
		# If times are not given, it defaults to 00:00 for the start date and 23:59 for the end date
		if isinstance(start, datetime.datetime):
			self.start = start
		else:
			self.start = trading_day_offset(day=end, offset=-start)
		if isinstance(end, datetime.datetime):
			self.end = end
		else:
			self.end = trading_day_offset(day=start, offset=end)
		if self.end.hour==0 and self.end.minute==0:
			self.end = self.end.replace(hour=23,minute=59)


	def load_symbols(self, symbols=[]):
		for symbol in symbols:
			self.data[symbol] = self.get_data(symbol)


	def get_data(self, symbol="SPY", start=None, end=None, timeframe=None):
		if start is None:
			start = self.start
		if end is None:
			end = self.end
		if timeframe is None:
			timeframe = self.timeframe
		slice_start = pd.Timestamp(start).replace(tzinfo=AlpacaData.timezone)
		slice_end = pd.Timestamp(end).replace(tzinfo=AlpacaData.timezone)
		orig_start = pd.Timestamp(start).replace(tzinfo=AlpacaData.timezone)
		orig_end = pd.Timestamp(end).replace(tzinfo=AlpacaData.timezone)
		data = None
		while True:
			startts = slice_start.isoformat()
			endts = slice_end.isoformat()
			df = self.api.get_barset(symbol, timeframe, start=startts, end=endts, limit=1000).df[symbol]
			if len(df) <= 1:
				break
			if data is None:
				data = df
			else:
				df = df[:df.index[-2]]
				data = pd.concat([df, data]) # try combine_first as well
			slice_end = df.index[0]
			if slice_end <= orig_start:
				break
		if timeframe == 'day':
			data.index = [ts.replace(hour=9, minute=30) for ts in data.index]
		return data[orig_start:orig_end]


	def update_symbols(self):
		new_data_dict = {}
		for symbol, old_data in self.data.items():
			current_time = pd.Timestamp(datetime.datetime.now().astimezone(AlpacaData.timezone))
			if old_data is None:
				new_data = self.get_data(symbol=symbol, start=current_time, end=current_time, timeframe=self.timeframe)
				self.data[symbol] = new_data
				new_data_dict[symbol] = new_data
			else:
				last_time = self.data[symbol].index[-1]
				new_data = self.get_data(symbol=symbol, start=last_time, end=current_time, timeframe=self.timeframe)
				updated_data = pd.concat([old_data[:-1], new_data])
				self.data[symbol] = updated_data
				new_data_dict = new_data
		return new_data_dict


	def start_live(self):
		self.live = True
		self.scheduler.add_job(self.scheduled_update, self.trigger)
		self.scheduler.start()


	def stop_live(self):
		self.live = False
		self.scheduler.shutdown(wait=True)


	def scheduled_update(self):
		clock = self.api.get_clock()
		if clock.is_open:
			new_data = self.update_symbols()
			for callback in self.callbacks:
				callback(new_data, self)


	def get(self, symbol, start=None, end=None, length=None):
		if isinstance(start, int):
			start = trading_day_offset(day=end, offset=-start)
		if isinstance(end, int):
			end = trading_day_offset(day=start, offset=end)
		if isinstance(start, datetime.datetime):
			start = pd.Timestamp(start.replace(tzinfo=AlpacaData.timezone))
		if isinstance(end, datetime.datetime):
			end = pd.Timestamp(end.replace(tzinfo=AlpacaData.timezone))
		if start is None:
			if length is None:
				start = self.data[symbol].index[0]
			else:
				end = self.data[symbol].index.get_loc(end, method='pad')+1
				start = max(0, end-length)
		if end is None:
			if length is None:
				end = self.data[symbol].index[-1]
			else:
				start = self.data[symbol].index.get_loc(start, method='pad')
				end = min(len(self.data[symbol])-1, start+length)
		return self.data[symbol][start:end]


	def quote(self, symbol, time):
		idx = self.data[symbol].index.get_loc(pd.Timestamp(time), method='pad')
		idx_time = self.data[symbol].index[idx]
		curr_time = pd.Timestamp(time).replace(tzinfo=AlpacaData.timezone)
		if self.timeframe != 'day':
			if curr_time >= idx_time + timeframe_to_timedelta(self.timeframe):
				datatype = 'close'
			else:
				datatype = 'open'
		else:
			if curr_time.to_pydatetime().time() < datetime.time(15,55):
				datatype = 'open'
			else:
				datatype = 'close'
		return self.data[symbol][datatype][idx]




if __name__ == '__main__':
	data = AlpacaData(start=5, timeframe='minute', symbols=["SPY"], live=True)
	import pdb; pdb.set_trace()

