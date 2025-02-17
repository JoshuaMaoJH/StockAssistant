# StockAssistant
# Stock Market Analysis System
# This system provides functionality for downloading, analyzing, and visualizing Chinese A-share stock data
# Author: Joshua Mao
# Create Date: 02-17-2025

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
