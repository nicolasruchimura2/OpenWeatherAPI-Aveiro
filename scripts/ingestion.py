import os
from datetime import datetime, timezon
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
