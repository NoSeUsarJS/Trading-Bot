from win10toast import ToastNotifier
from utils.Writer import Writer
from time import sleep
from datetime import datetime
from utils.BinanceManager import BinanceManager
import threading
from dotenv import load_dotenv
import os

load_dotenv()

toaster = ToastNotifier()

timeframe = input('Ingresar marco de tiempo (1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M): ')

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

binance_manager = BinanceManager(api_key=api_key, api_secret=api_secret)

symbol = binance_manager.find_symbol()

writer = Writer()

writer._write_headers(symbol=symbol, timeframe=timeframe)

balance = binance_manager.get_balance()

inversion = balance/2

buy_value = 0
sell_value = 0

fast_sma = 5
slow_sma = 200

lock = threading.Lock()
stop_thread = False

def execute_find_symbol():
    global symbol
    while True:
        if not stop_thread:
            lock.acquire()
            symbol = binance_manager.find_symbol()
            lock.release()
            sleep(60)
        else:
            exit(0)

holding = False

buy_time = None

max_decimales = 0

total_profit = 0
total_profit_no_comision = 0

init_time = datetime.now()
init_time = init_time.strftime("%H:%M:%S")
current_time = None

current_symbol = symbol
max_change_thread = threading.Thread(target=execute_find_symbol)
max_change_thread.daemon = True
max_change_thread.start()
change_symbol_signal= False

is_positive_var = False

sell_price = 0
last_time = -1
sell_signal = False

while True:
    if current_symbol != symbol and not holding and change_symbol_signal:
        change_symbol_signal = False
        current_symbol = symbol
        print(f'PAR CAMBIADO A {current_symbol}')
        toaster.show_toast(f'PAR CAMBIADO A {current_symbol}', duration=1)
    try:
        if total_profit >= 6:
            current_time = datetime.now()
            current_time = current_time.strftime("%H:%M:%S")
            print(f'Tiempo de inicio: {init_time}. Tiempo de término: {current_time}')
            print(f'EL PROFIT TOTAL PARA {current_symbol} FUE: {total_profit}%')
            input('ingrese cualquier tecla para salir:')
            exit(0)

        closing_prices = binance_manager.get_closing_prices(current_symbol, timeframe=timeframe, limit=slow_sma+1)

        buy_signal = binance_manager.last_3_periods_closed(symbol=current_symbol, timeframe=timeframe)
        is_positive_var = binance_manager.is_positive(symbol=current_symbol, timeframe=timeframe)

        decimales = str(closing_prices[-1])[::-1].find('.')
        
        current_candle_time = binance_manager.current_candle_open_time(symbol=current_symbol, timeframe=timeframe)
        if last_time != current_candle_time:
            sell_signal = True
            last_time = current_candle_time
        else:
            sell_signal = False
        
        if max_decimales < decimales:
            max_decimales = decimales

        sma_slow, previous_sma_slow = binance_manager.calculate_sma(closing_prices, slow_sma)
        sma_slow = round(sma_slow, max_decimales)
        previous_sma_slow = round(previous_sma_slow, max_decimales)

        sma_fast = binance_manager.calculate_sma(closing_prices, fast_sma)[0]
        sma_fast = round(sma_fast, max_decimales)

        slope = sma_slow/previous_sma_slow - 1

        if closing_prices[-1] > sma_fast and sell_price < closing_prices[-1]:
            sell_price = closing_prices[-1]

        print("-----------------------------------------------------------------")
        print(f"Cantidad mínima a invertir: {binance_manager.minQty(current_symbol)}")
        if holding:
            delta = round(100*closing_prices[-1]/buy_value - 100, 2)

            delta = delta - 0.1

            print(f'HOLDING WITH {buy_value}, {delta}%')

        if slope > 0:
            change_symbol_signal = False
            print("ALCISTA")
        else:
            change_symbol_signal = True
            print("BAJISTA")
            
        print(f"Timeframe: {timeframe}")
        print(f"El precio actual {current_symbol} es: {closing_prices[-1]}.")
        print(f"SMA 5: {sma_fast}, SMA 200: {sma_slow}, previous SMA 200: {previous_sma_slow}")
        print(f"Pendiente: {slope}")
        print(f'Total profit: {total_profit}%')
        print(f'Balance: {balance}')
        print("-----------------------------------------------------------------")

        if slope > 0 and buy_signal and closing_prices[-1] < sma_fast and is_positive_var and not holding:
            binance_manager.buy_order(symbol=current_symbol)
            print(f"Comprar ahora (SMA 5: {sma_fast}, SMA 200: {sma_slow})...")
            buy_value = closing_prices[-1]
            
            buy_time = datetime.now().strftime("%H:%M:%S")

            toaster.show_toast(f"COMPRA {current_symbol}", f'{buy_value}', duration=1)
            balance = balance - inversion
        
            holding = True
            continue

        if (sell_signal and closing_prices[-1] > sma_fast) and holding:
            binance_manager.sell_order(symbol=current_symbol, decimales=max_decimales)

            print(f"Vender ahora (SMA 5: {sma_fast}, SMA 200: {sma_slow})...")
            sell_value = closing_prices[-1]
            sell_signal = False

            if buy_value == 0:
                sleep(1)
                continue

            delta = round(100*sell_value/buy_value - 100, 2)

            delta = delta - 0.1 # COMISION

            total_profit += delta
            total_profit_no_comision += delta + 0.1

            toaster.show_toast(f"VENTA {current_symbol}", f'{buy_value},{delta}%', duration=1)
            diferencia = inversion * (1 + delta/100)
            balance = balance + diferencia

            current_time = datetime.now()
            current_time = current_time.strftime("%H:%M:%S")
            
            holding = False
            writer._write_sell(
                symbol=current_symbol,
                timeframe=timeframe, 
                current_time=current_time, 
                buy_time=buy_time,
                buy_value=buy_value,
                sell_value=sell_value,
                delta=delta
                )
            
            continue

        sleep(0.5)
    except KeyboardInterrupt:
        stop_thread = True
        print(f'EL PROFIT TOTAL PARA {current_symbol} FUE: {total_profit}%')
        print(f'Sin contar comision sería: {total_profit_no_comision}%')
        sleep(5)
        exit(0)