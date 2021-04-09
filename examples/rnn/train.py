import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tensorboard import program
import datetime
import math
import webbrowser
from AlgoTrader.AlpacaData import AlpacaData
from AlgoTrader.MarketDataSet import MarketDataSet, collate_fn
from Model import MarketPredictor, create_indicators, percent_change


def create_data(prices, window=12):
	datapoint = create_indicators(prices[:,:-1], window)
	X = torch.stack([datapoint['pct'], datapoint['macd1'], datapoint['macd2'],  datapoint['var']], dim=2)
	pct_output = percent_change(prices[:,-2:])
	Y = pct_output[:,0] * 100
	return X, Y


def loss_fn(dist, truth):
	# negative log loss, which approximates the KL-divergence in expectation
	logprob = -dist.log_prob(truth)
	return logprob.mean()


def accuracy(dist, truth):
	correct = torch.sign(dist.mean) == torch.sign(truth)
	return torch.sum(correct) / torch.numel(correct)


def load_model(model, path):
	try:
		fp = open(path, 'rb')
		print('Loaded Model ' + path)
	except:
		return
	model_dict = torch.load(fp)
	model.load_state_dict(model_dict)


def save_model(model, path):
	model_dict = model.state_dict()
	with open(path, 'wb') as fp:
		torch.save(model_dict, fp)
	print("Saved Model " + path)


if __name__ == '__main__':

	alpacadata = AlpacaData(symbols=["SPY"], timeframe='day', start=3000, end=datetime.datetime(2017,1,1))
	dataset = MarketDataSet(alpacadata, hist=40, datatypes=['open'])
	train_dataset, val_dataset = torch.utils.data.random_split(dataset, [len(dataset)-300, 300])
	train_dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
	val_dataloader = DataLoader(val_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)

	tensorboard = SummaryWriter()
	tb = program.TensorBoard()
	tb.configure(argv=[None, '--logdir', tensorboard.log_dir])
	url = tb.launch()
	webbrowser.open(url)

	model = MarketPredictor()

	model_path = 'model_params.pt'
	load_model(model, model_path)

	optimiser = torch.optim.Adam(model.parameters(), lr=1e-3)

	t = 0
	for epoch in range(300):
		for sample in train_dataloader:

			X, Y = create_data(sample["SPY"]["open"])

			model.train()
			optimiser.zero_grad()

			dist = model(X)

			loss = loss_fn(dist, Y)
			loss.backward()
			tensorboard.add_scalar('loss/train', loss, t)
			acc = accuracy(dist, Y)
			tensorboard.add_scalar('accuracy/train', acc, t)

			optimiser.step()

			if t % 10 == 0:
				model.eval()
				optimiser.zero_grad()
				val_sample = next(iter(val_dataloader))
				X, Y = create_data(val_sample["SPY"]["open"])
				dist = model(X)
				loss = loss_fn(dist, Y)
				tensorboard.add_scalar('loss/val', loss, t)
				acc = accuracy(dist, Y)
				tensorboard.add_scalar('accuracy/val', acc, t)

			t += 1

	save_model(model, model_path)


