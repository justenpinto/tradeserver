import socket
import sys
import argparse
import atexit
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from models.price_engine import PriceEngine
from models.strategy import Strategy


def ceil_timestamp(ts, delta):
    return ts + (datetime.min - ts) % delta


def schedule_quote_job(minutes, price_engine, scheduler):
    start_date = ceil_timestamp(datetime.now(), timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:00')
    quote_job = scheduler.add_job(price_engine.fetch_quotes, 'interval', minutes=minutes, start_date=start_date)
    return quote_job


def server(port=None, reload_file=None, minutes=None, tickers=None, flip_signal=None):
    host = socket.gethostname()
    port = port
    s = socket.socket()
    s.bind((host, port))

    price_engine = PriceEngine(
        tickers=tickers,
        interval=minutes,
        reload_file=reload_file
    )

    scheduler = BackgroundScheduler()
    quote_job = schedule_quote_job(minutes, price_engine, scheduler)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    strategy = Strategy(price_engine, flip_signal=flip_signal)
    strategy.calculate_positions()
    strategy.calculate_pnl()

    print('Server started at: {}:{}'.format(host, port))

    s.listen(1)
    try:
        while True:
            print('Waiting for connection...')
            client_socket, address = s.accept()
            print('Connection from: {}'.format(address))

            while True:
                data = client_socket.recv(1024).decode(encoding='UTF-8')
                print('Received command: "{}"'.format(data))
                response = 'Command not recognized: "{}"'.format(data)

                if data.startswith('--price'):
                    try:
                        response = price_engine.get_price_at_time(data.split(' ')[1].strip())
                    except IndexError:
                        response = '1'
                elif data.startswith('--signal'):
                    try:
                        response = strategy.get_signal_at_time(data.split(' ')[1].strip())
                    except IndexError:
                        response = '1'
                elif data.startswith('--del_ticker'):
                    try:
                        ticker = data.split(' ')[1].strip().upper()
                        response = price_engine.remove_ticker(ticker)
                    except IndexError:
                        response = '1'
                elif data.startswith('--add_ticker'):
                    try:
                        ticker = data.split(' ')[1].strip().upper()
                        response = price_engine.add_ticker(ticker)
                        price_engine.fetch_historical_prices(ticker=ticker)
                    except IndexError:
                        response = '1'
                elif data == '--reset':
                    quote_job.remove()
                    price_engine.reset()
                    strategy.reset()
                    quote_job = schedule_quote_job(minutes, price_engine, scheduler)
                    response = '0'
                elif not data:
                    break

                client_socket.sendall(response.encode(encoding='UTF-8'))
    except KeyboardInterrupt:
        print('You pressed Ctrl+C!')
        s.close()
        sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the trading server.')
    parser.add_argument('--port', type=int, default=8000, help='Specify port to listen on.')
    parser.add_argument('--minutes', type=int, default=1, help='Frequency of the trading strategy in (5, 15, 30, 60).')
    parser.add_argument('--reload', type=str, help='Reload historical price from file.')
    parser.add_argument('--tickers', nargs='+', help='Tickers to start with. Max of 3.')
    parser.add_argument('--flip_signal', action='store_true', help='Invert the strategy if you wish.')

    args = parser.parse_args()
    if args.minutes and args.minutes not in {1, 5, 15, 30, 60}:
        print('Invalid minutes interval, defaulting to 5 minutes.')
        args.minutes = 5
    if args.tickers and len(args.tickers) > 3:
        print('Too many tickers specified. Trimming list to: {}'.format(args.tickers[:3]))
        args.tickers = args.tickers[:3]
    if not args.tickers:
        args.tickers = ['AAPL']

    server(
        port=args.port,
        reload_file=args.reload,
        minutes=args.minutes,
        tickers=args.tickers,
        flip_signal=args.flip_signal
    )
