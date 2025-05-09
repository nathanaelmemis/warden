from pymongo import MongoClient
import os

db = MongoClient(os.environ["MONGODB_URL"])