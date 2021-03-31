import torch


class MarketPredictor(torch.nn.Module):

	def __init__(self):
		pass


	def forward(self, X):
		pass



def create_indicators(prices, window=12):
	# prices: batch x time (most recent last)

	data = {}
	input_length = prices.shape[1] - window + 1

	if include_output:
		output = percent_change(output_prices)[:,0]
		data['output'] = output * 100

	malong = moving_average(prices, window=window)[:,-input_length:]
	mashort = moving_average(prices, window=int(window/4))[:,-input_length:]
	macd = (mashort - malong) / malong
	data['macd'] = macd * 100

	pct = percent_change(prices)[:,-input_length:]
	data['pct'] = pct * 100

	x = torch.nn.functional.unfold(prices.unsqueeze(1).unsqueeze(3), kernel_size=(12,1)) # batch x channels (1) x dim1 (t) x dim2 (1)
	var = torch.var(x, dim=1)
	data['var'] = (var / malong) * 100

	return data


def percent_change(prices):
	return (prices[:,1:] / prices[:,:-1]) - 1


def moving_average(prices, window):
	kernel = torch.ones((1, 1, window), dtype=torch.float64) / window
	ma = torch.nn.functional.conv1d(prices.unsqueeze(1),kernel)[:,0,:]
	return ma