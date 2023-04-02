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
import MetaTrader5 as mt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import yfinance

def f_pip_size(param_ins):
    pips = pd.read_csv("files/instruments_pips.csv")
    try:
        pip_size = 1 / float(
            pips[pips["Instrument"] == param_ins[0:3] + "_" + param_ins[3:]]["TickSize"])
    except:
        pip_size = 100
    return pip_size

def f_columnas_tiempos(param_data):
    param_data['opentime'] = [datetime.fromtimestamp(i) for i in param_data['Time']]
    param_data['closetime'] = [datetime.fromtimestamp(i) for i in param_data['Time.1']]
    param_data['TiempoF'] = (param_data['closetime'] - param_data['opentime']).apply(timedelta.total_seconds, 1)
    return param_data


def f_columnas_pips(param_data):
    for i in range(len(param_data)):
        if param_data['Type'].iloc[i] == 'buy':
            param_data.loc[i,'pips'] = (param_data['Price.1'].iloc[i] - param_data['Price'].iloc[i]) * f_pip_size(param_data['Symbol'].iloc[i])
        else:
            param_data.loc[i, 'pips'] =  (param_data['Price'].iloc[i] - param_data['Price.1'].iloc[i]) *f_pip_size(param_data['Symbol'].iloc[i])
    param_data['pips_acm'] = param_data['pips'].cumsum()
    param_data['profit_acm'] = param_data['Profit'].cumsum()
    return param_data


def f_estadisticas_ba(param_data):
    df_1_tabla = pd.DataFrame()
    valores = [len(param_data), len(param_data[param_data['Profit'] >= 0]), len(param_data[(param_data['Profit'] >= 0) & (param_data['Type'] == 'buy')]),
               len(param_data[(param_data['Profit'] >= 0) & (param_data['Type'] != 'buy')]), len(param_data[param_data['Profit'] < 0]),
               len(param_data[(param_data['Profit'] < 0) & (param_data['Type'] == 'buy')]), len(param_data[(param_data['Profit'] < 0) & (param_data['Type'] != 'buy')]),
               statistics.median(param_data.sort_values(by='Profit')['Profit']),statistics.median(param_data.sort_values(by='pips')['pips']),
               (len(param_data[param_data['Profit'] >= 0])/len(param_data)), (len(param_data[param_data['Profit'] >= 0])/len(param_data[param_data['Profit'] < 0])),
               len(param_data[(param_data['Profit'] >= 0) & (param_data['Type'] == 'buy')])/len(param_data), len(param_data[(param_data['Profit'] >= 0) & (param_data['Type'] != 'buy')])/len(param_data)]
    df_1_tabla["Medida"] = ['Ops totales', 'Ganadoras', 'Ganadoras_c', 'Ganadoras_v', 'Perdedoras',
                             'Perdedoras_c', 'Perdedoras_v', 'Mediana(Profit)', 'Mediana(Pips)',
                             'r_efectividad', 'r_proporcion', 'r_efectividad_c', 'r_efectividad_v']
    df_1_tabla["Valor"] = np.round(valores, 2)
    symbols = param_data['Symbol'].unique()
    rank = []
    for i in symbols:
        rank.append(
            round(len(param_data[(param_data['Profit'] > 0) & (param_data['Symbol'] == i)]) / len(param_data[param_data['Symbol'] == i]) * 100, 2))
    df_2_ranking = pd.DataFrame({'Symbol': symbols, 'rank %': rank})

    return (df_1_tabla,df_2_ranking)

#%% Parte 2: Métricas de Atribución al Desempeño


def f_evolucion_capital(param_data):
    param_data['timestamp'] = pd.to_datetime(param_data['closetime'].dt.date)
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

def f_be_de(param_data):
    ocurrencias = []
    cantidad_ocurrencias = 0
    resultados = {'ocurrencias': ocurrencias, 'cantidad': cantidad_ocurrencias}
    
    # Agregar columna de capital acumulado
    param_data['capital_acm'] = param_data['profit_acm'] + 100000
    
    for i in range(len(param_data) - 1):
        # Identificar la operación ganadora
        if param_data.iloc[i]['Profit'] > 0:
            operacion_ganadora = param_data.iloc[i]
            # Identificar la operación perdedora
            j = i + 1
            while j < len(param_data) and param_data.iloc[j]['Profit'] >= 0:
                j += 1
            if j < len(param_data):
                operacion_perdedora = param_data.iloc[j]
                # Calcular ratios
                ratio_cp_cg = abs(operacion_perdedora['Profit'] / operacion_ganadora['Profit'])
                ratio_cp_profit_acm = abs(operacion_perdedora['Profit'] / operacion_perdedora['profit_acm'])
                ratio_cg_profit_acm = abs(operacion_ganadora['Profit'] / operacion_ganadora['profit_acm'])
                
                # Verificar si se cumple el sesgo
                if ratio_cp_cg > 1 and ratio_cp_profit_acm > ratio_cg_profit_acm:
                    # Guardar información de las operaciones
                    ocurrencia = {
                        f'ocurrencia_{cantidad_ocurrencias + 1}': {
                            'timestamp': operacion_ganadora['close_time'],
                            'operaciones': {
                                'ganadora': {
                                    'instrumento': operacion_ganadora['Symbol'],
                                    'volumen': operacion_ganadora['Volume'],
                                    'sentido': operacion_ganadora['Type'],
                                    'profit_ganadora': operacion_ganadora['Profit']
                                },
                                'perdedora': {
                                    'instrumento': operacion_perdedora['Symbol'],
                                    'volumen': operacion_perdedora['Volume'],
                                    'sentido': operacion_perdedora['Type'],
                                    'profit_perdedora': operacion_perdedora['Profit']
                                }
                            },
                            'ratio_cp_profit_acm': ratio_cp_profit_acm,
                            'ratio_cg_profit_acm': ratio_cg_profit_acm,
                            'ratio_cp_cg': ratio_cp_cg
                        }
                    }
                    ocurrencias.append(ocurrencia)
                    cantidad_ocurrencias += 1

    resultados['cantidad'] = cantidad_ocurrencias
    resultados['ocurrencias'] = ocurrencias
    return resultados

