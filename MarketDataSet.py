from torch.utils.data import DataSet

class MarketDataSet(DataSet):

	def __init__(self, dataobj, hist=1, datatypes=['open']):
		self.dataobj = dataobj
		self.hist = hist
		self.datatypes = datatypes


	def __len__(self):
		return len(self.dataobj.get(self.dataobj.symbols[0])) - self.hist + 1


	def __getitem__(self, idx):
		symbols = dataobj.symbols
		datapoint = {}
		datapoint['t'] = torch.tensor(dataobj.data[symbols[0]].index.values)[idx:idx+hist-1]
		for symbol in symbols:
			datapoint[symbol] = {}
			df = dataobj.get(symbol)
			for datatype in self.datatypes:
				datapoint[symbol][datatype] = torch.tensor(df[datatype].values)[idx:idx+hist-1]
		return datapoint


def collate_fn(sample_list):
	datapoints = {'t': []}
	for sample in sample_list:
		datapoints['t'].append(sample['t'])
		for symbol in sample.keys():
			if symbol != 't':
				if symbol not in datapoints:
					datapoints[symbol] = {datatype: [] for datatype in sample[symbol].keys()}
				for datatype, data in sample[symbol].items():
					datapoints[symbol][datatype].append(data)
	tensors = {}
	tensors['t'] = torch.cat(datapoints['t'], dim=0)
	for symbol in datapoints.keys():
		if symbol != 't':
			if symbol not in tensors:
				tensors[symbol] = {}
			for datatype, data in datapoints[symbol].items()
				tensors[symbol][datatype] = torch.cat(data, dim=0)
	return tensors
