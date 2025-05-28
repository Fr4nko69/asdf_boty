from binance.client import Client
import time
import requests
from datetime import datetime

# 👉 Rellena estos dos campos
TELEGRAM_TOKEN = '7994759392:AAGV3DfTHg_yTckFeGHyfzJIIwrmOsYIgbY'
TELEGRAM_CHAT_ID = '750141377'

variacion = 5  # Variación en los últimos 30 minutos en porcentaje
variacion_100 = 7  # Variación si tiene menos de 100k de volumen
variacionfast = 2  # Variación en los últimos 2 minutos en porcentaje

client = Client('', '', tld='com')

def escape_markdown(text):
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def enviar_telegram(mensaje):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': mensaje,  'parse_mode': 'MarkdownV2'}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f'Error al enviar mensaje a Telegram: {e}')


def buscarticks():
    ticks = []
    lista_ticks = client.futures_symbol_ticker()
    print('Numero de monedas encontradas #' + str(len(lista_ticks)))

    for tick in lista_ticks:
        if tick['symbol'][-4:] != 'USDT':
            continue
        ticks.append(tick['symbol'])

    print('Numero de monedas encontradas en el par USDT: #' + str(len(ticks)))
    return ticks


def get_klines(tick):
    klines = client.futures_klines(symbol=tick, interval=Client.KLINE_INTERVAL_1MINUTE, limit=30)
    return klines


def infoticks(tick):
    info = client.futures_ticker(symbol=tick)
    return info


def human_format(volumen):
    magnitude = 0
    while abs(volumen) >= 1000:
        magnitude += 1
        volumen /= 1000.0
    return '%.2f%s' % (volumen, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def porcentaje_klines(tick, klines, knumber):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    inicial = float(klines[0][4])
    final = float(klines[knumber][4])

    # LONG
    if inicial > final:
        result = round(((inicial - final) / inicial) * 100, 2)
        if result >= variacion:
            info = infoticks(tick)
            volumen = float(info['quoteVolume'])
            if volumen > 100000000 or result >= variacion_100:
                msg = (f'*🟢 LONG: `{escape_markdown(tick)}`* 🟢\n\n'
                       f'Variación: {result}%\n'
                       f'Volumen: {human_format(volumen)}\n'
                       f'Precio Máx: {info["highPrice"]}\n'
                       f'Precio Mín: {info["lowPrice"]}\n\n'
                       f'{now}')                       
                print(msg + '\n')
                enviar_telegram(msg)

    # SHORT
    if final > inicial:
        result = round(((final - inicial) / inicial) * 100, 2)
        if result >= variacion:
            info = infoticks(tick)
            volumen = float(info['quoteVolume'])
            if volumen > 100000000 or result >= variacion_100:
                msg = (f'*🔴 SHORT: `{escape_markdown(tick)}`* 🔴\n\n'
                       f'Variación: {result}%\n'
                       f'Volumen: {human_format(volumen)}\n'
                       f'Precio Máx: {info["highPrice"]}\n'
                       f'Precio Mín: {info["lowPrice"]}\n\n'
                       f'{now}')
                print(msg + '\n')
                enviar_telegram(msg)

    # FAST
    if knumber >= 3:
        inicial = float(klines[knumber - 2][4])
        final = float(klines[knumber][4])
        if inicial < final:
            result = round(((final - inicial) / inicial) * 100, 2)
            if result >= variacionfast:
                info = infoticks(tick)
                volumen = float(info['quoteVolume'])
                msg = (f'*⚡🔴⚡FAST SHORT: `{escape_markdown(tick)}`*⚡🔴⚡\n\n'
                       f'Variación: {result}%\n'
                       f'Volumen: {human_format(volumen)}\n'
                       f'Precio Máx: {info["highPrice"]}\n'
                       f'Precio Mín: {info["lowPrice"]}\n\n'
                       f'{now}')
                print(msg + '\n')
                enviar_telegram(msg)


while True:
    ticks = buscarticks()
    print('Escaneando monedas...\n')
    for tick in ticks:
        klines = get_klines(tick)
        knumber = len(klines)
        if knumber > 0:
            knumber -= 1
            porcentaje_klines(tick, klines, knumber)
    print('Esperando 30 segundos...\n')
    time.sleep(30)
