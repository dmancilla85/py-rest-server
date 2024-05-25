import logging
import websocket
from os import environ as env
from pymongo import MongoClient


# add your own check function to the healthcheck
def mongo_available():
    try:
        client = MongoClient(env['MONGODB_CONN'])
        info = client.server_info()
        return True, {"status": "OK", "info": str(info)}
    except Exception as e:
        return False, {"status": "ERROR", "info": e}


def check_websocket(url):
    ws = websocket.WebSocket()

    try:
        ws.connect(url)
        ws.ping("Test whether the connection is alive")
        response = ws.recv()
        return response is not None

    except Exception as e:
        logging.error(f'WS ({url}) Health Error: {e}')
        return False




