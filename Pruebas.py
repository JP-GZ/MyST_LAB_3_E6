import pandas as pd

cuentas = pd.read_csv(r'.\files\Accounts.csv')
Nombres = list(cuentas['Name'])
Usuario = list(cuentas['Account'])
Password = list(cuentas['Password'])

print('Los nombres son:', Nombres)
Nombre = input('Ingrese nombre del integrante a analizar: gaby ')
print(cuentas['Account'][cuentas.Name == Nombre][0])


