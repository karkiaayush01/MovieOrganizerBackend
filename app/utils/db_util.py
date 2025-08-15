from pymongo import MongoClient
import os

_client = None
_db = None
_DB_NAME = 'MovieRecommender'
MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_URI", None)

def get_db():
    global _client
    global _db
    global MONGO_CONNECTION_STRING

    if _db is not None:
        return _db

    if _client is not None:
        _db = _client[_DB_NAME]  
        return _db

    if MONGO_CONNECTION_STRING is None:
        print("❌ MONGO_CONNECTION_URI not set in environment.")
        return None 
    
    try:
        _client = MongoClient(MONGO_CONNECTION_STRING)
        _db = _client[_DB_NAME]  
        return _db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {str(e)}")
        return None