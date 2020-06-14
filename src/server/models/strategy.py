import math
import pandas as pd

HOURS_IN_TRADING_DAY = 6.5
MINUTES_PER_HOUR = 60


class Strategy:
    def __init__(self, price_engine, flip_signal=False):
        self.price_engine = price_engine
        self.strategy_data_map = {}
        self.flip_signal = flip_signal

    def reset(self):
        self.strategy_data_map = {}
        self.calculate_positions()
        self.calculate_pnl()

    def remove_ticker(self, ticker):
        if ticker in self.strategy_data_map:
            del self.strategy_data_map[ticker]

    def calculate_positions(self):
        for ticker, price_df in self.price_engine.prices.items():
            self.strategy_data_map[ticker] = self.get_rolling_moving_averages(price_df)

        for ticker, strategy_df in self.strategy_data_map.items():
            signal_data = []
            position_data = []
            current_position_data = []

            for timestamp, row in strategy_df.iterrows():
                if pd.isna(row['avg']):
                    signal_data.append(0)
                    position_data.append(0)
                    current_position_data.append(0)
                else:
                    price, s_avg, s_sigma = row
                    current_position_data.append(position_data[-1])
                    if price > s_avg + s_sigma:
                        position_data.append(position_data[-1] + (-1 if self.flip_signal else 1))
                        signal_data.append(1)
                    elif price < s_avg - s_sigma:
                        position_data.append(position_data[-1] - (-1 if self.flip_signal else 1))
                        signal_data.append(-1)
                    else:
                        position_data.append(position_data[-1])
                        signal_data.append(0)

            strategy_df['signal'] = signal_data
            strategy_df['current_position'] = current_position_data

    def calculate_pnl(self):
        for ticker, strategy_df in self.strategy_data_map.items():
            returns = strategy_df['price'].pct_change()
            positions = strategy_df['current_position']
            strategy_df['pnl'] = positions * returns
        # TODO: add back
        # self.output_results()

    def get_rolling_moving_averages(self, price_df):
        rma_df = pd.DataFrame()
        window = int(math.ceil(HOURS_IN_TRADING_DAY / (self.price_engine.interval / MINUTES_PER_HOUR))) + 1
        rma_df['price'] = price_df.iloc[:, 0]
        rma_df['avg'] = price_df.iloc[:, 0].rolling(window=window).mean()
        rma_df['sigma'] = price_df.iloc[:, 0].rolling(window=window).std()
        return rma_df

    def get_signal_at_time(self, timestamp):
        signal_data = {key: None for key in self.strategy_data_map.keys()}
        for ticker, signal_df in self.strategy_data_map.items():
            if timestamp in signal_df.index:
                signal_data[ticker] = signal_df.at[timestamp, 'signal']
            elif timestamp == 'now':
                signal_data[ticker] = signal_df.signal.iat[-1]

        output = []
        if not all(s is None for s in signal_data.values()):
            for ticker, signal in signal_data.items():
                if signal is not None:
                    output.append('{} {}'.format(ticker, signal))
                else:
                    output.append('{} No Data'.format(ticker))
        else:
            output.append('Server has no data')

        return '\n'.join(output)

    def output_results(self):
        for ticker, strategy_df in self.strategy_data_map.items():
            with open('./src/server/data/{}_result.csv'.format(ticker.lower()), 'w') as f:
                f.write('datetime,price,signal,position,pnl\n')
                for timestamp, row in strategy_df.iterrows():
                    f.write('{},{},{},{},{}\n'.format(timestamp, row['price'], row['signal'], row['current_position'], row['pnl']))
