from os import getenv
from pymongo import MongoClient
from bson import ObjectId

if getenv("MONGO_URI") is None:
    raise ValueError("MONGO_URI environment variable is not set.")


def get_db():
    """
    Connect to the MongoDB database and return the database object.
    """
    client = MongoClient(host=getenv("MONGO_URI"))
    db = client.get_default_database()
    if db is None:
        raise ValueError("Failed to connect to the database. Please check your MONGO_URI.")
    return db