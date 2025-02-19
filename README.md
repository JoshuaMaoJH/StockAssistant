# Chinese A-Share Stock Analysis System

A comprehensive Python-based system for downloading, analyzing, and visualizing Chinese A-share stock market data. This system provides tools for batch downloading stock data, creating various technical analysis charts, and performing trend analysis.

## Features

- **Batch Data Download**: Concurrent downloading of stock data for all A-shares
- **Data Validation**: Automatic verification of data completeness and integrity
- **Multiple Visualization Options**:
  - Candlestick charts
  - Moving average analysis
  - Trend visualization
- **Customizable Parameters**: Flexible date ranges, frequencies, and analysis periods

## Requirements

```
python >= 3.7
akshare
pandas
matplotlib
tqdm
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-analysis-system.git
cd stock-analysis-system
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from stock_system import StockSystem

# Create system instance
stock_system = StockSystem()

# Download data for all stocks
stock_system.downloader.download_all_stocks()

# Draw charts for a specific stock
stock_code = '000001'  # Example: Ping An Bank

# Draw candlestick chart
stock_system.lineDrawer.draw_single_stock_kline(stock_code)

# Draw moving averages (5, 10, 20, 30 days)
stock_system.lineDrawer.draw_single_stock_ma([5,10,20,30], stock_code)

# Draw trend analysis
stock_system.lineDrawer.draw_single_stock_trends(stock_code)
```

### Advanced Configuration

You can customize various parameters by modifying the `StockDownloader` initialization:

```python
class StockDownloader:
    def __init__(self):
        self.frequency = 'daily'  # Change data frequency
        self.start_date = '20220101'  # Modify start date
        self.end_date = dt.datetime.now().strftime('%Y%m%d')  # Modify end date
        self.max_workers = 10  # Adjust concurrent download threads
```

## Project Structure

```
stock-analysis-system/
├── stock_system.py     # Main system implementation
├── requirements.txt    # Package dependencies
├── stock_data/        # Downloaded stock data directory
└── README.md          # This file
```

## Class Overview

### StockDownloader
Handles all data downloading and management operations:
- Downloads stock data using AKShare API
- Manages concurrent downloads
- Validates data integrity
- Saves data to CSV files

### StockLineDrawer
Provides visualization functionality:
- Candlestick charts
- Moving average analysis
- Trend visualization
- Customizable chart parameters

### StockSystem
Main system class that integrates all functionality:
- Initializes necessary components
- Provides unified interface for all operations

## Data Storage

Stock data is stored in CSV format in the `stock_data` directory. Each file is named using the format:
```
{stock_code}_{stock_name}_{start_date}_{end_date}.csv
```

## Error Handling

The system includes comprehensive error handling:
- Network errors during downloads
- Data validation errors
- File system errors
- Visualization errors

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [AKShare](https://www.akshare.xyz/) for providing the data API
- Chinese A-share market data providers

## Support

For support and questions, please open an issue in the GitHub repository.
