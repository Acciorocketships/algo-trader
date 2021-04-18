import torch
from torch import nn
from torch.distributions.normal import Normal


class MarketPredictor(torch.nn.Module):

	def __init__(self, input_channels=4, recurrent=True):
		super().__init__()
		self.recurrent = recurrent
		# Parameters
		self.finput_layer_sizes = [input_channels, 8, 16, 16]
		self.foutput_layer_sizes = [16, 16, 8, 2]
		# Networks
		self.finput = self.create_net(layer_sizes=self.finput_layer_sizes)
		self.foutput = self.create_net(layer_sizes=self.foutput_layer_sizes, omit_last_activation=True)
		if self.recurrent:
			self.gru = nn.GRUCell(self.finput_layer_sizes[-1], self.finput_layer_sizes[-1])


	def create_net(self, layer_sizes, omit_last_activation=False):
		layers = []
		for i in range(len(layer_sizes)-1):
			layers.append(nn.Linear(layer_sizes[i], layer_sizes[i+1]))
			layers.append(nn.BatchNorm1d(layer_sizes[i+1]))
			if i < len(layer_sizes)-2 or not omit_last_activation:
				layers.append(nn.ReLU())
		return nn.Sequential(*layers)


	def forward(self, x):
		# x: batch x time x channels
		if self.recurrent:
			batch, timesteps, channels = x.shape
			x_input = self.finput(x.float().reshape(batch * timesteps, channels)).reshape(batch, timesteps, self.finput_layer_sizes[-1])
			hidden = torch.zeros(batch, self.finput_layer_sizes[-1])
			for t in range(timesteps):
				hidden = self.gru(x_input[:,t,:], hidden)
			x_output = self.foutput(hidden)
			return self.dist(x_output[:,0], x_output[:,1])
		else:
			batch, channels = x.shape
			x_input = self.finput(x)
			x_output = self.foutput(x_input)
			return self.dist(x_output[:,0], x_output[:,1])


	def dist(self, mean, var):
		return Normal(mean, torch.abs(var))



def loss_fn(dist, truth):
	# negative log loss, which approximates the KL-divergence in expectation
	logprob = -dist.log_prob(truth)
	return logprob.mean()


def stats(dist, truth):
	correct = torch.sign(dist.mean) == torch.sign(truth)
	accuracy = torch.sum(correct) / torch.numel(correct)
	return {"accuracy": accuracy}


def create_indicators(prices, window=18):
	# prices: batch x time (most recent last)

	data = {}
	input_length = prices.shape[1] - window + 1

	malong = moving_average(prices, window=int(window/2))[:,-input_length:]
	mashort = moving_average(prices, window=int(window/6))[:,-input_length:]
	macd1 = (mashort - malong) / malong
	data['macd1'] = macd1 * 100

	malong = moving_average(prices, window=int(window))[:,-input_length:]
	mashort = moving_average(prices, window=int(window/3))[:,-input_length:]
	macd2 = (mashort - malong) / malong
	data['macd2'] = macd2 * 100

	pct = percent_change(prices)[:,-input_length:]
	data['pct'] = pct * 100

	x = nn.functional.unfold(prices.unsqueeze(1).unsqueeze(3), kernel_size=(12,1)) # batch x channels (1) x dim1 (t) x dim2 (1)
	var = torch.var(x, dim=1)
	data['var'] = (var / malong) * 100

	return data


def percent_change(prices):
	return (prices[:,1:] / prices[:,:-1]) - 1


def moving_average(prices, window):
	kernel = torch.ones((1, 1, window), dtype=torch.float64) / window
	ma = torch.nn.functional.conv1d(prices.unsqueeze(1),kernel)[:,0,:]
	return ma