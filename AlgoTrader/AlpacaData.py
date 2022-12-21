from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import alpaca_trade_api as tradeapi
import datetime
import pandas as pd
import numpy as np
import json
from transformers import pipeline
from AlgoTrader.Util import get_creds, trading_day_offset
from AlgoTrader.Logger import Logger


class AlpacaData:

	def __init__(self, symbols=["SPY"], start=1000, end=datetime.datetime.now(), news_data=True):
		self.start, self.end = self.calc_start_end(start, end)
		self.api_key = get_creds("ALPACA_API_KEY")
		self.secret_key = get_creds("ALPACA_SECRET_KEY")
		self.symbols = symbols
		self.get_news_data = news_data
		self.price_data = {symbol: None for symbol in symbols}
		self.raw_news_data = {symbol: None for symbol in symbols}
		self.news_data = {symbol: None for symbol in symbols}
		self.fetch_data()


	def calc_start_end(self, start, end):
		# If start/end are datetimes, then they are directly set
		# If one of them is an int, then it is that number of trading days before/after the other
		# For example, if start is 10 and end is datetime.datetime(2021,3,5), then start will be whatever date
		#		that makes the interval start-end 10 trading days long.
		# If times are not given, it defaults to 00:00 for the start date and 23:59 for the end date
		if isinstance(start, int):
			start = trading_day_offset(day=end, offset=-start)
		if isinstance(end, int):
			end = trading_day_offset(day=start, offset=end)
		if end.hour==0 and end.minute==0:
			end = end.replace(hour=23,minute=59)
		return start, end


	def get(self, symbol, datatype, start=None, end=None, length=None):
		start, end = self.calc_start_end(start, end)
		if start is not None:
			start = start.replace(tzinfo=self.price_data[symbol].index.tz)
		if end is not None:
			end = end.replace(tzinfo=self.price_data[symbol].index.tz)
		if isinstance(start, datetime.datetime):
			start = pd.Timestamp(start)
		if isinstance(end, datetime.datetime):
			end = pd.Timestamp(end)
		if datatype in ['open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']:
			data = self.price_data
		elif datatype in ['sentiment', 'news_count']:
			data = self.news_data
		else:
			raise ValueError(f"datatype {datatype} not recognised.")
		if start is None:
			if length is None:
				length = 1
			end = data[symbol].index.get_indexer([end], method='bfill')[0]+1
			start = max(0, end-length)
		if end is None:
			if length is None:
				end = data[symbol].index[-1]
			else:
				start = data[symbol].index.get_indexer([start], method='pad')[0]
				end = min(len(data[symbol])-1, start+length)
		return data[symbol][datatype][start:end]


	def quote(self, symbol, time):
		idx = self.price_data[symbol].index.get_indexer([pd.Timestamp(time.replace(tzinfo=self.price_data[symbol].index.tz))], method='bfill')[0]
		idx_time = self.price_data[symbol].index[idx]
		curr_time = pd.Timestamp(time)
		if curr_time.to_pydatetime().time() < datetime.time(19,50):
			datatype = 'open'
		else:
			datatype = 'close'
		return self.price_data[symbol][datatype][idx]


	def fetch_data(self):
		for symbol in self.symbols:
			is_crypto = "\\" in symbol
			price_bars = None
			news_bars = None
			if is_crypto:
				client = CryptoHistoricalDataClient()
				request_params = CryptoBarsRequest(
				                        symbol_or_symbols=symbol,
				                        timeframe=TimeFrame.Day,
				                        start=self.start,
				                        end=self.end,
				                 )
				price_bars = client.get_crypto_bars(request_params).df
			else:
				client = StockHistoricalDataClient(self.api_key, self.secret_key)
				request_params = StockBarsRequest(
				                        symbol_or_symbols=symbol,
				                        timeframe=TimeFrame.Day,
				                        start=self.start,
				                        end=self.end,
				                 )
				price_bars = client.get_stock_bars(request_params).df.droplevel("symbol")
			price_bars.index = pd.Index([d.replace(hour=20,minute=0) for d in price_bars.index])
			self.price_data[symbol] = price_bars
			if self.get_news_data:
				if is_crypto:
					symbol = "$" + symbol.split("/")[0]
				client = tradeapi.REST(self.api_key, self.secret_key, base_url="https://api.alpaca.markets", api_version='v2')
				news = client.get_news(symbol=symbol, start=self.start.strftime("%Y-%m-%d"), end=self.end.strftime("%Y-%m-%d"), sort=tradeapi.rest.Sort.Asc, limit=100000)
				headlines = pd.Series([article.headline for article in news])
				summaries = pd.Series([article.summary for article in news])
				dates = pd.Index([article.created_at for article in news], name='timestamp')
				news_bars = pd.DataFrame()
				news_bars["headline"] = headlines
				news_bars["summary"] = summaries
				news_bars.index = dates
				self.raw_news_data[symbol] = news_bars
				self.news_data[symbol] = self.sentiment(news_bars, price_bars.index)


	def sentiment(self, news_data, dates):
		analyser = pipeline("sentiment-analysis", model="ahmedrachid/FinancialBERT-Sentiment-Analysis")
		# mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis
		# ahmedrachid/FinancialBERT-Sentiment-Analysis
		dates = pd.Index([d.replace(hour=23, minute=59) for d in dates])
		score = np.zeros(len(dates))
		count = np.zeros(len(dates))
		idx = 0
		for date, article in news_data.iterrows():
			while date.date() > dates[idx].date():
				idx += 1
			if len(article["summary"]) == 0:
				continue
			result = analyser(article["summary"])[0]
			classification = 0
			if result['label'] == "positive":
				classification = 1
			elif result['label'] == "negative":
				classification = -1
			confidence = result['score']
			score[idx] += classification * confidence
			count[idx] += 1
		count_nonzero = count.copy()
		count_nonzero[count_nonzero==0] = 1
		score = score / count_nonzero
		sentiment = pd.DataFrame()
		sentiment.index = dates
		sentiment["sentiment"] = score
		sentiment["news_count"] = count
		return sentiment


if __name__ == '__main__':
	data = AlpacaData(start=10, symbols=["AMZN"], news_data=True)
	x = data.quote("AMZN", datetime.datetime(2022, 12, 19, 15, 0))
	breakpoint()

