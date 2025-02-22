from stock_system import StockSystem

def get_stock_codes():
    return [code.strip() for code in input('INPUT A CODE LIST (USE "," TO SEPARATE): ').split(',')]

def downloader(stock_system):
    while True:
        choice = input(
            """
            1. Download all stock data
            2. Download stock data by code
            3. Back
            INPUT A CHOICE:
            """)
        if choice == '1':
            stock_system.downloader.download_all_stocks()
            print("Download complete!")
        elif choice == '2':
            codes = get_stock_codes()
            for code in codes:
                if code in stock_system.downloader.stocks:
                    result = stock_system.downloader.download_single_stock(code)
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
    while True:
        choice = input(
            """
            1. Draw stock kline
            2. Draw stock ma
            3. Draw stock trend
            4. Back
            INPUT A CHOICE:
            """)
        if choice == '1':
            codes = get_stock_codes()
            for code in codes:
                result = stock_system.line_drawer.draw_single_stock_kline(code)
                if isinstance(result, Exception):
                    print(f"Error plotting kline for {code}: {result}")
        elif choice == '2':
            codes = get_stock_codes()
            try:
                mas = [int(ma.strip()) for ma in input('INPUT A MA LIST (USE "," TO SEPARATE): ').split(',')]
                for code in codes:
                    result = stock_system.line_drawer.draw_single_stock_ma(mas, code)
                    if isinstance(result, Exception):
                        print(f"Error plotting MA for {code}: {result}")
            except ValueError:
                print("Invalid MA values. Please enter numbers.")
        elif choice == '3':
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
    stock_system = StockSystem()
    while True:
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

if __name__ == '__main__':
    main()