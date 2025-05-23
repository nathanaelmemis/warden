from typing import Callable
from pymongo import MongoClient
import os

from utils import exception
from utils.logging import logger

db = MongoClient(os.environ["MONGODB_URL"]).warden