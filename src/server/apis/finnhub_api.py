import logging
import requests
from datetime import datetime

API_KEY = 'bri49ofrh5rep8a5h4q0'
QUERY_URL = 'https://finnhub.io/api/v1/quote?token={}&'.format(API_KEY)


class FinnhubAPI:
    @staticmethod
    def fetch_quote(ticker):
        quote = FinnhubAPI.request_data(ticker)
        if quote:
            return {
                'price': float(quote['c']),
                'timestamp': datetime.fromtimestamp(quote['t']).strftime('%Y-%m-%d-%H:%M')
            }
        else:
            return {}

    @staticmethod
    def request_data(ticker):
        r = requests.get('{}symbol={}'.format(QUERY_URL, ticker), verify=False)

        if r.status_code != 200:
            logging.error('Error fetching {} quote, status code {}: {}'.format(ticker, r.status_code, r.text))
            return {}

        return r.json()
