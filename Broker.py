import numpy as np
import alpaca_trade_api as tradeapi

class BacktestBroker:

	def __init__(self, data, cash=10000):
		self.cash = cash
		self.value = cash
		self.data = data
		self.positions = {}


	def order(self, symbol, amount, time):
		price = self.data.quote(symbol, time)
		total_price = price * amount
		if total_price > self.cash:
			print('Order Failed: {amount} shares of {symbol} at ${price} \
					 costs {total_price}, but you only have ${cash} in cash.'
					 .format(amount=amount, symbol=symbol, price=price, 
					 		 total_price=total_price, cash=self.cash))
			return
		if amount < 0 and abs(amount) > self.positions.get(symbol, 0):
			print('Order Failed: tried to sell {amount} shares of {symbol}, \
					but you only have {actual_shares} shares.'
					 .format(amount=amount, symbol=symbol, actual_shares=self.positions.get(symbol, 0)))
			return
		self.cash -= total_price
		if symbol not in self.positions:
			self.positions[symbol] = 0
		self.positions[symbol] += amount
		if amount > 0:
			print("Buying {amount} shares of {symbol} at ${price}.".format(amount=amount, symbol=symbol, price=price))
		elif amount < 0:
			print("Selling {amount} shares of {symbol} at ${price}.".format(amount=abs(amount), symbol=symbol, price=price))


	def order_target_percent(self, symbol, percent, time):
		self.update_value(time)
		price = self.data.quote(symbol, time)
		current_amount = self.positions.get(symbol, 0)
		desired_amount = np.floor(self.value * percent / price)
		diff = desired_amount - current_amount
		if percent > 1 or percent < 0:
			print("Order Failed. The target percent must be between 0 and 1, \
					but you entered {percent}.".format(percent=percent))
			return
		if diff * price > self.cash:
			print("Order Failed. You tried to order {diff} shares of {symbol} \
					at ${price}, but you only have ${cash} in cash. This is because \
					the target percent you entered ({percent}) is greater than the percent of \
					your portfolio which is in cash ({cash_percent})".format(diff=diff, symbol=symbol,
						price=price, cash=self.cash, percent=percent, cash_percent=self.cash/self.value))
			return
		self.order(symbol, diff, time)


	def update_value(self, time):
		positions_value = 0
		for symbol, amount in self.positions.items():
			if amount > 0:
				price = self.data.quote(symbol, time)
				positions_value += price * amount
		self.value = self.cash + positions_value





class AlpacaBroker:

	def __init__(self, paper=True):
		with open('creds.txt') as f:
			creds = json.load(f)
		key_id = creds["ALPACA_PAPER_API_KEY"] if paper else creds["ALPACA_API_KEY"]
		secret_key = creds["ALPACA_PAPER_SECRET_KEY"] if paper else creds["ALPACA_PAPER_SECRET_KEY"]
		self.api = tradeapi.REST(key_id, secret_key, base_url='https://api.alpaca.markets', api_version='v2')
		






