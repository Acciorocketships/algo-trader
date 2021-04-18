import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tensorboard import program
import datetime
import math
import webbrowser
from AlgoTrader.AlpacaData import AlpacaData
from AlgoTrader.MarketDataSet import MarketDataSet, collate_fn
from Model import MarketPredictor, create_indicators, percent_change, loss_fn, stats


def create_data(prices, window):
	datapoint = create_indicators(prices[:,:-1], window)
	X = torch.stack([datapoint['pct'], datapoint['macd1'], datapoint['macd2'],  datapoint['var']], dim=-1)
	pct_output = percent_change(prices[:,-2:])
	Y = pct_output[:,0] * 100
	return X, Y


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

	length = 41
	window = 18

	alpacadata = AlpacaData(symbols=["SPY"], timeframe='day', start=3000, end=datetime.datetime(2017,1,1))
	dataset = MarketDataSet(alpacadata, hist=length, datatypes=['open'])
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
	for epoch in range(150):
		for sample in train_dataloader:

			X, Y = create_data(sample["SPY"]["open"], window=window)

			model.train()
			optimiser.zero_grad()

			dist = model(X)

			loss = loss_fn(dist, Y)
			loss.backward()
			tensorboard.add_scalar('loss/train', loss, t)
			stat = stats(dist, Y)
			tensorboard.add_scalar('accuracy/train', stat['accuracy'], t)
			tensorboard.add_scalar('precision/train', stat['precision'], t)
			tensorboard.add_scalar('recall/train', stat['recall'], t)

			optimiser.step()

			if t % 10 == 0:
				model.eval()
				optimiser.zero_grad()
				val_sample = next(iter(val_dataloader))
				X, Y = create_data(val_sample["SPY"]["open"], window=window)
				dist = model(X)
				loss = loss_fn(dist, Y)
				tensorboard.add_scalar('loss/val', loss, t)
				stat = stats(dist, Y)
				tensorboard.add_scalar('accuracy/val', stat['accuracy'], t)
				tensorboard.add_scalar('precision/val', stat['precision'], t)
				tensorboard.add_scalar('recall/val', stat['recall'], t)

			t += 1

	save_model(model, model_path)


