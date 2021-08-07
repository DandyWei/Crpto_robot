from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
import logging
import time
import threading
import os


# https://docs.python.org/3/library/logging.html#logging-levels
logging.basicConfig(level=logging.INFO,
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")


def print_stream_data_from_stream_buffer(binance_websocket_api_manager):
    while True:
        if binance_websocket_api_manager.is_manager_stopping():
            exit(0)
        oldest_stream_data_from_stream_buffer = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(0.01)
        else:
            print(oldest_stream_data_from_stream_buffer)


# configure api key and secret for binance.com
api_key = 'nux5568AFIq0eL63qdQpsFHgG08nKGg3aO3FRDduzxhxOTx3l3FN1kpMTyXbE8it'
api_secret = 'kgj4GJz65eqaumiBH0Bgu4L7eaG4eVqJc9u6UZ12ykChYaMgbN6fZDzYr5EO0fyl'

# create instances of BinanceWebSocketApiManager
ubwa_com = BinanceWebSocketApiManager(exchange="binance.com")

# create the userData streams
user_stream_id = ubwa_com.create_stream('arr', '!userData', api_key=api_key, api_secret=api_secret)

# start a worker process to move the received stream_data from the stream_buffer to a print function
worker_thread = threading.Thread(target=print_stream_data_from_stream_buffer, args=(ubwa_com,))
worker_thread.start()

# configure api key and secret for binance.com Isolated Margin
api_key = 'nux5568AFIq0eL63qdQpsFHgG08nKGg3aO3FRDduzxhxOTx3l3FN1kpMTyXbE8it'
api_secret = 'kgj4GJz65eqaumiBH0Bgu4L7eaG4eVqJc9u6UZ12ykChYaMgbN6fZDzYr5EO0fyl'

# create instances of BinanceWebSocketApiManager
ubwa_com_im = BinanceWebSocketApiManager(exchange="binance.com-isolated_margin")

# create the userData streams
user_stream_id_im = ubwa_com_im.create_stream('arr', '!userData', symbols="dogeusdt", api_key=api_key, api_secret=api_secret)

# start a worker process to move the received stream_data from the stream_buffer to a print function
worker_thread = threading.Thread(target=print_stream_data_from_stream_buffer, args=(ubwa_com_im,))
worker_thread.start()

# monitor the streams
while True:
    ubwa_com.print_stream_info(user_stream_id)
    ubwa_com_im.print_stream_info(user_stream_id_im)
    time.sleep(1)
