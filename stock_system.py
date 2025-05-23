# Stock Market Analysis System
# This system provides functionality for downloading, analyzing, and visualizing Chinese A-share stock data
# Author: Joshua Mao
# Date: 02-22-2025
# Version: 0.1.4

import akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from tqdm import tqdm
import os
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import logging


class StockDataError(Exception):
    """Custom exception for stock data related errors"""
    pass


class StockAnalysisSystem:
    def __init__(self, downloader):
        self.downloader = downloader
        self.folder = 'analysis_results'

    def get_analyze_top(self, interesting_stocks, top_n=5):
        """获取前n个分析结果"""
        if interesting_stocks:
            # 按概率降序排序
            sorted_stocks = sorted(interesting_stocks.items(), key=lambda x: x[1]['probability'], reverse=True)
            return dict(sorted_stocks[:top_n])
        return {}

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

    def get_ma(self, stock_code, ma_days, day='2022-01-04'):
        """
        获取股票的均线数据

        Args:
            stock_code (str): 股票代码
            ma_days (list): 需要计算的均线天数列表，如 [5, 10, 20]
            day (str): 查询日期，格式为 'YYYY-MM-DD'

        Returns:
            dict: 包含各个周期均线值的字典，格式如 {'5': 10.5, '10': 10.2, '20': 10.0}
        """
        try:
            # 构建文件路径
            file_path = f'{self.downloader.folder}/{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv'

            # 读取数据
            stock_data = self.downloader.read_csv(file_path)
            if stock_data is None or stock_data.empty:
                logging.error(f"No data found for stock {stock_code}")
                return {str(d): None for d in ma_days}

            # 确保日期列格式正确
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            target_date = pd.to_datetime(day)

            # 按日期排序并重置索引
            stock_data = stock_data.sort_values('日期').reset_index(drop=True)

            # 获取目标日期之前的所有数据
            data_until_target = stock_data[stock_data['日期'] <= target_date]

            if data_until_target.empty:
                logging.error(f"No data found before or on date {day}")
                return {str(d): None for d in ma_days}

            # 计算各周期均线
            ma_values = {}
            for d in ma_days:
                if len(data_until_target) >= d:
                    # 使用最后d天的数据计算均线
                    ma_data = data_until_target['收盘'].tail(d).mean()
                    ma_values[str(d)] = round(float(ma_data), 2)
                else:
                    logging.warning(
                        f"Insufficient data for {d}-day MA calculation. Only {len(data_until_target)} days available.")
                    ma_values[str(d)] = None

            return ma_values

        except Exception as e:
            logging.error(f"Error calculating MA for {stock_code}: {str(e)}")
            return {str(d): None for d in ma_days}

    def predict_limit_up_probability(self, stock_code: str) -> dict:
        """
        预测股票涨停概率

        Args:
            stock_code (str): 股票代码

        Returns:
            dict: 包含涨停概率和详细指标的字典
        """
        try:
            # 获取股票数据
            file_path = f'{self.downloader.folder}/{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv'
            stock_data = self.downloader.read_csv(file_path)

            if stock_data is None or stock_data.empty:
                return {"probability": 0, "status": "数据不足"}

            # 获取最近两天的数据
            last_two_days = stock_data.tail(2)
            if len(last_two_days) < 2:
                return {"probability": 0, "status": "数据不足"}

            this_day = last_two_days.iloc[-1]
            last_day = last_two_days.iloc[-2]

            # 1. 成交量比值评分 (30%)
            volume_ratio = float(this_day['成交额']) / float(last_day['成交额'])
            volume_score = (100 if 1.8 <= volume_ratio <= 2.2 else
                            80 if (1.5 <= volume_ratio < 1.8 or 2.2 < volume_ratio <= 2.5) else 40)

            # 2. 价格变动评分 (30%)
            price_change = ((float(this_day['收盘']) - float(last_day['收盘'])) / float(last_day['收盘'])) * 100
            price_score = (100 if 2 <= price_change <= 4 else
                           80 if (1 <= price_change < 2 or 4 < price_change <= 5) else 40)

            # 3. 换手率评分 (40%)
            turnover = float(this_day['换手率'])
            turnover_score = (100 if turnover >= 4 else
                              80 if 2 <= turnover < 4 else 40)

            # 4. 计算均线趋势系数
            stock_data['MA5'] = stock_data['收盘'].astype(float).rolling(window=5).mean()
            stock_data['MA10'] = stock_data['收盘'].astype(float).rolling(window=10).mean()
            latest_ma = stock_data.iloc[-1]
            trend_coef = (1.2 if latest_ma['MA5'] > latest_ma['MA10'] else
                          0.8 if latest_ma['MA5'] < latest_ma['MA10'] else 1.0)

            # 计算最终得分
            final_score = (volume_score * 0.3 +
                           price_score * 0.3 +
                           turnover_score * 0.4) * trend_coef

            probability = min(round(final_score, 2), 100)

            # 返回结果
            return {
                "probability": probability,
                "risk_level": ("极强" if probability >= 85 else
                               "强烈" if probability >= 70 else
                               "中等" if probability >= 50 else "较弱"),
                "indicators": {
                    "volume_ratio": round(volume_ratio, 2),
                    "price_change": round(price_change, 2),
                    "turnover": round(turnover, 2),
                    "ma5": round(float(latest_ma['MA5']), 2),
                    "ma10": round(float(latest_ma['MA10']), 2)
                },
                "scores": {
                    "volume_score": volume_score,
                    "price_score": price_score,
                    "turnover_score": turnover_score,
                    "trend_coef": trend_coef
                },
                "date": this_day['日期'],
                "stock_name": self.downloader.stocks[stock_code],
                "status": "success"
            }

        except Exception as e:
            logging.error(f"Error calculating limit up probability for {stock_code}: {str(e)}")
            return {
                "probability": 0,
                "status": f"error: {str(e)}"
            }

    def have_file(self, file_path):
        if os.path.exists(file_path):
            return True
        return False

    def save_analysis_result(self, interesting_stocks):
        """保存分析结果"""
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        for stock_code, analysis in interesting_stocks.items():
            file_path = f'{self.folder}/{stock_code}_{analysis["date"]}.txt'
            with open(file_path, 'w', encoding='utf-8') as f:
                # 先判断是不是返回正确
                if not analysis['status'] == 'success':
                    f.write(f"Error: {analysis['status']}")
                    continue
                f.write(f"Stock Name: {analysis['stock_name']}\n")
                f.write(f"Date: {analysis['date']}\n")
                f.write(f"Probability: {analysis['probability']}%\n")
                f.write(f"Risk Level: {analysis['risk_level']}\n\n")
                f.write("Indicators:\n")
                f.write(f"  Volume Ratio: {analysis['indicators']['volume_ratio']}\n")
                f.write(f"  Price Change: {analysis['indicators']['price_change']}\n")
                f.write(f"  Turnover Rate: {analysis['indicators']['turnover']}\n")
                f.write(f"  MA5: {analysis['indicators']['ma5']}\n")
                f.write(f"  MA10: {analysis['indicators']['ma10']}\n\n")
                f.write("Scores:\n")
                f.write(f"  Volume Score: {analysis['scores']['volume_score']}\n")
                f.write(f"  Price Score: {analysis['scores']['price_score']}\n")
                f.write(f"  Turnover Score: {analysis['scores']['turnover_score']}\n")
                f.write(f"  Trend Coefficient: {analysis['scores']['trend_coef']}\n")

    def analyze_stock(self, stock_code):
        """分析单个股票"""
        try:
            # 读取数据
            file_path = f'{self.downloader.folder}/{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv'
            if not self.have_file(file_path):
                return False, {}
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

            # 返回分析结果
            analysis_result = self.predict_limit_up_probability(stock_code)

            # 定义筛选条件
            is_interesting = analysis_result['probability'] >= 70

            return is_interesting, analysis_result

        except Exception as e:
            logging.error(f"Error analyzing stock {stock_code}: {e}")
            return False, {}

    def analyze_all_stocks(self):
        """分析所有股票并返回符合条件的结果"""
        interesting_stocks = {}

        with ThreadPoolExecutor(max_workers=self.downloader.max_workers) as executor:
            with tqdm(total=len(self.downloader.stocks), desc='ANALYSIS PROGRESS', unit='stock(s)') as pbar:
                futures = {executor.submit(self.analyze_stock, code): code for code in self.downloader.stocks.keys()}
                for future in as_completed(futures):
                    code = futures[future]
                    is_interesting, analysis_result = future.result()
                    if is_interesting:
                        interesting_stocks[code] = analysis_result
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

        if stock_code.startswith('4') or stock_code.startswith('8') or stock_code.startswith(
                '9') or stock_code.startswith('68'):
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


def download_all_stocks(stock_system):
    print("\nDownloading stock data...")
    stock_system.downloader.download_all_stocks()
    print("\nDownload complete!")


def analyze_all_stocks(stock_system):
    print("\nAnalyzing stocks...")
    interesting_stocks = stock_system.analysis_system.analyze_all_stocks()
    print("\nAnalysis complete!")
    return interesting_stocks


def analyze_single_stock(stock_system, stock_code):
    print(f"\nAnalyzing stock {stock_code}...")
    is_interesting, analysis_result = stock_system.analysis_system.analyze_stock(stock_code)
    if is_interesting:
        print("\nInteresting stock found!")
        print(analysis_result)
    else:
        print("\nNo interesting data found for this stock.")

    return is_interesting, analysis_result


def print_analyze(interesting_stocks):
    print("\n=== Analysis Results ===")
    if interesting_stocks:
        print(f"Found {len(interesting_stocks)} interesting stocks:")
        for stock_code, analysis in interesting_stocks.items():
            print(f"Stock Code: {stock_code}")
            print(f"Stock Name: {analysis['stock_name']}")
            print(f"Date: {analysis['date']}")
            print(f"Probability: {analysis['probability']}%")
            print(f"Risk Level: {analysis['risk_level']}")
            print(f"Indicators:")
            print(f"  Volume Ratio: {analysis['indicators']['volume_ratio']}")
            print(f"  Price Change: {analysis['indicators']['price_change']}")
            print(f"  Turnover Rate: {analysis['indicators']['turnover']}")
            print(f"  MA5: {analysis['indicators']['ma5']}")
            print(f"  MA10: {analysis['indicators']['ma10']}")
            print(f"Scores:")
            print(f"  Volume Score: {analysis['scores']['volume_score']}")
            print(f"  Price Score: {analysis['scores']['price_score']}")
            print(f"  Turnover Score: {analysis['scores']['turnover_score']}")
            print(f"  Trend Coefficient: {analysis['scores']['trend_coef']}")
            print()
    else:
        print("No stocks matching the criteria found.")


def print_analyze_top(interesting_stocks, top_n=5):
    print("\n=== Top Analysis Results ===")
    if interesting_stocks:
        # Sort stocks by probability in descending order
        sorted_stocks = sorted(interesting_stocks.items(), key=lambda x: x[1]['probability'], reverse=True)
        print(f"Top {top_n} interesting stocks:")
        for i, (stock_code, analysis) in enumerate(sorted_stocks[:top_n]):
            print(f"TOP {i + 1}")
            print(f"Stock Code: {stock_code}")
            print(f"Stock Name: {analysis['stock_name']}")
            print(f"Date: {analysis['date']}")
            print(f"Probability: {analysis['probability']}%")
            print(f"Risk Level: {analysis['risk_level']}")
            print(f"Indicators:")
            print(f"  Volume Ratio: {analysis['indicators']['volume_ratio']}")
            print(f"  Price Change: {analysis['indicators']['price_change']}")
            print(f"  Turnover Rate: {analysis['indicators']['turnover']}")
            print(f"  MA5: {analysis['indicators']['ma5']}")
            print(f"  MA10: {analysis['indicators']['ma10']}")
            print(f"Scores:")
            print(f"  Volume Score: {analysis['scores']['volume_score']}")
            print(f"  Price Score: {analysis['scores']['price_score']}")
            print(f"  Turnover Score: {analysis['scores']['turnover_score']}")
            print(f"  Trend Coefficient: {analysis['scores']['trend_coef']}")
            print()

    else:
        print("No stocks matching the criteria found.")


def save_analysis_result(interesting_stocks):
    print("\nSaving analysis results...")
    stock_system.analysis_system.save_analysis_result(interesting_stocks)
    print("Results saved successfully!")


########增加一个选股日期输入模块
def get_date_input():
    # 获取输入的日期
    input_start = input("请输入选股开始日期（格式：YYYYMMDD）：").strip()
    input_end = input("请输入选股结束日期（格式：YYYYMMDD）：").strip()
    #获取akshare交易日历
    trade_date_df = ak.tool_trade_date_hist_sina()
    #将'日期'转换成字符串 %Y%m%d 格式
    trade_date_df['trade_date'] = trade_date_df['trade_date'].apply(lambda x: x.strftime('%Y%m%d'))
    trade_date_list = trade_date_df['trade_date'].tolist()
    #判断输入的日期是否在交易日历中,如果不在则往前找到最近一个交易日
    while input_start not in trade_date_list:
        input_start = (datetime.strptime(input_start, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
    while input_end not in trade_date_list:
        input_end = (datetime.strptime(input_end, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
    #获取input_start和input_end在trade_date_list中的索引
    input_start_index = trade_date_list.index(input_start)
    input_end_index = trade_date_list.index(input_end)
    #获取input_start和input_end的索引之间的交易日
    trade_date_list = trade_date_list[input_start_index:input_end_index+1]
    return input_start, input_end,trade_date_list

def get_buy_sell_result_combined():
    # 假设所有 CSV 文件保存在 'buy_sell_result' 文件夹下
    folder_path = 'buy_sell_result'
    all_dfs = []

    # 遍历文件夹中的所有 CSV 文件
    for file_name in os.listdir(folder_path):
        if file_name.endswith('_buy_sell_profit.csv'):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            all_dfs.append(df)

    # 按行合并所有 DataFrame
    combined_df = pd.concat(all_dfs, axis=0, ignore_index=True)

    # 计算所有 increase 的总和
    total_increase_sum = combined_df['increase'].sum()

    # 添加总收益之和列，默认填充 NaN
    combined_df['total_increase_sum'] = pd.NA

    # 只在最后一行填入总收益之和
    if not combined_df.empty:
        combined_df.loc[combined_df.index[-1], 'total_increase_sum'] = total_increase_sum

    # 计算并输出每个 filter_date 的总收益（作为参考）
    grouped_totals = combined_df.groupby('filter_date')['increase'].sum()
    print("每个选股日期的总收益：")
    for filter_date, total in grouped_totals.items():
        print(f'{filter_date} 总收益率：{total:.2%}')

    # 输出所有日期的总收益之和
    print(f'所有选股日期的总收益之和：{total_increase_sum:.2%}')

    # 保存合并后的结果
    combined_df.to_csv('buy_sell_result/combined_buy_sell_profit.csv', index=False)

    # 查看合并后的 DataFrame
    print("\n合并后的 DataFrame:")
    print(combined_df)

if __name__ == '__main__':
    print("=== Stock Analysis Example ===")

    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    stock_system = StockSystem()
    stock_system.downloader.max_workers = 25

    input_start, input_end, trade_date_list = get_date_input()
    print(f'选股日期范围：{input_start}至{input_end}')
    buy_sell_profit_dict = {}
    for filter_date in trade_date_list:
        stock_system.downloader.end_date = filter_date
        # 下载数据
        download_all_stocks(stock_system)
        # 分析股票
        interesting_stocks = analyze_all_stocks(stock_system)
        # 输出分析结果
        print_analyze_top(interesting_stocks)
        # 保存分析结果
        save_analysis_result(interesting_stocks)
        filter_codes_dict = stock_system.analysis_system.get_analyze_top(interesting_stocks)
        print(f'{filter_date}选股结果{filter_codes_dict}')
        #
        filter_codes_list = list(filter_codes_dict.keys())
        # 计算选股日期后未来两天的收益情况（买卖策略：次日开盘买入，次次日收盘卖出）
        # 获取akshare的交易日历
        trade_date_df = ak.tool_trade_date_hist_sina()
        # 将'日期'转换成字符串 %Y%m%d 格式
        trade_date_df['trade_date'] = trade_date_df['trade_date'].apply(lambda x: x.strftime('%Y%m%d'))
        # 判断选股日期在交易日历trade_date_df的索引
        filter_date_index = trade_date_df[trade_date_df['trade_date'] == filter_date].index[0]
        # 获取选股日期后买入交易日
        buy_date = trade_date_df.loc[filter_date_index + 1, 'trade_date']
        # 获取选股日期后的卖出交易日
        sell_date = trade_date_df.loc[filter_date_index + 2, 'trade_date']

        total_increase = 0

        # 计算选股日期后未来两天的收益情况
        buy_sell_profit_df_dict_list = []
        for stock_code in filter_codes_list:
            # 创建一个新的字典对象，避免引用问题
            buy_sell_profit_df_dict = {}

            # 获取买入交易日的开盘价
            buy_date_data = ak.stock_zh_a_hist(symbol=stock_code, period='daily', start_date=buy_date,
                                               end_date=buy_date, adjust="qfq")
            buy_open = round(buy_date_data['开盘'][0], 2)

            # 获取卖出交易日的收盘价
            sell_date_data = ak.stock_zh_a_hist(symbol=stock_code, period='daily', start_date=sell_date,
                                                end_date=sell_date, adjust="qfq")
            sell_close = sell_date_data['收盘'][0]

            # 计算收益率
            increase = (sell_close - buy_open) / buy_open

            # 保存收益情况到新字典
            buy_sell_profit_df_dict['filter_date'] = filter_date
            buy_sell_profit_df_dict['stock_code'] = stock_code
            buy_sell_profit_df_dict['buy_date'] = buy_date
            buy_sell_profit_df_dict['buy_open'] = buy_open
            buy_sell_profit_df_dict['sell_date'] = sell_date
            buy_sell_profit_df_dict['sell_close'] = sell_close
            buy_sell_profit_df_dict['increase'] = round(increase,2)
            total_increase += increase

            # 将新字典添加到列表
            buy_sell_profit_df_dict_list.append(buy_sell_profit_df_dict)

            # 输出收益情况
            print(f'{filter_date}选股股票{stock_code}未来两天收益率：{increase:.2%}')

        # 将收益情况保存为 DataFrame
        buy_sell_profit_df = pd.DataFrame(buy_sell_profit_df_dict_list)

        # 添加总收益列，默认填充 NaN
        buy_sell_profit_df['total_increase'] = pd.NA

        # 只在最后一行填入总收益
        buy_sell_profit_df.loc[buy_sell_profit_df.index[-1], 'total_increase'] = total_increase

        # 输出总收益
        print(f'{filter_date}选股组合总收益率：{total_increase:.2%}')

        # 保存选股日期后未来两天的收益情况到 CSV 文件
        buy_sell_profit_df.to_csv(f'buy_sell_result/{filter_date}_buy_sell_profit.csv', index=False)
        # 输出总收益

        print(f'{filter_date}选股日期后未来两天的收益情况已保存！')
    # 合并所有的买卖收益情况
    get_buy_sell_result_combined()

