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

