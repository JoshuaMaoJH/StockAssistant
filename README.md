# Chinese A-Share Market Analysis System

A comprehensive tool for downloading, analyzing, and visualizing Chinese A-share stock market data. This system provides an easy-to-use interface for accessing historical stock data and generating various technical analysis charts.

## Features

- **Data Download**
  - Download historical data for all A-share stocks
  - Selective download for specific stock codes
  - Automatic data validation and error handling
  - Multi-threaded downloading for improved performance
  - ST stock and delisting detection

- **Visualization Tools**
  - Candlestick (K-line) charts
  - Moving Average (MA) analysis with customizable periods
  - Trend analysis combining price and moving averages
  - Professional-grade charts with Chinese character support

## Prerequisites

The following Python packages are required:

```bash
pip install akshare pandas matplotlib tqdm
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JoshuaMaoJH/StockAssistant.git
cd StockAssistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

1. Start the system:
```bash
python stock_system.py
```

2. Use the menu interface to:
   - Download stock data
   - Generate visualizations
   - Exit the program

### Advanced Usage

You can also use the system programmatically:

```python
from stock_system import StockSystem

# Initialize the system
system = StockSystem()

# Download data for all stocks
system.downloader.download_all_stocks()

# Draw a candlestick chart for a specific stock
system.line_drawer.draw_single_stock_kline('000001')

# Draw MA lines with custom periods
system.line_drawer.draw_single_stock_ma([5, 10, 20], '000001')

# Draw trend analysis
system.line_drawer.draw_single_stock_trends('000001')
```

## Configuration

Default settings can be modified in `StockDownloader.__init__()`:

- `frequency`: Data frequency ('daily' by default)
- `start_date`: Start date for historical data ('20220101' by default)
- `end_date`: End date (current date by default)
- `max_workers`: Maximum concurrent download threads (10 by default)

## Data Structure

Downloaded stock data includes:
- Date (日期)
- Opening Price (开盘)
- Closing Price (收盘)
- Highest Price (最高)
- Lowest Price (最低)
- Trading Volume (成交量)
- Trading Amount (成交额)
- Price Amplitude (振幅)
- Price Change Ratio (涨跌幅)
- Price Change Amount (涨跌额)
- Turnover Rate (换手率)

## Error Handling

The system includes comprehensive error handling for:
- Invalid stock codes
- Network connection issues
- Data validation failures
- File system operations
- Visualization errors

## Examples

### Downloading Stock Data
```python
# Download single stock
system = StockSystem()
system.downloader.download_single_stock('000001')

# Check downloaded data size
files, _, _, mb, _ = system.downloader.check_size_of_all_stock_data()
print(f"Total data size: {mb:.2f} MB")
```

### Creating Visualizations
```python
# Draw candlestick chart with 5, 10, and 20-day moving averages
system.line_drawer.draw_single_stock_ma([5, 10, 20], '000001')
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Joshua MaoJH (https://github.com/JoshuaMaoJH)

## Acknowledgments

- Thanks to the AKShare project for providing the data API
- Special thanks to all contributors and users of this system

## Support

For support and questions, please open an issue in the GitHub repository or contact the author directly.
