from stock_system import StockSystem


def main():
    stock_system = StockSystem()

    def choice_system():
        def downloader():
            choice = input(
                """
                1. Download all stock data
                2. Download stock data by code
                3. Back
                INPUT A CHOICE:
                """)
            if choice == '1':
                stock_system.downloader.download_all_stocks()
            elif choice == '2':
                codes = input('INPUT A CODE LIST (USE "," TO SEPARATE): ').split(',')
                for code in codes:
                    stock_system.downloader.download_single_stock(code)

            elif choice == '3':
                return
            else:
                print('Invalid choice')

        def line_drawer():
            choice = input(
                """
                1. Draw stock kline
                2. Draw stock ma
                3. Draw stock trend
                3. Back
                INPUT A CHOICE:
                """)
            if choice == '1':
                codes = input('INPUT A CODE LIST (USE "," TO SEPARATE): ').split(',')
                for code in codes:
                    stock_system.line_drawer.draw_single_stock_kline(code)
            elif choice == '2':
                codes = input('INPUT A CODE LIST (USE "," TO SEPARATE): ').split(',')
                mas = input('INPUT A MA LIST (USE "," TO SEPARATE): ').split(',')
                for code in codes:
                    stock_system.line_drawer.draw_single_stock_ma(mas, code)

            elif choice == '3':
                codes = input('INPUT A CODE LIST (USE "," TO SEPARATE): ').split(',')
                for code in codes:
                    stock_system.line_drawer.draw_single_stock_trends(code)

        choice = input(
            """
1. Downloader
2. LineDrawer
3. Exit
INPUT A CHOICE: 
""")
        if choice == '1':
            downloader()
        elif choice == '2':
            line_drawer()
        elif choice == '3':
            exit()
        else:
            print('Invalid choice')

    while True:
        choice_system()


if __name__ == '__main__':
    main()
