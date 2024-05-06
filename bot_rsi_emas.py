from utils.BinanceManager import BinanceManager
import utils.SignalCheckers as sc
from time import sleep
import os

b_manager = BinanceManager()

# Cryptocurrency symbol (BTCUSDT for example)
symbol = input("Enter symbol:")

# Timeframe (1m, 3m, 5m, 15m, 30m, 1H)
timeframe = input("Enter timeframe: ")

# Indicates if holding cryptocurrency
holding = False

# ------ Buy signals ------
over_ema = False
positive_cross = False


# ------ Sell signals ------
negative_cross = False
positive_profit = False
less_than_sma_negative = False
stop_loss = 0
goal = False
goal_profit = 0

if timeframe == '1m':
    goal_profit = 0.2
elif timeframe == '3m':
    goal_profit = 0.7
elif timeframe == '5m':
    goal_profit = 1.7
else:
    goal_profit = 3.7


# To calculate profit
buy_price = 0
sell_price = 0
total_profit = 0

# Wallet info
balance = b_manager.get_balance(symbol)[0]
init_balance = balance

max_decimals = 0

# Execution cicle
while True:
    try:
        balance, crypto_balance = b_manager.get_balance(symbol)

        # Retrieving prices
        prices = b_manager.get_closing_prices(symbol=symbol, timeframe=timeframe, limit=400)

        decimals = str(prices[-1])[::-1].find('.')
        
        if max_decimals < decimals:
            max_decimals = decimals

        # Technical indicators
        current_sma_fast = round(b_manager.calculate_sma(prices, 5)[0], max_decimals+1)
        current_sma_slow = round(b_manager.calculate_sma(prices, 20)[0], max_decimals+1)
        sma_fast, past_sma_fast = b_manager.calculate_sma(prices[:-1], 5)
        sma_fast = round(sma_fast, max_decimals+1)
        past_sma_fast = round(past_sma_fast, max_decimals+1)
        sma_slow, past_sma_slow = b_manager.calculate_sma(prices[:-1], 20)
        sma_slow = round(sma_slow, max_decimals+1)
        past_sma_slow = round(past_sma_slow, max_decimals+1)
        ema = round(b_manager.calculate_ema(prices, 200), max_decimals)

        os.system("cls")
        # Signals checking
        ## For buying
        if not holding:
            over_ema = prices[-1] > ema
            
            positive_cross = past_sma_fast < past_sma_slow and sma_fast >= sma_slow and current_sma_fast > current_sma_slow
            
            print("*******************************")
            print("WAITING FOR BUYING...")
            print("CURRENT PRICE IS MORE THAN EMA:", over_ema)
            print("POSITIVE CROSS:", positive_cross)
        
        ## For selling
        if holding:
            sell_price = prices[-1]

            profit = ((sell_price - buy_price) / buy_price)
            profit = profit * 100 - 0.3


            goal = profit >= goal_profit
            positive_profit = profit > 0
            negative_cross = past_sma_fast >= past_sma_slow and sma_fast < sma_slow
            less_than_sma_negative = prices[-1] < stop_loss
            
            print("*******************************")
            print("WAITING FOR SELLING...")
            print("PROFIT:", profit, "%")
            print("GOAL PROFIT:", goal_profit, "%")
            print("POSITIVE PROFIT:", positive_profit)
            print("NEGATIVE CROSS:", negative_cross)
            print("LESS THAN SMA NEGATIVE:", less_than_sma_negative)
            print("NEGATIVE:", stop_loss)
        
        print("-------------------------------")
        print(f"TIMEFRAME: {timeframe}")
        print(f"SYMBOL: {symbol}")
        print("CURRENT PROFIT =", total_profit, "%")
        print("CURRENT PRICE:", prices[-1])
        print("EMA:", ema)
        print("SMA SLOW:", sma_slow)
        print("SMA FAST:", sma_fast)
        print("BALANCE:", balance, "USDT", "-", crypto_balance, symbol[:-4])
        print("INITIAL BALANCE:", init_balance, "USDT")
        print("*******************************")
        
        buy = over_ema and positive_cross and not holding
        sell = (((positive_profit or less_than_sma_negative) and negative_cross) or goal) and holding
        
        if buy:
            b_manager.buy_order(symbol)
            print("BUY!!!")
            
            holding = True
            over_ema = False
            positive_cross = False

            buy_price = prices[-1]
            stop_loss = sma_slow

        if sell:
            b_manager.sell_order(symbol, max_decimals)
            print("SELL!!!")

            positive_profit = False
            negative_cross = False
            less_than_sma_negative = False
            goal = False

            holding = False

            balance = b_manager.get_balance(symbol)[0]

            profit = ((balance - init_balance) / init_balance)
            
            total_profit = profit * 100


        sleep(0.5)

    except KeyboardInterrupt:
        print(f'''BOT FINISHED...
        TOTAL_PROFIT: {total_profit}%''')

        input("Enter any character to end:")
        exit(0)

    except Exception as e:
        print(f"Error encoutered: {e}")