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
    param_data['timestamp'] = pd.to_datetime(param_data['close_time'].dt.date)
    df = pd.DataFrame(index=pd.date_range(start='2/16/2023', end='3/2/2023'), columns=['profit_d', 'profit_acm_d', 'capital_acm'])
    df['profit_d'] = param_data.groupby('timestamp')['Profit'].sum()
    df['profit_acm_d'] = df['profit_d'].cumsum()
    df['capital_acm'] = df['profit_acm_d'] + 100000
    return df



def f_estadisiticas_mad(riskfree, df):
    # Calculate initial Sharpe ratio
    returns = df.capital_acm.pct_change().fillna(0)
    sdp = returns.std()
    rp_mean = returns.mean()
    rf = riskfree / 252
    sharpe_og = (rp_mean - rf) / sdp

    # Update Sharpe ratio using benchmark
    benchmark = yf.download('^GSPC', '2023-02-16', '2023-03-02')['Adj Close']
    rp_benchmark = benchmark.pct_change().fillna(0)
    rp_rb = pd.concat([df.capital_acm, rp_benchmark], axis=1)
    rp_rb['Rp-Rb'] = rp_rb['capital_acm'] - rp_rb['Adj Close']
    std_sra = rp_rb['Rp-Rb'].std()
    r_trader = rp_rb['capital_acm'].mean()
    rp_benchmark = rp_rb['Adj Close'].mean()
    sharpe_actualizado = (r_trader - rp_benchmark) / std_sra

    # Calculate drawdown and drawup
    cum_returns = df.capital_acm.values
    previous_peaks = np.maximum.accumulate(cum_returns)
    drawdowns = previous_peaks - cum_returns
    drawdown_cap = drawdowns.min()
    date_drawdown = df.index[drawdowns.argmin()].strftime('%Y-%m-%d')
    drawups = np.diff(previous_peaks)
    drawup_cap = drawups.max()
    date_drawup = df.index[np.argmax(drawups)].strftime('%Y-%m-%d')

    # Create DataFrame with results

    # Create dictionary with results
    data = {
        'Metrica': ['sharpe_original', 'sharpe_actualizado', 'drawdown_capi', 'drawdown_capi', 'drawdown_capi',
                    'drawup_capi', 'drawup_capi', 'drawup_capi'],
        '': ['Cantidad', 'Cantidad', 'Fecha Inicial', 'Fecha Final', 'Máxima pérdida flotante registrada',
             'Fecha Inicial', 'Fecha Final', 'Máxima ganancia flotante registrada'],
        'Valor': [sharpe_og, sharpe_actualizado, date_drawdown, date_drawdown, drawdown_cap, date_drawup, date_drawup,
                  drawup_cap],
        'Descripcion': ["Sharpe Ratio Fórmula Original", "Sharpe Ratio Fórmula Ajustada",
                        "Fecha inicial del DrawDown de Capital", "Fecha final del DrawDown de Capital",
                        "Máxima pérdida flotante registrada", "Fecha inicial del DrawUp de Capital",
                        "Fecha final del DrawUp de Capital", "Máxima ganancia flotante registrada"]
    }

    # Create DataFrame with dictionary
    df_results = pd.DataFrame(data)

    return df_results, dd, drawup_cap


#%% Behavioral finance 

def f_columnas_pips2(param_data):
    param_data['float_pips'] = [(param_data['float_price'].iloc[i]-param_data['Price'].iloc[i])*f_pip_size(param_data['Symbol'].iloc[i])
                if param_data['Type'].iloc[i]== 'buy'
                else (param_data['Price'].iloc[i]-param_data['float_price'].iloc[i])*f_pip_size(param_data['Symbol'].iloc[i])
                for i in range(len(param_data))]
    return param_data

def f_be_de_1(param_data):
    # Filtrado de operaciones ganadoras (operaciones ancla)
    param_data['capital_acm'] = param_data['profit_acm'] + 100000
    ganadoras = param_data[param_data.Profit > 0]
    ganadoras = ganadoras.reset_index(drop=True)
    ganadoras["Ratio"] = (ganadoras["Profit"] / abs(ganadoras["profit_acm"]))

    perdedoras = param_data[param_data.Profit < 0]
    perdedoras = perdedoras.reset_index(drop=True)
    perdedoras["Ratio"] = (perdedoras["Profit"] / abs(perdedoras["profit_acm"]))

    df_anclas = ganadoras.loc[:, ['close_time', "open_time", 'Type', "Symbol",'Profit', "profit_acm", "capital_acm", "Ratio", "Time", "Time.1", "Price", "Volume"]]                         
    df_anclas = df_anclas.reset_index(drop=True)
    
    # Criterio de selección de operaciones abiertas por cada ancla
    ocurrencias = []
    file_list = []
    for x in df_anclas.index:
        df = param_data[(param_data.open_time <= df_anclas["close_time"][x]) &
                        (param_data.close_time > df_anclas["close_time"][x])].loc[:,
             ['Type', 'Symbol', 'Volume', 'Profit', "Price", "pips"]]
        df['close_time_ancla'] = pd.Timestamp(df_anclas['close_time'][x])
        file_list.append(df)
        ocurrencias.append(len(df))
    all_df = pd.concat(file_list, ignore_index=True)

    # Descarga de precios para cada operación abierta
    float_price = []
  
    for i in range(len(all_df)):
        utc_from = datetime(all_df['close_time_ancla'][i].year,
                            all_df['close_time_ancla'][i].month,
                            all_df['close_time_ancla'][i].day) 
        utc_to = datetime(all_df['close_time_ancla'][i].year+1,
                            all_df['close_time_ancla'][i].month+1,
                            all_df['close_time_ancla'][i].day+1) 
        symbol = all_df['Symbol'][i]
        ticks = mt.copy_ticks_range(symbol, utc_from, utc_to, mt.COPY_TICKS_ALL)
        ticks_frame = pd.DataFrame(ticks)
        ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
        tick_time = next(x for x in ticks_frame['time'] if x >= all_df['close_time_ancla'][i])
        price = ticks_frame.loc[ticks_frame['time'] == tick_time]
        if all_df["Type"][i] == "buy":
            price = price["bid"].mean()
        else:
            price = price["ask"].mean()
        float_price.append(price)
        float_prices = pd.DataFrame(columns=['float_price'], data=float_price)

    all_df = all_df.join(float_prices)

    all_df = f_columnas_pips2(all_df)
    all_df["float_P&L"] = (all_df["Profit"] / all_df["pips"]) * all_df["float_pips"]
    all_df = all_df[all_df['float_P&L'] < 0].reset_index(drop=True)

    return all_df, df_anclas
def f_be_de2(param_data):
    # Filtrado de operaciones ancla para ganadoras 
    param_data['capital_acm'] = param_data['profit_acm'] + 100000
    ganadoras = param_data[param_data.Profit > 0]
    ganadoras = ganadoras.reset_index(drop=True)
    ganadoras["Ratio"] = (ganadoras["Profit"] / abs(ganadoras["profit_acm"]))
    perdedoras = param_data[param_data.Profit < 0]
    perdedoras = perdedoras.reset_index(drop=True)
    perdedoras["Ratio"] = (perdedoras["Profit"] / abs(perdedoras["profit_acm"]))

    df_anclas = ganadoras.loc[:, ['close_time', "open_time", 'Type', "Symbol",'Profit', "profit_acm", "capital_acm", "Ratio", "Time", "Time.1", "Price", "Volume"]]                         
    df_anclas = df_anclas.reset_index(drop=True)
    

    #selección de operaciones abiertas por cada ancla
    ocurrencias = []
    file_list = []
    for x in df_anclas.index:
        df = param_data[(param_data.open_time <= df_anclas["close_time"][x]) &
                        (param_data.close_time > df_anclas["close_time"][x])].loc[:,
             ['Type', 'Symbol', 'Volume', 'Profit', "Price", "pips"]]
        df['close_time_ancla'] = pd.Timestamp(df_anclas['close_time'][x])
        file_list.append(df)
        ocurrencias.append(len(df))
    all_df = pd.concat(file_list, ignore_index=True)

    # Descarga de precios para cada operación abierta
    float_price = []
    if not mt.initialize():
        print(mt.last_error())
        quit()
