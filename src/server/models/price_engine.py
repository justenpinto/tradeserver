import logging
import pandas as pd

from apis.alphavantage_api import AlphaVantageAPI
from apis.finnhub_api import FinnhubAPI


ALLOWED_INTERVALS = {1, 5, 15, 30, 60}


class PriceEngine:
    # TODO: Convert timestamps to UTC
    # TODO: Scheduler to fetch quotes - should not fetch quotes outside of market hours
    def __init__(self, tickers, interval, reload_file=None):
        self.prices = {}
        self.quote_schedule_map = {}

        for ticker in tickers:
            self.add_ticker(ticker)

        self.interval = None
        self.update_interval(interval)

        if reload_file:
            self.reload_price_from_file(reload_file)
        else:
            self.fetch_historical_prices()
            # TODO: add this back
            # self.output_price_history()

    def reset(self):
        tickers = self.prices.keys()
        self.prices = {}
        for ticker in tickers:
            self.add_ticker(ticker)
        self.fetch_historical_prices()

    def reload_price_from_file(self, reload_file):
        try:
            with open('./src/server/data/{}'.format(reload_file), 'r') as f:
                price_list = []
                for line in f.readlines()[1:]:
                    timestamp, price = line.rstrip('\n').split(',')
                    price_list.append({
                        'timestamp': timestamp,
                        'price': float(price)
                    })
        except FileNotFoundError:
            raise RuntimeError('Could not find reload file: {}'.format(reload_file))

        ticker = reload_file.split('_')[0].upper()
        self.add_ticker(ticker)
        df = pd.DataFrame(price_list, columns=['timestamp', 'price'])
        df.set_index('timestamp', inplace=True)
        self.prices[ticker] = df

    def update_interval(self, interval: int):
        if not interval:
            logging.error('No interval specified.')
        elif interval not in ALLOWED_INTERVALS:
            logging.error('{}m interval not allowed for historical API'.format(interval))
        else:
            self.interval = interval

    def add_ticker(self, ticker):
        if not ticker:
            logging.error('No ticker specified for addition.')
            return '2'

        ticker = ticker.upper()
        if ticker in self.prices:
            logging.warning('{} ticker already added.'.format(ticker))
        elif not AlphaVantageAPI.validate_ticker(ticker):
            logging.error('{} ticker is invalid, ignoring.'.format(ticker))
            return '2'
        else:
            self.prices[ticker] = pd.DataFrame()
        return '0'

    def remove_ticker(self, ticker):
        if not ticker:
            logging.error('No ticker specified for removal.')

        ticker = ticker.upper()
        if ticker not in self.prices:
            logging.warning('{} ticker does not exist in price map.'.format(ticker))
            return '2'
        else:
            del self.prices[ticker]
            return '0'

    def fetch_historical_prices(self, ticker=None):
        if not ticker:
            for ticker in self.prices.keys():
                self._add_historical_dataframe(ticker)
        else:
            self._add_historical_dataframe(ticker)

    def _add_historical_dataframe(self, ticker):
        df = pd.DataFrame(AlphaVantageAPI.fetch_historical_data(self.interval, ticker),
                          columns=['timestamp', 'price'])
        df.set_index('timestamp', inplace=True)
        self.prices[ticker] = df

    def fetch_quotes(self, ticker=None):
        if not ticker:
            for symbol in self.prices.keys():
                self._fetch_ticker_quote(symbol)
        else:
            self._fetch_ticker_quote(ticker)

    def _fetch_ticker_quote(self, ticker):
        if self.prices[ticker].empty:
            self.fetch_historical_prices(ticker)
        print('Fetching quote for: {}'.format(ticker))
        quote = FinnhubAPI.fetch_quote(ticker)

        df = self.prices[ticker]
        timestamp = quote['timestamp']

        if timestamp not in df.index:
            new_df = pd.DataFrame([{
                'timestamp': timestamp,
                'price': quote['price']
            }], columns=['timestamp', 'price'])
            new_df.set_index('timestamp', inplace=True)

            self.prices[ticker] = df.append(new_df)
        else:
            df.at[timestamp, 'price'] = quote['price']
            self.prices[ticker] = df

    def get_price_at_time(self, timestamp):
        price_data = {key: None for key in self.prices.keys()}
        for ticker, price_df in self.prices.items():
            if timestamp in price_df.index:
                price_data[ticker] = price_df.at[timestamp, 'price']
            elif timestamp == 'now':
                price_data[ticker] = price_df.price.iat[-1]

        output = []
        if any(price_data.values()):
            for ticker, price in price_data.items():
                if price:
                    output.append('{} {}'.format(ticker, price))
                else:
                    output.append('{} No Data'.format(ticker))
        else:
            output.append('Server has no data')

        return '\n'.join(output)

    def output_price_history(self):
        for ticker, price_df in self.prices.items():
            with open('./src/server/data/{}_price.csv'.format(ticker.lower()), 'w') as f:
                f.write('datetime,price\n')
                for timestamp, row in price_df.iterrows():
                    f.write('{},{}\n'.format(timestamp, row['price']))
