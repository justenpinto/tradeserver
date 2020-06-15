import logging
import requests
from datetime import datetime

API_KEY = 'AKOCV5JF4J0P8MEC'
QUERY_URL = 'https://www.alphavantage.co/query?apikey={}&'.format(API_KEY)


class AlphaVantageAPI:
    @staticmethod
    def fetch_historical_data(interval, ticker):
        request_data = AlphaVantageAPI.request_data(ticker, interval='{}min'.format(interval))
        ticker_data = request_data.get('Time Series ({}min)'.format(interval), {})
        if not ticker_data:
            return {}
        price_data = []
        for timestamp in sorted(ticker_data.keys()):
            timestamp_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            price_dict = {
                'timestamp': timestamp_dt.strftime('%Y-%m-%d-%H:%M'),
                'price': float(ticker_data[timestamp]['4. close'])
            }
            price_data.append(price_dict)

        return price_data

    @staticmethod
    def validate_ticker(ticker):
        return 'Error Message' not in AlphaVantageAPI.request_data(ticker, function='GLOBAL_QUOTE')

    @staticmethod
    def request_data(ticker, function=None, interval=None):
        function = function or 'TIME_SERIES_INTRADAY'
        interval = interval or '60min'
        r = requests.get('{}function={}&outputsize=full&symbol={}&interval={}'.format(
            QUERY_URL, function, ticker, interval
        ), verify=False)

        if r.status_code != 200:
            logging.error('Error fetching {} historical data, status code: {}. Error: {}'.format(ticker, r.status_code, r.text))
            return {}

        return r.json()
