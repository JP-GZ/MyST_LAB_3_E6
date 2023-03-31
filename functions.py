"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: functions.py : python script with general functions                                         -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""
import statistics
import MetaTrader5
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import yfinance


def f_leer_archivo():
    #cuenta = pd.read_csv(r'.\files\Accounts.csv')
    #nombres = list(cuenta['Name'])
    #print(f'Nombres disponibles:', nombres)
    #global nombre
    #nombre = input('Ingrese nombre cuenta a utilizar:')
    #uname = int(cuenta['Account'][cuenta.Name == nombre][0])
    #pword = str(cuenta['Password'][cuenta.Name == nombre][0])

    # Prueba
    uname = 5568903
    pword = 'Dn8UIDQw'
    # Ensure that all variables are the correct type

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

            return Dates.sort_values(by='Time.1', ascending=True).reset_index(drop=True)

        else:
            print("Login Fail")
            quit()
            return PermissionError
    else:
        print("MT5 Initialization Failed")
        quit()
        return ConnectionAbortedError


def f_pip_size(param_ins):
    #cuenta = pd.read_csv(r'.\files\Accounts.csv')
    #uname = int(cuenta['Account'][cuenta.Name == nombre][0])
    #pword = str(cuenta['Password'][cuenta.Name == nombre][0])
    
    uname = 5568903
    pword = 'Dn8UIDQw'
    
    trading_server = str('FxPro-MT5')  # Server must be a string
    try:
        MetaTrader5.initialize(login=uname, server= trading_server, password=pword)
        pip_size = int(0.1 / MetaTrader5.symbol_info(param_ins)._asdict().get('trade_tick_size'))
        return pip_size
    except:
        print(MetaTrader5.last_error())


def f_columnas_tiempos(param_data):
    param_data['open_time'] = [datetime.fromtimestamp(i) for i in param_data['Time']]
    param_data['close_time'] = [datetime.fromtimestamp(i) for i in param_data['Time.1']]
    param_data['time'] = (param_data['close_time'] - param_data['open_time']).apply(timedelta.total_seconds, 1)
    return param_data


def f_columnas_pips(param_data):
    param_data['pips'] = [
        (param_data['Price.1'].iloc[i] - param_data['Price'].iloc[i]) * f_pip_size(param_data['Symbol'].iloc[i])
        if param_data['Type'].iloc[i] == 'buy'
        else (param_data['Price'].iloc[i] - param_data['Price.1'].iloc[i]) * f_pip_size(param_data['Symbol'].iloc[i])
        for i in range(len(param_data))]
    param_data['pips_acm'] = param_data['pips'].cumsum()
    param_data['profit_acm'] = param_data['Profit'].cumsum()
    return param_data


def f_estadisticas_ba(param_data):
    Ops_totales = len(param_data)
    Ganadoras = len(param_data[param_data['Profit'] >= 0])
    Ganadoras_c = len(param_data[(param_data['Profit'] >= 0) & (param_data['Type'] == 'buy')])
    Ganadoras_v = len(param_data[(param_data['Profit'] >= 0) & (param_data['Type'] != 'buy')])
    Perdedoras = len(param_data[param_data['Profit'] < 0])
    Perdedoras_c = len(param_data[(param_data['Profit'] < 0) & (param_data['Type'] == 'buy')])
    Perdedoras_v = len(param_data[(param_data['Profit'] < 0) & (param_data['Type'] != 'buy')])
    Mediana_profit = statistics.median(param_data.sort_values(by='Profit')['Profit'])
    Mediana_pips = statistics.median(param_data.sort_values(by='pips')['pips'])
    r_efectividad = Ganadoras / Ops_totales
    r_proporcion = Ganadoras / Perdedoras
    r_efectividad_c = Ganadoras_c / Ops_totales
    r_efectividad_v = Ganadoras_v / Ops_totales

    valores = [Ops_totales, Ganadoras, Ganadoras_c, Ganadoras_v, Perdedoras, Perdedoras_c, Perdedoras_v, Mediana_profit,
               Mediana_pips, r_efectividad, r_proporcion, r_efectividad_c, r_efectividad_v]
    df_1_tabla = pd.DataFrame({'medida': ['Ops totales', 'Ganadoras', 'Ganadoras_c', 'Ganadoras_v', 'Perdedoras',
                                          'Perdedoras_c', 'Perdedoras_v', 'Mediana(Profit)', 'Mediana(Pips)',
                                          'r_efectividad', 'r_proporcion', 'r_efectividad_c', 'r_efectividad_v'],
                               'valor': np.round(valores, 2)})
    symbols = param_data['Symbol'].unique()
    df_2_ranking = pd.DataFrame({'symbol': param_data['Symbol'].unique(),
                                 'rank (%)': 100 * np.round([len(param_data[(param_data['Profit'] > 0) &
                                                                            (param_data['Symbol'] == symbols[i])]) /
                                                             len(param_data[param_data['Symbol'] == symbols[i]])
                                                             for i in range(len(symbols))], 2)
                                 })
    df_2_ranking = df_2_ranking.sort_values(by='rank (%)', ascending=False).reset_index(drop=True)

    return (df_1_tabla,df_2_ranking)

#%% Parte 2: Métricas de Atribución al Desempeño

def f_evolucion_capital(param_data):
    param_data['close_time'] = [i.strftime('%Y-%m-%d') for i in param_data['close_time']]
    param_data['timestamp'] = pd.to_datetime(param_data['close_time'])
    df = pd.DataFrame({'timestamp': pd.date_range(start='2/16/2023', end='3/2/2023')})
    df = df.fillna(0)
    df = df.set_index('timestamp')
    df = df.resample('D').sum()
    df['profit_d'] = df['Profit']
    df['profit_acm_d'] = df['Profit'].cumsum()
    df['capital_acm'] = df['profit_acm_d'] + 100000

    return df

def f_estadisiticas_mad(riskfree, df):
    # Sacamos el radio de Sharpe inicial
    rp = np.log(df.capital_acm) - np.log(df.capital_acm.shif(1))
    rp = rp.fillna(0)
    sdp = rp.std()
    rp_mean = rp.mean()
    rf = riskfree / 252
    sharpe_og = (rp_mean - rf) / sdp

    # Actualizamos el Sharpe Ratio
    benchmark = yfinance.download('^GSPC', '2023-02-16', '2023-03-2')
    benchmark = benchmark['Adj Close']
    benchmark = pd.DataFrame(benchmark)

    rp_benchmark = np.log(benchmark) - np.log(benchmark.shift(1))
    rp_benchmark = pd.DataFrame(rp_benchmark)
    rp_benchmark = rp_benchmark.rename(columns={'Adj Close': 'capital_acm'})

    rp_rb = pd.concat([benchmark, rp_benchmark], axis=1)
    rp_rb['Rp-Rb'] = rp_rb['capital_acm'] - rp_rb['Adj Close']

    std_sra = rp_rb['Rp-Rb'].std()
    r_trader = rp_rb['capital_acm'].mean()
    rp_benchmark = rp_rb['Adj Close'].mean()

    sharpe_actualizado = (r_trader - rp_benchmark) / std_sra

    minimum = df.capital_acm.min()
    maximum = df.capital_acm.max()

    # Sacamos el drawdown
    drawdown_cap = df.profit_acm_d.min()
    date_drawdown = (df.loc[df.profit_acm_d == drawdown_cap].index.values[0])
    date_drawdown = np.datetime_as_string(date_drawdown, unit='D')

        #Creamos variables inciales para loop
    temp = 0
    peak = 0
    du = 0
    b =df.profit_acm_d

        # Condicionales que vimos en clase
    for i in range(len(b)):
        if b[i] < b[i - 1] and b[i] < peak:
            peak = b[i]
            temp = 0

        elif b[i] > b[i - 1]:
            temp = b[i]

        if du < (temp-peak):
            du = temp - peak

    drawup_cap = du
    date_drawdown = np.datetime_as_string(df.loc[df.capital_acm == minimum].index.values[0], unit="D")

    data = [
        ['sharpe_original', 'Cantidad', sharpe_og, "Sharpe Ratio Fórmula Original"],
        ['sharpe_actualizado', 'Cantidad', sharpe_actualizado, "Sharpe Ratio Fórmula Ajustada"],
        ['drawdown_capi', 'Fecha Inicial', date_drawdown, "Fecha inicial del DrawDown de Capital"],
        ['drawdown_capi', 'Fecha Final', date_drawdown, "Fecha final del DrawDown de Capital"],
        ['drawdown_capi', 'Fecha Final', dd, "Máxima pérdida flotante registrada"],
        ['drawup_capi', 'Fecha Inicial', date_drawup, "Fecha inicial del DrawUp de Capital"],
        ['drawup_capi', 'Fecha Final', date_drawup, "Fecha final del DrawUp de Capital"],
        ['drawup_capi', 'Fecha Final', drawup_cap, "Máxima ganancia flotante registrada"]
    ]
    # Creamos un dataframe con todos los datos que acabamos de sacar
    df = pd.DataFrame(data, columns = ['Metrica', '', 'Valor', 'Descripcion'])

    return df, dd, drawup_cap

































# Behavioral finance 

def f_columnas_pips2(param_data):
    paran_data['float_pips'] = [(param_data['float_price'].iloc[i]
    - param_data['Price'].iloc[i])*f_pip_size(param_data['Symbol'].iloc[i])
    if param_data['Type'].iloc[i]=='buy'
    else (param_data['Price'].iloc[i]- param_data['float_price'].iloc[i])*
    f_pip_size(param_data['Symbol'].iloc[i])
    for i in range(len(param_data))]
    return param_data



