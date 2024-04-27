from binance.client import Client
import math
from concurrent.futures import ThreadPoolExecutor

class BinanceManager:
    def __init__(self, api_key, api_secret) -> None:
        self.client = Client(api_key, api_secret)
    
    def get_price_change(self, symbol):
        ticker_24hr = self.client.get_ticker(symbol=symbol)
        price_change_percent = float(ticker_24hr['priceChangePercent'])
        return symbol, price_change_percent

    def find_symbol(self):
        # Obtén todos los pares de trading disponibles
        tickers = self.client.get_all_tickers()

        # Filtra los pares para incluir solo aquellos con "USDT" como moneda base o de cotización
        usdt_pairs = [ticker for ticker in tickers if "USDT" in ticker['symbol']]

        # Utiliza múltiples hilos para obtener el porcentaje de cambio de cada símbolo
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.get_price_change, ticker['symbol']) for ticker in usdt_pairs]

        # Espera a que se completen todas las tareas y obtén los resultados
        results = [future.result() for future in futures]

        # Encuentra el par con el mayor cambio positivo utilizando la función max de Python
        max_ticket = max(results, key=lambda x: x[1])

        return max_ticket[0]
    
    def get_balance(self):
        return float(self.client.get_asset_balance(asset='USDT')['free'])
    
    # Función para obtener los datos del precio de cierre
    def get_closing_prices(self, symbol, timeframe, limit):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
        closing_prices = [float(candle[4]) for candle in candles]
        return closing_prices
    
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
    
    def buy_order(self, symbol):
        account_info = self.client.get_account()
        balances = {item['asset']: float(item['free']) for item in account_info['balances']}
        usdt_balance = balances.get('USDT', 0)
        current_price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])

        quantity = usdt_balance * 1 / current_price

        min_qty = self.minQty(symbol=symbol)

        quantity = max(min_qty, quantity)
        quantity = math.floor(quantity / min_qty) * min_qty
        quantity = round(quantity, 4)

        print(f"Inversión de {quantity} {symbol[:-4]}: {round(usdt_balance * 1, 4)} USDT")
        buy_order = self.client.order_market_buy(symbol=symbol, quantity=quantity)
        print("Orden de compra:", buy_order)
    
    def sell_order(self, symbol, decimales):
        account_info = self.client.get_account()
        balances = {item['asset']: float(item['free']) for item in account_info['balances']}
        quantity = float(balances.get(symbol[:-4], 0))
        
        min_qty = self.minQty(symbol=symbol)

        quantity = max(min_qty, quantity)
        quantity = math.floor(quantity / min_qty) * min_qty
        quantity = round(quantity, decimales)

        sell_order = self.client.order_market_sell(symbol=symbol, quantity=quantity)
        print("Orden de compra:", sell_order)

    def minQty(self, symbol):
        # Obtiene las restricciones de tamaño de lote para el par de trading
        min_qty = self.client.get_symbol_info(symbol=symbol)["filters"][1]["minQty"]
        return float(min_qty)
    