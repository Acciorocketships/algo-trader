import math
import datetime
import pandas as pd
from AlgoTrader.Util import get_creds

class BacktestBroker:

	def __init__(self, data, cash=10000):
		self.cash = cash
		self.value = cash
		self.data = data
		self.positions = {}
		self.limit_orders = {} # (symbol, starttime): (price, amount, above(1)/below(-1))


	def order(self, symbol, amount, limit=None, stop=None, price=None, time=None):

		if amount == 0:
			return

		if price is None:
			price = self.data.quote(symbol, time)

		if (limit is None) and (stop is None or amount > 0):
			total_price = price * amount
			current_shares = self.get_position_amount(symbol)
			if total_price > self.cash:
				print(('Order Failed: {amount} shares of {symbol} at ${price} '
						 'costs {total_price}, but you only have ${cash} in cash.')
						 .format(amount=amount, symbol=symbol, price=price, 
						 		 total_price=total_price, cash=self.cash))
				return
			if amount < 0 and abs(amount) > current_shares:
				print(('Order Failed: tried to sell {amount} shares of {symbol}, '
						'but you only have {actual_shares} shares.')
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
				print("Buying {amount} shares of {symbol} at ${price:.2f}.".format(amount=amount, symbol=symbol, price=price))
			elif amount < 0:
				print("Selling {amount} shares of {symbol} at ${price:.2f}.".format(amount=abs(amount), symbol=symbol, price=price))

		if limit is not None:
			if (limit > 0 and amount < 0) or (limit < 0 and amount > 0):
				print(('Order Failed: You tried to place an order for {amount} shares '
					'with a limit percent of {limit}. When buying, the limit must be <0, '
					'and when selling the limit must be >0.').format(amount=amount, limit=limit))
			sign = limit / abs(limit) if (limit != 0) else 1
			limit_price = (1.0 + limit) * price
			self.limit_orders[(symbol, time)] = (limit_price, amount, sign)

		if stop is not None:
			sign = stop / abs(stop) if (stop != 0) else 1
			stop_price = (1.0 + stop) * price
			self.limit_orders[(symbol, time)] = (stop_price, -abs(amount), sign)



	def check_limit_orders(self, time=None):
		for (symbol, starttime), (price, amount, sign) in list(self.limit_orders.items()):
			hist = self.data.get(symbol, start=starttime, end=time)
			if sign < 0:
				low = hist['low'].min()
				if low < price:
					if amount < 0:
						print(('Stop Loss kicking in. Selling {amount} shares of {symbol} ' 
							'at ${price:.2f}.').format(amount=abs(amount), symbol=symbol, price=price))
					else:
						print(('Limit Order kicking in. Buying {amount} shares of {symbol} '
							'at ${price:.2f}.').format(amount=amount, symbol=symbol, price=price))
					self.order(symbol=symbol, amount=amount, price=price, time=time)
					del self.limit_orders[(symbol, starttime)]
			else:
				high = hist['high'].max()
				if high > price:
					if amount < 0:
						print(('Take Gain kickin in. Selling {amount} shares of {symbol} ' 
							'at ${price:.2f}').format(amount=abs(amount), symbol=symbol, price=price))
					else:
						print(('Invalid Limit Order. You are ttempting to place a buy order '
							'for a price higher than the current price.'))
					self.order(symbol=symbol, amount=amount, price=price, time=time)
					del self.limit_orders[(symbol, starttime)]



	def order_target_percent(self, symbol, percent, limit=None, stop=None, time=None):
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
					at ${price:.2f}, but you only have ${cash} in cash. This is because \
					the target percent you entered ({percent}) is greater than the percent of \
					your portfolio which is in cash ({cash_percent})".format(diff=diff, symbol=symbol,
						price=price, cash=cash, percent=percent, cash_percent=cash/value))
			return
		self.order(symbol=symbol, amount=diff, limit=limit, stop=stop, time=time)


	def get_position_amount(self, symbol):
		if symbol in self.positions:
			return self.positions[symbol]['amount']
		return 0


	def get_positions(self, time=None):
		for symbol in self.positions.keys():
			if self.positions[symbol]['amount'] == 0:
				del self.positions[symbol]
				continue
			self.positions[symbol]['price'] = self.data.quote(symbol, time)
		return self.positions


	def get_value(self, time=None):
		positions_value = 0
		for symbol in self.positions.keys():
			self.positions[symbol]['price'] = self.data.quote(symbol, time)
			positions_value += self.positions[symbol]['price'] * self.positions[symbol]['amount']
		self.value = self.cash + positions_value
		return {"value": self.value, "cash": self.cash}


	def cancel_orders(self, symbol=None):
		if symbol is None:
			self.limit_orders = {}
		else:
			for stock, order_placed in list(self.limit_orders.keys()):
				if stock==symbol:
					del self.limit_orders[(stock, order_placed)]



class AlpacaBroker:

	def __init__(self, paper=True):
		self.api = get_api(paper)
		self.start_date = datetime.datetime.now()
		

	def order(self, symbol, amount, limit=None, stop=None, price=None, time=datetime.datetime.now()):
		# stop < 0: stop loss. stop > 0 take gain. if it is a buy order, then it places the stop order after the buy is filled
		price = self.quote(symbol)
		order_type = 'market'
		limit_price = None
		if stop is not None:
			stop_price = (1.0 + stop) * price
		if limit is not None:
			limit_price = (1.0 + limit) * price
			order_type = 'limit'
		if amount > 0:
			if stop is None:
				orderid = self.api.submit_order(symbol=symbol, side='buy', type=order_type, limit_price=limit_price, qty=str(amount), time_in_force='day')
			else:
				if stop_price > price:
					orderid = self.api.submit_order(symbol=symbol, side='buy', type=order_type, limit_price=limit_price, qty=str(amount), time_in_force='gtc', order_class='oto', take_profit={'limit_price': stop_price})
				else:
					orderid = self.api.submit_order(symbol=symbol, side='buy', type=order_type, limit_price=limit_price, qty=str(amount), time_in_force='gtc', order_class='oto', stop_loss={'stop_price': stop_price})
			return orderid
		elif amount < 0:
			if stop is None:
				orderid = self.api.submit_order(symbol=symbol, side='sell', type=order_type, limit_price=limit_price, qty=str(abs(amount)), time_in_force='day')
			else:
				if stop_price > price:
					orderid = self.api.submit_order(symbol=symbol, side='sell', type='limit', qty=str(abs(amount)), time_in_force='gtc', order_class='oco', take_profit={'limit_price': stop_price}, stop_loss={'stop_price': 0})
				else:
					orderid = self.api.submit_order(symbol=symbol, side='sell', type='limit', qty=str(abs(amount)), time_in_force='gtc', order_class='oco', take_profit={'limit_price': 100*price}, stop_loss={'stop_price': stop_price})
			return orderid


	def order_target_percent(self, symbol, percent, limit=None, stop=None, time=datetime.datetime.now()):
		account_value = self.get_value()['value']
		positions = self.get_positions(time=time)
		current_amount = positions[symbol]['amount'] if (symbol in positions) else 0
		price = positions[symbol]['price'] if (symbol in positions) else self.quote(symbol)
		desired_amount = math.floor(account_value * percent / price)
		diff = desired_amount - current_amount
		self.order(symbol=symbol, amount=diff, limit=limit, stop=stop, time=time)



	def quote(self, symbol):
		price = self.api.get_last_trade(symbol).price
		return price



	def get_history(self, start=None, end=None):
		if start is None:
			start = self.start_date
		if end is None:
			end = datetime.datetime.now()
		start_date = start.date().isoformat()
		end_date = end.date().isoformat()
		hist = self.api.get_portfolio_history(date_start=start_date, date_end=end_date, timeframe='1D')
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


	def cancel_orders(self, symbol=None):
		if symbol is None:
			self.api.cancel_all_orders()
		else:
			orders = list(filter(lambda order: order.symbol==symbol, self.api.list_orders()))
			for order in orders:
				self.api.cancel_order(order.id)



if __name__ == '__main__':
	broker = AlpacaBroker(paper=True)
	broker.cancel_orders()
	broker.order("SPY", 5)
	broker.order("SPY", -4, stop=-0.01)
	print(broker.api.list_orders())


