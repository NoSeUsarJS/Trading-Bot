import os

class Writer:
    def _create_folder(self, folder_name):
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
            print(f"Se ha creado la carpeta '{folder_name}'")
        else:
            print(f"La carpeta '{folder_name}' ya existe")

    def _write_headers(self, symbol, timeframe):
        self._create_folder(folder_name='results')
        
        with open(f'results/{symbol}_{timeframe}.csv', 'w') as file:
            file.write('time,buy_time,buy_price,sell_price,type,delta,max_delta\n')
    
    def _write_sell(self, symbol, timeframe, current_time, buy_time, buy_value, sell_value, delta):
        with open(f'results/{symbol}_{timeframe}.csv', 'a') as file:
            if delta > 0:
                file.write(f'{current_time},{buy_time},{buy_value},{sell_value},P,{delta}%\n')
            else:
                file.write(f'{current_time},{buy_time},{buy_value},{sell_value},L,{delta}%\n')
            
        