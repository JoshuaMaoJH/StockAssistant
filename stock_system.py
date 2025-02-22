# Stock Market Analysis System
# This system provides functionality for downloading, analyzing, and visualizing Chinese A-share stock data
# Author: Joshua Mao
# Date: 02-22-2025
# Version: 0.0.6

import akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from tqdm import tqdm
import os
from datetime import datetime
import matplotlib.pyplot as plt
import logging


class StockDataError(Exception):
    """Custom exception for stock data related errors"""
    pass


class StockAnalysisSystem:
    def __init__(self, downloader):
        self.downloader = downloader

    def is_stock_limit_up(self, stock_code, day):
        """检查股票是否涨停"""
        try:
            close_price = self.get_closing_price(stock_code, day)
            open_price = self.get_opening_price(stock_code, day)
            increase = self.get_increase(stock_code, day)

            # 检查返回值
            if isinstance(close_price, Exception) or isinstance(open_price, Exception) or isinstance(increase,
                                                                                                     Exception):
                return False

            return float(close_price) >= float(open_price) and float(increase) >= 0
        except Exception as e:
            logging.error(f"Error checking limit up for {stock_code}: {str(e)}")
            return False

    def get_increase(self, stock_code, day):
        """获取股票某日的涨跌幅"""
        try:
            close_price = self.get_closing_price(stock_code, day)
            open_price = self.get_opening_price(stock_code, day)

            # 检查是否返回了异常
            if isinstance(close_price, Exception) or isinstance(open_price, Exception):
                return 0

            return float(close_price) - float(open_price)
        except Exception as e:
            logging.error(f"Error calculating increase for {stock_code}: {str(e)}")
            return 0

    def get_closing_price(self, stock_code, day):
        """获取收盘价"""
        try:
            # 获取当天数据
            day_data = self.get_date_data(stock_code, day)
            if isinstance(day_data, Exception):
                logging.error(f"Error getting data for {stock_code}: {day_data}")
                return None

            # 直接返回收盘价，因为day_data['收盘']已经是具体的值
            return float(day_data['收盘'])
        except Exception as e:
            logging.error(f"Error getting closing price for {stock_code}: {e}")
            return None

    def get_opening_price(self, stock_code, day):
        """获取开盘价"""
        try:
            day_data = self.get_date_data(stock_code, day)
            if isinstance(day_data, Exception):
                logging.error(f"Error getting data for {stock_code}: {day_data}")
                return None

            # 直接返回开盘价
            return float(day_data['开盘'])
        except Exception as e:
            logging.error(f"Error getting opening price for {stock_code}: {e}")
            return None

    def get_date_data(self, stock_code, day='2022-01-01'):
        """获取指定日期的股票数据"""
        try:
            stock_data = self.downloader.read_csv(
                f'{self.downloader.folder}/{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv')
            stock_data.index = stock_data['日期']
            return stock_data.loc[day]
        except Exception as e:
            logging.error(f"Error getting date data for {stock_code}: {e}")
            return e

    def analyze_stock(self, stock_code):
        """分析单个股票"""
        try:
            # 读取数据
            file_path = f'{self.downloader.folder}/{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv'
            stock_data = self.downloader.read_csv(file_path)

            # 获取最近的交易日数据
            last_day_date = str(stock_data['日期'].values[-2])
            this_day_date = str(stock_data['日期'].values[-1])

            # 获取价格数据并检查有效性
            last_close = self.get_closing_price(stock_code, last_day_date)
            this_close = self.get_closing_price(stock_code, this_day_date)

            # 如果任何价格数据无效，返回False
            if last_close is None or this_close is None:
                return False, {}

            # 计算涨跌幅
            increase_rate = ((this_close - last_close) / last_close) * 100

            # 获取成交量数据
            try:
                last_volume = float(stock_data['成交量'].values[-2])
                this_volume = float(stock_data['成交量'].values[-1])
                is_volume_up = this_volume > last_volume
            except (IndexError, ValueError, TypeError):
                is_volume_up = False

            # 判断趋势
            is_uptrend = this_close > last_close

            # 返回分析结果
            analysis_result = {
                'date': this_day_date,
                'stock_name': self.downloader.stocks[stock_code],
                'close_price': this_close,
                'increase_rate': round(increase_rate, 2),
                'is_uptrend': is_uptrend,
                'is_volume_up': is_volume_up
            }

            # 定义筛选条件
            is_interesting = (
                    is_uptrend and
                    is_volume_up and
                    increase_rate > 2.0
            )

            is_interesting = (self.get_increase(stock_code, this_day_date) > self.get_increase(stock_code, last_day_date)
                              and self.is_stock_limit_up(stock_code, this_day_date) and self.is_stock_limit_up(stock_code, last_day_date)
                              and is_interesting)

            return is_interesting, analysis_result

        except Exception as e:
            logging.error(f"Error analyzing stock {stock_code}: {e}")
            return False, {}

    def analyze_all_stocks(self):
        """分析所有股票并返回符合条件的结果"""
        results = {}
        interesting_stocks = {}

        with ThreadPoolExecutor(max_workers=self.downloader.max_workers) as executor:
            with tqdm(total=len(self.downloader.stocks), desc='ANALYSIS PROGRESS', unit='stock(s)') as pbar:
                futures = {
                    executor.submit(self.analyze_stock, stock_code): stock_code
                    for stock_code in self.downloader.stocks.keys()
                }

                for future in as_completed(futures):
                    stock_code = futures[future]
                    try:
                        is_interesting, analysis = future.result()
                        if is_interesting:
                            interesting_stocks[stock_code] = analysis
                    except Exception as e:
                        logging.error(f"Error processing {stock_code}: {e}")
                    pbar.update(1)

        return interesting_stocks


class StockDownloader:
    """
    A class for downloading and managing stock data from Chinese A-share market.

    This class provides functionality to:
    - Download stock data for all A-shares
    - Save stock data to CSV files
    - Manage and verify downloaded data
    """

    def __init__(self):
        """
        Initialize the StockDownloader with default parameters:
        - Daily frequency
        - Start date from 2022-01-01
        - End date as current date
        - Maximum 10 concurrent download threads
        """
        self.frequency = 'daily'
        self.start_date = '20220101'
        self.end_date = datetime.now().strftime('%Y%m%d')
        self.max_workers = 10
        self.stocks = self.get_all_stocks()
        self.folder = 'stock_data'

    def read_csv(self, file_path):
        return pd.read_csv(file_path)

    def have_folder(self, folder):
        return os.path.exists(folder)

    def make_folder(self, folder):
        os.makedirs(folder)

    def get_all_stocks(self):
        """
        Retrieve a list of all available A-share stocks.

        Returns:
            dict: A dictionary mapping stock codes to stock names
        """
        try:
            # Get list of all A-shares
            stock_info_df = ak.stock_info_a_code_name()
            # Return dictionary of code:name pairs
            return dict(zip(stock_info_df['code'], stock_info_df['name']))
        except Exception as e:
            print(f"An error occurred while getting the stock list: {str(e)}")
            return {}

    def get_stock_data(self, frequency, stock_code, start_date, end_date):
        """
        Download historical data for a single stock.

        Args:
            frequency (str): Data frequency ('daily', 'weekly', etc.)
            stock_code (str): Stock code
            start_date (str): Start date in format 'YYYYMMDD'
            end_date (str): End date in format 'YYYYMMDD'

        Returns:
            pandas.DataFrame: Historical stock data
        """
        try:
            stock_data = ak.stock_zh_a_hist(symbol=stock_code,
                                            period=frequency,
                                            start_date=start_date,
                                            end_date=end_date,
                                            adjust="qfq")
            return stock_data
        except Exception as e:
            return e

    def download_stock_to_file(self, stock_data, stock_code, stock_name, start_date, end_date):
        """
        Save downloaded stock data to a CSV file.

        Args:
            stock_data (pandas.DataFrame): Stock data to save
            stock_code (str): Stock code
            stock_name (str): Stock name
            start_date (str): Start date
            end_date (str): End date
        """
        if not self.have_folder(self.folder):
            self.make_folder(self.folder)

        try:
            filepath = os.path.join(self.folder, f'{stock_code}_{stock_name}_{start_date}_{end_date}.csv')

            # Verify data completeness
            if not self.check_stock_data_files(stock_data, stock_code):
                return

            stock_data.to_csv(filepath, index=False, encoding='utf-8')
        except Exception as e:
            return e

    def download_single_stock(self, stock_code):
        """
        Download and save data for a single stock.

        Args:
            stock_code (str): Stock code to download
        """
        stock_data = self.get_stock_data(self.frequency, stock_code, self.start_date, self.end_date)
        self.download_stock_to_file(stock_data, stock_code, self.stocks[stock_code], self.start_date, self.end_date)

    def download_all_stocks(self):
        """
        Download data for all stocks using multiple threads.
        Shows a progress bar during download.
        """
        with ThreadPoolExecutor(self.max_workers) as executor:
            with tqdm(total=len(self.stocks), desc='DOWNLOAD PROGRESS', unit='stock(s)') as pbar:
                futures = [executor.submit(self.download_single_stock, stock_code) for stock_code in self.stocks.keys()]
                for future in as_completed(futures):
                    pbar.update(1)

    def check_size_of_all_stock_data(self):
        """
        Calculate total size of downloaded stock data files.

        Returns:
            tuple: (files_list, size_in_bytes, size_in_KB, size_in_MB, size_in_GB)
        """
        files = os.listdir(self.folder)
        total_size = 0
        for file in files:
            total_size += os.path.getsize(os.path.join(self.folder, file))
        B = total_size
        KB = B / 1024
        MB = KB / 1024
        GB = MB / 1024
        return files, round(B, 2), round(KB, 2), round(MB, 2), round(GB, 2)

    def check_stock_data_files(self, stock_data, stock_code):
        """
        Verify completeness and validity of stock data, including ST/delisting check.

        Args:
            stock_data (pandas.DataFrame): Stock data to verify
            stock_code (str): Stock code to check against ST/delisting status

        Returns:
            bool: True if data is complete and valid (not ST/delisted), False otherwise
        """
        if stock_data is None or stock_data.empty:
            return False

        check_columns = [
            "日期",  # Date
            "开盘",  # Open
            "收盘",  # Close
            "最高",  # High
            "最低",  # Low
            "成交量",  # Volume
            "成交额",  # Amount
            "振幅",  # Amplitude
            "涨跌幅",  # Change Ratio
            "涨跌额",  # Change Amount
            "换手率",  # Turnover Rate
        ]

        # Check for required columns and no null values
        for column in check_columns:
            if column not in stock_data.columns:
                return False
            if stock_data[column].isnull().sum() > 0:
                return False

        # Check if it's an ST stock or delisted stock using the stock name from self.stocks
        stock_name = self.stocks.get(stock_code, "")
        if 'ST' in stock_name or '退' in stock_name:
            return False

        return True


class StockLineDrawer:
    """
    A class for creating various stock charts and visualizations.
    Supports candlestick charts, moving averages, and trend analysis.
    """

    def __init__(self, downloader):
        """
        Initialize the StockLineDrawer with a StockDownloader instance.

        Args:
            downloader (StockDownloader): Instance of StockDownloader
        """
        self.downloader = downloader
        self.folder = self.downloader.folder

    def plt_init(self):
        """
        Initialize matplotlib settings for Chinese character support.
        """
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

    def draw_single_stock_kline(self, stock_code):
        """
        Draw a candlestick chart for a single stock.

        Args:
            stock_code (str): Stock code to visualize
        """
        try:
            self.plt_init()
            filepath = os.path.join(self.folder,
                                    f'{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv')
            stock_data = pd.read_csv(filepath, encoding='utf-8')

            # Create figure and axis
            fig, ax = plt.subplots(figsize=(15, 8))
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])

            # Set colors for candlesticks (red for up, green for down)
            colors = ['red' if close >= open_ else 'green'
                      for close, open_ in zip(stock_data['收盘'], stock_data['开盘'])]

            # Plot candlesticks
            for idx, (date, open_, close, high, low) in enumerate(zip(
                    stock_data['日期'], stock_data['开盘'],
                    stock_data['收盘'], stock_data['最高'], stock_data['最低'])):
                # Draw candle body
                ax.add_patch(plt.Rectangle(
                    (idx - 0.25, min(open_, close)),
                    0.5, abs(close - open_),
                    fill=True, color=colors[idx]
                ))
                # Draw candle wicks
                ax.plot([idx, idx], [low, high], color=colors[idx], linewidth=1)

            # Customize plot appearance
            plt.title(f"{stock_code} {self.downloader.stocks[stock_code]} K线图")
            plt.xlabel('日期')
            plt.ylabel('价格')

            # Set x-axis labels
            tick_positions = range(0, len(stock_data), len(stock_data) // 10)
            tick_labels = stock_data['日期'].iloc[tick_positions].dt.strftime('%Y-%m-%d')
            plt.xticks(tick_positions, tick_labels, rotation=45)

            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.show()
            plt.close()

        except Exception as e:
            return e

    def draw_single_stock_ma(self, ma_days, stock_code):
        """
        Draw moving average lines for a single stock.

        Args:
            ma_days (list): List of days for moving averages (e.g., [5,10,20])
            stock_code (str): Stock code to visualize
        """
        try:
            self.plt_init()
            filepath = os.path.join(self.folder,
                                    f'{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv')
            stock_data = pd.read_csv(filepath, encoding='utf-8')
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])

            fig, ax = plt.subplots(figsize=(15, 8))

            # Plot moving averages with different colors
            colors = ['red', 'blue', 'green', 'purple', 'orange']
            for i, days in enumerate(ma_days):
                ma = stock_data['收盘'].rolling(window=days).mean()
                ax.plot(stock_data['日期'], ma,
                        label=f'{days}日均线',
                        color=colors[i % len(colors)],
                        alpha=0.7)

            plt.title(f"{stock_code} {self.downloader.stocks[stock_code]} 均线图")
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.show()
            plt.close()

        except Exception as e:
            return e

    def draw_single_stock_trends(self, stock_code):
        """
        Draw trend analysis chart combining closing prices and moving averages.

        Args:
            stock_code (str): Stock code to visualize
        """
        try:
            self.plt_init()
            filepath = os.path.join(self.folder,
                                    f'{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv')
            stock_data = pd.read_csv(filepath, encoding='utf-8')
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])

            fig, ax = plt.subplots(figsize=(15, 8))

            # Plot closing price
            ax.plot(stock_data['日期'], stock_data['收盘'], label='收盘价', color='black')

            # Add moving averages
            ma_days = [5, 10, 20]
            colors = ['red', 'blue', 'green', 'purple', 'orange']
            for i, days in enumerate(ma_days):
                ma = stock_data['收盘'].rolling(window=days).mean()
                ax.plot(stock_data['日期'], ma,
                        label=f'{days}日均线',
                        color=colors[i % len(colors)],
                        alpha=0.7)

            plt.title(f"{stock_code} {self.downloader.stocks[stock_code]} 趋势图")
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.show()
            plt.close()

        except Exception as e:
            return e


class StockSystem:
    """
    Main class that integrates StockDownloader and StockLineDrawer functionality.
    Provides a unified interface for the stock analysis system.
    """

    def __init__(self):
        """
        Initialize the stock system by creating instances of StockDownloader and StockLineDrawer.
        """
        self.downloader = StockDownloader()
        self.line_drawer = StockLineDrawer(self.downloader)
        self.analysis_system = StockAnalysisSystem(self.downloader)


# Usage Guide
"""
How to use the Stock Analysis System:

1. Basic Setup:
   ```python
   # Create a StockSystem instance
   stock_system = StockSystem()
   ```

2. Download Stock Data:
   ```python
   # Download data for all stocks
   stock_system.downloader.download_all_stocks()

   # Check downloaded data size
   files, b, kb, mb, gb = stock_system.downloader.check_size_of_all_stock_data()
   print(f"Total data size: {mb:.2f} MB")
   ```

3. Visualize Stock Data:
   ```python
   # Draw candlestick chart
   stock_system.lineDrawer.draw_single_stock_kline('000001')  # Replace with desired stock code

   # Draw moving averages
   stock_system.lineDrawer.draw_single_stock_ma([5,10,20,30], '000001')  # Customize MA periods

   # Draw trend analysis
   stock_system.lineDrawer.draw_single_stock_trends('000001')
   ```

4. Customization:
   - Modify date range: Adjust start_date and end_date in StockDownloader.__init__()
   - Change data frequency: Modify frequency in StockDownloader.__init__()
   - Adjust concurrent downloads: Modify max_workers in StockDownloader.__init__()

Note: This system requires the following packages:
- akshare
- pandas
- matplotlib
- tqdm
"""

if __name__ == '__main__':
    print("=== Stock Analysis Example ===")

    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    stock_system = StockSystem()
    stock_system.downloader.max_workers = 25
    stock_system.downloader.start_date = '20220101'
    stock_system.downloader.end_date = '20250217'

    # 下载数据
    print("Downloading stock data...")
    stock_system.downloader.download_all_stocks()

    # 分析股票
    print("\nAnalyzing stocks...")
    interesting_stocks = stock_system.analysis_system.analyze_all_stocks()

    # 输出分析结果
    print("\n=== Analysis Results ===")
    if interesting_stocks:
        print(f"Found {len(interesting_stocks)} interesting stocks:")
        for stock_code, analysis in interesting_stocks.items():
            print(f"\n{analysis['stock_name']} ({stock_code}):")
            print(f"  日期: {analysis['date']}")
            print(f"  收盘价: {analysis['close_price']:.2f}")
            print(f"  涨跌幅: {analysis['increase_rate']}%")
            print(f"  成交量增加: {'是' if analysis['is_volume_up'] else '否'}")
    else:
        print("No stocks matching the criteria found.")
