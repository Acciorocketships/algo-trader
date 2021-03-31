import pandas_market_calendars as mcal
import datetime

nyse = mcal.get_calendar('NYSE')


def is_trading_day(date):
	date_range = nyse.schedule(start_date=date, end_date=date)
	return len(date_range) > 0


def next_runtime(trigger, time):
	time += datetime.timedelta(seconds=1)
	nexttime = trigger.get_next_fire_time(None, time).replace(tzinfo=None)
	while not is_trading_day(nexttime):
		nextday = (nexttime + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
		nexttime = trigger.get_next_fire_time(None, nextday).replace(tzinfo=None)
	return nexttime


def equals_runtime(trigger, time):
	return time == trigger.get_next_fire_time(None, time).replace(tzinfo=None)


def timeframe_to_timedelta(timeframe):
	if timeframe == 'minute':
		return datetime.timedelta(minutes=1)
	if timeframe == 'day':
		return datetime.timedelta(days=1)
	if timeframe == 'hour':
		return datetime.timedelta(hours=1)
	if timeframe == 'second':
		return datetime.timedelta(seconds=1)