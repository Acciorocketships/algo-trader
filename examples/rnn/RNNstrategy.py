from AlgoTrader.Algo import Algo
from AlgoTrader.Manager import Manager
from AlgoTrader.AlpacaData import AlpacaData
from Model import MarketPredictor, create_indicators
import datetime
import torch

class RNNstrategy(Algo):

	def init(self):
		self.set_schedule(["30 9 * * *"])
		self.predictor = MarketPredictor(recurrent=True)
		load_model(self.predictor, 'model_params.pt')
		self.predictor.eval()
		self.last_prediction = None

	def run(self):
		hist = self.get_data("SPY", days=40)
		if self.data.timeframe == 'minute':
			hist = hist.at_time(datetime.time(9,30))
		prices = torch.tensor(hist).unsqueeze(0)
		indicators = create_indicators(prices, window=18, series=True)
		X = torch.stack([indicators['pct'], indicators['macd1'], indicators['macd2'],  indicators['var']], dim=-1)
		predictions = self.predictor(X)[0,:]
		increase_prob = predictions[2] - predictions[0]
		if increase_prob > 0.4:
			self.order_target_percent("SPY", 1.0, stop=-0.8)
		else:
			self.order_target_percent("SPY", 0.0)
			self.cancel_orders("SPY")
		# Report
		pct = 100 * (prices[0,-1] / prices[0,-2] - 1)
		# print('Pct Change: {pct}   Predictions: {pred}'.format(pct=pct, pred=self.last_prediction))
		self.last_prediction = predictions.tolist()


def load_model(model, path):
	try:
		fp = open(path, 'rb')
		print('Loaded Model ' + path)
	except:
		return
	model_dict = torch.load(fp)
	model.load_state_dict(model_dict)

if __name__ == '__main__':
	data = AlpacaData(start=datetime.datetime(2016,10,1), end=datetime.datetime(2021,4,15), timeframe='day', symbols=["SPY"], live=False)
	manager = Manager(data)
	algo = RNNstrategy()
	manager.add_algo(algo)
	manager.backtest(start=datetime.datetime(2017,1,1), end=datetime.datetime(2021,4,15))