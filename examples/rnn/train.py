import torch
from torch.utils.data import DataLoader
from AlgoTrader.AlpacaData import AlpacaData
from AlgoTrader.MarketDataSet import MarketDataSet, collate_fn
import datetime
from model import create_indicators, percent_change


def create_data(prices, window=12):
	datapoint = create_indicators(prices[:,:-1], window)
	X = torch.stack([datapoint['macd'], datapoint['pct'], datapoint['var']], dim=1)
	pct_output = percent_change(prices[:,-2:])[:,0]
	Y = pct_output * 100
	return X, Y


if __name__ == '__main__':
	alpacadata = AlpacaData(symbols=["SPY"], timeframe='day', start=1000, end=datetime.datetime(2018,1,1))
	dataset = MarketDataSet(alpacadata, hist=30, datatypes=['open'])
	dataloader = DataLoader(dataset, batch_size=16, shuffle=True, collate_fn=collate_fn)
	for sample in dataloader:
		datapoint = create_indicators(sample["SPY"]["open"])
		X = torch.stack([datapoint['macd'], datapoint['pct'], datapoint['var']], dim=1)
		Y = datapoint['output']
