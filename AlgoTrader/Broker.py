import math
import datetime
import pandas as pd
from AlgoTrader.Util import get_api

class BacktestBroker:

	def __init__(self, data, cash=10000):
		self.cash = cash
		self.value = cash
		self.data = data
		self.positions = {}


	def order(self, symbol, amount, time):
		price = self.data.quote(symbol, time)
		total_price = price * amount
		current_shares = self.get_position_amount(symbol)
		if total_price > self.cash:
			print('Order Failed: {amount} shares of {symbol} at ${price} \
					 costs {total_price}, but you only have ${cash} in cash.'
					 .format(amount=amount, symbol=symbol, price=price, 
					 		 total_price=total_price, cash=self.cash))
			return
		if amount < 0 and abs(amount) > current_shares:
			print('Order Failed: tried to sell {amount} shares of {symbol}, \
					but you only have {actual_shares} shares.'
					 .format(amount=amount, symbol=symbol, actual_shares=current_shares))
			return
		self.cash -= total_price
		if symbol not in self.positions:
			self.positions[symbol] = {
					'amount': 0,
					'avg entry price': 0.0,
					'price': 0.0
				}
		if self.positions[symbol]['amount'] + amount != 0:
			self.positions[symbol]['avg entry price'] = \
					(self.positions[symbol]['amount'] * self.positions[symbol]['avg entry price'] + 
					 price * amount) / (self.positions[symbol]['amount'] + amount)
		self.positions[symbol]['amount'] += amount
		self.positions[symbol]['price'] = price
		if amount > 0:
			print("Buying {amount} shares of {symbol} at ${price}.".format(amount=amount, symbol=symbol, price=price))
		elif amount < 0:
			print("Selling {amount} shares of {symbol} at ${price}.".format(amount=abs(amount), symbol=symbol, price=price))


	def order_target_percent(self, symbol, percent, time):
		account = self.get_value(time)
		cash = account['cash']
		value = account['value']
		price = self.data.quote(symbol, time)
		current_amount = self.get_position_amount(symbol)
		desired_amount = math.floor(value * percent / price)
		diff = desired_amount - current_amount
		if percent > 1 or percent < 0:
			print("Order Failed. The target percent must be between 0 and 1, \
					but you entered {percent}.".format(percent=percent))
			return
		if diff * price > cash:
			print("Order Failed. You tried to order {diff} shares of {symbol} \
					at ${price}, but you only have ${cash} in cash. This is because \
					the target percent you entered ({percent}) is greater than the percent of \
					your portfolio which is in cash ({cash_percent})".format(diff=diff, symbol=symbol,
						price=price, cash=cash, percent=percent, cash_percent=cash/value))
			return
		self.order(symbol, diff, time)


	def get_position_amount(self, symbol):
		if symbol in self.positions:
			return self.positions[symbol]['amount']
		return 0


	def get_positions(self, time):
		for symbol in self.positions.keys():
			if self.positions[symbol]['amount'] == 0:
				del self.positions[symbol]
				continue
			self.positions[symbol]['price'] = self.data.quote(symbol, time)
		return self.positions


	def get_value(self, time):
		positions_value = 0
		for symbol in self.positions.keys():
			self.positions[symbol]['price'] = self.data.quote(symbol, time)
			positions_value += self.positions[symbol]['price'] * self.positions[symbol]['amount']
		self.value = self.cash + positions_value
		return {"value": self.value, "cash": self.cash}





class AlpacaBroker:

	def __init__(self, paper=True):
		self.api = get_api(paper)
		self.start_date = datetime.datetime.now()
		

	def order(self, symbol, amount, time=datetime.datetime.now()):
		if amount > 0:
			orderid = self.api.submit_order(symbol=symbol, side='buy', type='market', qty=str(amount), time_in_force='day')
			return orderid
		elif amount < 0:
			orderid = self.api.submit_order(symbol=symbol, side='sell', type='market', qty=str(amount), time_in_force='day')
			return orderid


	def order_target_percent(self, symbol, percent, time=datetime.datetime.now()):
		account_value = self.get_value()['value']
		positions = self.get_positions(time=time)
		current_amount = positions[symbol]['amount']
		desired_amount = math.floor(account_value * percent / positions[symbol]['price'])
		diff = desired_amount - current_amount
		self.order(symbol=symbol, amount=diff, time=time)



	def get_history(self, start=None, end=None, timeframe='day'):
		if timeframe == 'day':
			timeframe = '1D'
		elif timeframe == 'minute':
			timeframe = '1Min'
		if start is None:
			start = self.start_date
		if end is None:
			end = datetime.datetime.now()
		start_date = start.date().isoformat()
		end_date = end.date().isoformat()
		hist = self.api.get_portfolio_history(date_start=start_date, date_end=end_date, timeframe=timeframe)
		times = [pd.Timestamp(time, unit='s') for time in hist.timestamp]
		values = pd.Series(hist.equity, times)
		return values


	def get_positions(self, time=datetime.datetime.now()):
		positions = {}
		position_data = self.api.list_positions()
		for entry in position_data:
			positions[entry.symbol] = {}
			positions[entry.symbol]['amount'] = float(entry.qty)
			positions[entry.symbol]['avg entry price'] = float(entry.avg_entry_price)
			positions[entry.symbol]['price'] = float(entry.current_price)
		return positions


	def get_value(self, time=datetime.datetime.now()):
		account = {}
		account_data = self.api.get_account()
		account['value'] = float(account_data.equity)
		account['cash'] = float(account_data.cash)
		return account


# TODO: 
# 1. order types other than market
# 2. wait_until_filled(orderid)

if __name__ == '__main__':
	broker = AlpacaBroker(paper=True)
	broker.order_target_percent("SPY", 0.2)


