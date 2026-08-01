from services.mongodb_service import MongoDbService


def mongo_available():
    try:
        svc = MongoDbService()
        info = svc.get_info()
        return True, {"status": "OK", "info": str(info)}
    except Exception as e:
        return False, {"status": "ERROR", "info": str(e)}


