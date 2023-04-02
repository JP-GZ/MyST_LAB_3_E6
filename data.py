"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: data.py : python script for data collection                                                 -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""
import MetaTrader5
import  pandas as pd
import numpy as np
from datetime import datetime, timedelta


def f_leer_archivo():
    cuenta = pd.read_csv(r'.\files\Accounts.csv')
    nombres = list(cuenta['Name'])
    print(f'Nombres disponibles:', nombres)
    global nombre
    nombre = input('Ingrese nombre cuenta a utilizar:')
    uname = int(cuenta['Account'][cuenta.Name == nombre][0])
    pword = str(cuenta['Password'][cuenta.Name == nombre][0])

    trading_server = str('FxPro-MT5')  # Server must be a string
    # Attempt to start MT5
    if MetaTrader5.initialize(login=uname, password=pword, server=trading_server):
        # Login to MT5
        if MetaTrader5.login(login=uname, password=pword, server=trading_server):
            # return True
            df_trades = MetaTrader5.history_deals_get(datetime(2023, 1, 1), datetime.now())
            df_trades = pd.DataFrame(list(df_trades), columns=df_trades[0]._asdict().keys())
            print(len(df_trades['position_id'].unique()))
            # df_trades.to_csv('data_trades.csv')
            Dates = pd.DataFrame({'Position': df_trades['position_id'].unique()})
            opentime = []
            closetime = []
            price_open = []
            price_close = []
            for i in df_trades['position_id'].unique():
                dates = np.array(df_trades['time'][df_trades['position_id'] == i])
                prices = np.array(df_trades['price'][df_trades['position_id'] == i])
                if len(dates) == 2:
                    opentime.append(dates[0])
                    closetime.append(dates[1])
                    price_open.append(prices[0])
                    price_close.append(prices[1])
                else:
                    opentime.append(dates[0])
                    closetime.append(0)
                    price_open.append(prices[0])
                    price_close.append(prices[-1])
            Dates['Time'] = opentime
            Dates['Symbol'] = [np.array(df_trades['symbol'][df_trades['position_id'] == i])[0]

                               for i in df_trades['position_id'].unique()]

            type_op = [np.array(df_trades['type'][df_trades['position_id'] == i])[0]
                       for i in df_trades['position_id'].unique()]

            Dates['Type'] = ['buy' if i == 0 else 'sell' for i in type_op]
            Dates['Volume'] = [np.array(df_trades['volume'][df_trades['position_id'] == i])[0]
                               for i in df_trades['position_id'].unique()]
            Dates['Price'] = price_open
            Dates['Time.1'] = closetime
            Dates['Price.1'] = price_close
            Dates['Commission'] = [np.array(df_trades['commission'][df_trades['position_id'] == i])[-1]
                                   for i in df_trades['position_id'].unique()]
            Dates['Swap'] = [np.array(df_trades['swap'][df_trades['position_id'] == i])[-1]
                             for i in df_trades['position_id'].unique()]
            Dates['Profit'] = [np.array(df_trades['profit'][df_trades['position_id'] == i])[-1]
                               for i in df_trades['position_id'].unique()]
            Dates = Dates[Dates['Time.1'] != 0]
            # Dates.to_csv("datos.csv")
            return (Dates.sort_values(by='Time.1', ascending=True).reset_index(drop=True))

        else:
            print("Login Fail")
            quit()
            return PermissionError
    else:
        print("MT5 Initialization Failed")
        quit()
        return ConnectionAbortedError

