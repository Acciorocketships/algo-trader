from setuptools import setup
from setuptools import find_packages

setup(name = 'AlgoTrader',
      version = '0.0.1',
      packages = find_packages(),
      install_requires = ['pandas', 'APScheduler', 'pytz', 'ta', 'QuantStats', 'alpaca-trade-api', 'pandas-market-calendars', 'numpy', 'torch'],
      author = 'Ryan Kortvelesy',
      author_email = 'rk627@cam.ac.uk',
      description = 'An algorithmic trading library, enabling the development of strategies, backtesting, and live deployment with Alpaca.',
)