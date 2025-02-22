# Import the main StockSystem class that handles data downloading and visualization
from stock_system import StockSystem


def get_stock_codes():
    """
    Helper function to get a list of stock codes from user input.
    Returns a list of cleaned stock codes, removing any whitespace.
    """
    return [code.strip() for code in input('INPUT A CODE LIST (USE "," TO SEPARATE): ').split(',')]


def downloader(stock_system):
    """
    Handles the stock data downloading functionality.
    Provides options to download all stocks or specific stocks by code.

    Args:
        stock_system: Instance of StockSystem class containing downloader functionality
    """
    while True:
        # Display download menu options
        choice = input(
            """
            1. Download all stock data
            2. Download stock data by code
            3. Back
            INPUT A CHOICE:
            """)

        if choice == '1':
            # Download data for all available stocks
            stock_system.downloader.download_all_stocks()
            print("Download complete!")
        elif choice == '2':
            # Get specific stock codes from user
            codes = get_stock_codes()
            for code in codes:
                # Verify if the stock code exists in the system
                if code in stock_system.downloader.stocks:
                    result = stock_system.downloader.download_single_stock(code)
                    # Handle potential download errors
                    if isinstance(result, Exception):
                        print(f"Error downloading {code}: {result}")
                    else:
                        print(f"Downloaded {code}")
                else:
                    print(f"Invalid stock code: {code}")
        elif choice == '3':
            break
        else:
            print('Invalid choice')


def line_drawer(stock_system):
    """
    Handles the stock visualization functionality.
    Provides options to draw different types of charts: K-line, Moving Average, and Trend lines.

    Args:
        stock_system: Instance of StockSystem class containing line drawing functionality
    """
    while True:
        # Display visualization menu options
        choice = input(
            """
            1. Draw stock kline
            2. Draw stock ma
            3. Draw stock trend
            4. Back
            INPUT A CHOICE:
            """)

        if choice == '1':
            # Draw K-line (candlestick) charts
            codes = get_stock_codes()
            for code in codes:
                result = stock_system.line_drawer.draw_single_stock_kline(code)
                if isinstance(result, Exception):
                    print(f"Error plotting kline for {code}: {result}")
        elif choice == '2':
            # Draw Moving Average (MA) lines
            codes = get_stock_codes()
            try:
                # Get MA periods from user (e.g., 5,10,20 for 5-day, 10-day, 20-day MA)
                mas = [int(ma.strip()) for ma in input('INPUT A MA LIST (USE "," TO SEPARATE): ').split(',')]
                for code in codes:
                    result = stock_system.line_drawer.draw_single_stock_ma(mas, code)
                    if isinstance(result, Exception):
                        print(f"Error plotting MA for {code}: {result}")
            except ValueError:
                print("Invalid MA values. Please enter numbers.")
        elif choice == '3':
            # Draw trend analysis charts
            codes = get_stock_codes()
            for code in codes:
                result = stock_system.line_drawer.draw_single_stock_trends(code)
                if isinstance(result, Exception):
                    print(f"Error plotting trends for {code}: {result}")
        elif choice == '4':
            break
        else:
            print('Invalid choice')


def main():
    """
    Main function that initializes the stock system and provides the primary menu interface.
    Creates an instance of StockSystem and handles the main program loop.
    """
    # Initialize the stock system
    stock_system = StockSystem()


    # Main program loop
    while True:
        # Display main menu options
        choice = input(
            """
1. Downloader
2. LineDrawer
3. Exit
INPUT A CHOICE: 
""")
        if choice == '1':
            downloader(stock_system)
        elif choice == '2':
            line_drawer(stock_system)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print('Invalid choice')


# Standard Python idiom to ensure main() only runs if the script is executed directly
if __name__ == '__main__':
    main()