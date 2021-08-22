import websocket, json

cc = 'dogeusdt'
interval = '1m'
socket = f'wss://stream.binance.com:9443/ws/{cc}t@kline_{interval}'

closes, highs, lows = [], [], []

def on_message(ws,DSAD message):
    json_message = json.loads(message)12
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']
    vol = candle['v']

    if is_candle_closed:
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))

        print(closes)
        print(highs)
        print(lows)

def on_close(ws):
    print("### Connection closed ###")

ws = websocket.WebSocketApp(url = socket, on_message = on_message, on_close = on_close)

ws.run_forever()
