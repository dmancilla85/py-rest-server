import logging
from threading import Lock
from pymongo import MongoClient
from os import environ as env


class SingletonMeta(type):
    _instances = {}
    _locks = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._locks:
            cls._locks[cls] = Lock()
        if cls not in cls._instances:
            with cls._locks[cls]:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class MongoDbService(metaclass=SingletonMeta):

    def __init__(self):
        self.client = None
        self.db = None

        self._initialize_client()

    def get_info(self):
        if not self.is_connected():
            return "Disconnected"

        return self.client.server_info()

    def is_connected(self):
        return self.db is not None

    def _initialize_client(self):
        try:
            self.client = MongoClient(env['MONGODB_CONN'])
            self.db = self.client[env['MONGODB_DB']]
        except Exception as e:
            logging.error(f"Error connecting server: {e}")

    def get_collection(self, collection_name):
        if not self.is_connected():
            return None

        return self.db[collection_name]
