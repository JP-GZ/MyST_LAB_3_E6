"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: functions.py : python script with general functions                                         -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""
import MetaTrader5
import pandas as pd


def f_leer_archivo():
    cuenta = pd.read_csv(r'.\files\Accounts.csv')
    nombres = list(cuenta['Name'])

    print(f'Nombres disponibles:', nombres)
    nombre = input('Ingrese nombre cuenta a utilizar:')
    uname = int(cuenta['Account'][cuenta.Name == nombre][0])
    pword = str(cuenta['Password'][cuenta.Name == nombre][0])
    # Ensure that all variables are the correct type

    trading_server = str('FxPro-MT5')  # Server must be a string
    # Attempt to start MT5
    if MetaTrader5.initialize(login=uname, password=pword, server=trading_server):
        # Login to MT5
        if MetaTrader5.login(login=uname, password=pword, server=trading_server):
            return True
        else:
            print("Login Fail")
            quit()
            return PermissionError
    else:
        print("MT5 Initialization Failed")
        quit()
        return ConnectionAbortedError


def status_c():
    MetaTrader5.account_info()


f_leer_archivo()
