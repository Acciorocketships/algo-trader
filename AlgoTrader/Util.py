import pandas_market_calendars as mcal
import alpaca_trade_api as tradeapi
import datetime
import json
import pandas as pd
import numpy as np
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
import copy

nyse = mcal.get_calendar('NYSE')


def is_trading_day(date):
	date_range = nyse.schedule(start_date=date, end_date=date)
	return len(date_range) > 0


def trading_day_offset(day, offset):
	if isinstance(day, pd.Timestamp):
		day = day.to_pydatetime()
	if offset < 0:
		roughstart = day - datetime.timedelta(days=2*abs(offset)+5)
		cal = nyse.schedule(start_date=roughstart, end_date=day)
		return cal.index[offset-1].to_pydatetime()
	else:
		roughend = day + datetime.timedelta(days=2*abs(offset)+5)
		cal = nyse.schedule(start_date=day, end_date=roughend)
		return cal.index[offset].to_pydatetime()


def next_runtime(trigger, time):
	time += datetime.timedelta(seconds=1)
	nexttime = trigger.get_next_fire_time(None, time).replace(tzinfo=None)
	while not is_trading_day(nexttime):
		nextday = (nexttime + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
		nexttime = trigger.get_next_fire_time(None, nextday).replace(tzinfo=None)
	return nexttime


def equals_runtime(trigger, time):
	return time == trigger.get_next_fire_time(None, time.replace(tzinfo=None)).replace(tzinfo=None)


def get_creds(key):
	with open('creds.json') as f:
		creds = json.load(f)
	return creds[key]


def convert_trigger_timezone(trigger, timezone):
	new_trigger = copy.copy(trigger)
	convert_trigger_helper(new_trigger, timezone)
	return new_trigger

def convert_trigger_helper(trigger, timezone):
	if isinstance(trigger, OrTrigger):
		for trigger_child in trigger.triggers:
			convert_trigger_helper(trigger_child, timezone)
	elif isinstance(trigger, CronTrigger):
		trigger.timezone = timezone


def np_to_datetime(time):
	if isinstance(time, np.datetime64):
		return datetime.datetime.utcfromtimestamp(time.astype(int) * 1e-9)
	elif isinstance(time, np.ndarray):
		times = np.empty(time.shape, dtype=object)
		for idx in range(len(time)):
			times[idx] = np_to_datetime(time[idx])
		return times

def build_trigger(schedule):
	if isinstance(schedule, list) and len(schedule) != 1:
		trigger = OrTrigger([CronTrigger(**cron) for cron in schedule])
	elif isinstance(schedule, list) and len(schedule) == 1:
		cron = schedule[0]
		trigger = CronTrigger(**cron)
	else:
		cron = schedule
		trigger = CronTrigger(**cron)
	return trigger

