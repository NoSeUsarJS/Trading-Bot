from binance.client import Client
import math
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

class BinanceManager:
    def __init__(self, api_key = API_KEY, api_secret = API_SECRET) -> None:
        self.client = Client(api_key, api_secret)
    
    def obtener_porcentaje_cambio(self, simbolo):
        try:
            # Obtener el precio de hace 4 hrs
            klines = self.client.get_klines(symbol=simbolo, interval=Client.KLINE_INTERVAL_3MINUTE, limit=490)
            precio_hora_anterior = float(klines[-480][4])
            
            # Obtener el precio actual
            ticker = self.client.get_ticker(symbol=simbolo)
            precio_actual = float(ticker['lastPrice'])
            
            # Calcular el porcentaje de cambio
            porcentaje_cambio = ((precio_actual - precio_hora_anterior) / precio_hora_anterior) * 100
            return simbolo, porcentaje_cambio
        except Exception as e:
            print(f"Error al obtener el porcentaje de cambio para {simbolo}: {e}")
            return simbolo, float('-inf')  # Retornar un valor negativo infinito en caso de error
    
    def get_volatility(self, symbol):
        try:
            volatility = {}

            candles = self.client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_4HOUR, limit=2)
            high_price = float(candles[-1][2])  # Precio máximo de las últimas 4 horas
            low_price = float(candles[-1][3])   # Precio mínimo de las últimas 4 horas
            volatility = high_price - low_price

            return symbol, volatility
        except Exception as e:
            print(f"Error al obtener el porcentaje de cambio para {symbol}: {e}")
            return symbol, float('-inf')  # Retornar un valor negativo infinito en caso de error

    def find_symbol(self):
        # Obtener los símbolos de todos los pares tradeables
        exchange_info = self.client.get_exchange_info()
        symbols = [symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['status'] == 'TRADING' and symbol['symbol'].endswith('USDT')]

        # Usar un ThreadPoolExecutor para procesar las solicitudes de manera asíncrona
        with ThreadPoolExecutor() as executor:
            # Mapear la función obtener_porcentaje_cambio a cada símbolo en paralelo
            resultados = executor.map(self.obtener_porcentaje_cambio, symbols)

        # Obtener el símbolo con el mayor crecimiento
        mayor_crecimiento = max(resultados, key=lambda x: x[1])[0]

        return mayor_crecimiento
    
    def get_balance(self, symbol):
        return float(self.client.get_asset_balance(asset='USDT')['free']), float(self.client.get_asset_balance(asset=symbol[:-4])['free'])
    
    # Función para obtener los datos del precio de cierre
    def get_closing_prices(self, symbol, timeframe, limit):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
        closing_prices = [float(candle[4]) for candle in candles]
        return closing_prices
    
    def get_high_prices(self, symbol, timeframe, limit):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
        high_prices = [float(candle[2]) for candle in candles]
        return high_prices

    def get_low_prices(self, symbol, timeframe, limit):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
        low_prices = [float(candle[3]) for candle in candles]
        return low_prices
    
    def last_2_periods_closed(self, symbol, timeframe, limit=3):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)[:2]
        closed_negative = [True if float(candle[4]) < float(candle[1]) else False for candle in candles]

        print(closed_negative)
        
        if all(closed_negative):
            return True
        else:
            return False
    
    def last_3_periods_closed(self, symbol, timeframe, limit=4):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)[:3]
        closed_negative = [True if float(candle[4]) < float(candle[1]) else False for candle in candles]

        print(closed_negative)
        
        if all(closed_negative):
            return True
        else:
            return False
    

    def is_positive(self, symbol, timeframe, limit=1):
        candle = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)[-1]
        
        return True if float(candle[4]) > float(candle[1]) else False

    def current_candle_open_time(self, symbol, timeframe, limit=1):
        time = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)[-1][0]

        return time
    
    # Función para calcular la media móvil (SMA)
    def calculate_sma(self, prices, period):
        length_prices = len(prices)
        
        current_sma = sum(prices[length_prices - period:length_prices]) / period
        previous_sma = sum(prices[length_prices-1 - period:length_prices-1]) / period

        return current_sma, previous_sma
    
    def calculate_ema(self, prices, period):
        alpha = 2 / (period + 1)
        ema_current_value = prices[0]  # El primer valor de la EMA es igual al primer valor de los datos

        for i in range(1, len(prices)):
            ema_current_value = (prices[i] - ema_current_value) * alpha + ema_current_value

        return ema_current_value

    def calculate_rsi(self, prices, period=6):
        price_changes = np.diff(prices)

        # Separa los cambios positivos y negativos
        positive_changes = price_changes.copy()
        positive_changes[positive_changes < 0] = 0
        negative_changes = -price_changes.copy()
        negative_changes[negative_changes < 0] = 0

        # Calcula el EMA de los cambios positivos y negativos
        alpha = 1 / period
        ema_up = np.zeros_like(positive_changes)
        ema_down = np.zeros_like(negative_changes)
        ema_up[period-1] = np.mean(positive_changes[:period])
        ema_down[period-1] = np.mean(negative_changes[:period])
        for i in range(period, len(positive_changes)):
            ema_up[i] = alpha * positive_changes[i] + (1 - alpha) * ema_up[i-1]
            ema_down[i] = alpha * negative_changes[i] + (1 - alpha) * ema_down[i-1]

        # Calcula el RSI
        rs = ema_up / ema_down
        rsi = 100 - (100 / (1 + rs))

        return rsi[-1]
    
    def calculate_ssl(self, symbol, timeframe, past=False, len_=10):
        high_prices = self.get_high_prices(symbol, timeframe, limit = 12)
        low_prices = self.get_low_prices(symbol, timeframe, limit = 12)
        close_prices = self.get_closing_prices(symbol, timeframe, limit = 12)

        if past:
            high_prices = high_prices[:-2][-len_:]
            low_prices = low_prices[:-2][-len_:]
            close_prices = close_prices[:-2][-len_:]
        else:
            high_prices = high_prices[:-1][-len_:]
            low_prices = low_prices[:-1][-len_:]
            close_prices = close_prices[:-1][-len_:]
        
        # Calcular las medias móviles
        smaHigh = np.mean(high_prices)
        smaLow = np.mean(low_prices)

         # Identificar la dirección del SSL
        if close_prices[-1] > smaHigh:
            Hlv = 1
        elif close_prices[-1] < smaLow:
            Hlv = -1
        else:
            Hlv = 0  # Inicializa como neutral si no cumple ninguna condición

        # Calcular las líneas SSL
        sslDown = smaHigh if Hlv < 0 else smaLow
        sslUp = smaLow if Hlv < 0 else smaHigh

        return sslDown, sslUp

    
    def buy_order(self, symbol):
        while True:
            try:
                account_info = self.client.get_account()
                balances = {item['asset']: float(item['free']) for item in account_info['balances']}
                usdt_balance = balances.get('USDT', 0)
                current_price = float(self.client.get_symbol_ticker(symbol=symbol)['price']) 

                quantity = usdt_balance * 1 / current_price

                min_qty = self.minQty(symbol=symbol)

                quantity = max(min_qty, quantity)
                quantity = math.floor(quantity / min_qty) * min_qty
                quantity = math.floor(quantity * 10**4) / 10**4
                quantity = quantity

                print(f"Inversión de {quantity} {symbol[:-4]}: {round(usdt_balance * 1, 4)} USDT")
                buy_order = self.client.order_market_buy(symbol=symbol, quantity=quantity)
                print("Orden de compra:", buy_order)
                break
            
            except Exception as e:
                print("Ocurrió un error con la compra, intentando nuevamente...", e)
                sleep(0.1)
                continue
    
    def sell_order(self, symbol, decimales):
        while True:
            try:
                account_info = self.client.get_account()
                balances = {item['asset']: float(item['free']) for item in account_info['balances']}
                quantity = float(balances.get(symbol[:-4], 0))
                min_qty = self.minQty(symbol=symbol)

                quantity = max(min_qty, quantity)
                quantity = math.floor(quantity / min_qty) * min_qty
                quantity = math.floor(quantity * 10**decimales) / 10**decimales
                quantity = quantity

                sell_order = self.client.order_market_sell(symbol=symbol, quantity=quantity)
                print("Orden de venta:", sell_order)
                break

            except Exception as e:
                print("Ocurrió un error con la venta, intentando nuevamente...", e)
                sleep(0.1)
                continue

    def minQty(self, symbol):
        # Obtiene las restricciones de tamaño de lote para el par de trading
        min_qty = self.client.get_symbol_info(symbol=symbol)["filters"][1]["minQty"]
        return float(min_qty)
    