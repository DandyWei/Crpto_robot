import pandas as pd
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager

# real one
api_Key = 'nux5568AFIq0eL63qdQpsFHgG08nKGg3aO3FRDduzxhxOTx3l3FN1kpMTyXbE8it'
api_Keyapi_Key ='kgj4GJz65eqaumiBH0Bgu4L7eaG4eVqJc9u6UZ12ykChYaMgbN6fZDzYr5EO0fyl'
client = Client(api_Key, api_Keyapi_Key)

bsm = BinanceSocketManager(client)

socket = bsm.trade_socket("BTCUSDT")

await socket.__aenter__()
msg = await socket.recv()
print(msg)
