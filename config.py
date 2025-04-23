import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_USERNAME = os.environ.get("MONGO_USERNAME", "adminn")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "helloworld")
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
MONGO_DB = os.environ.get("MONGO_DB", "smart_estate_compass")
MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

# API Keys
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
TRADING_ECONOMICS_API_KEY = os.environ.get("TRADING_ECONOMICS_API_KEY", "")

# API Endpoints
TRADING_ECONOMICS_BASE_URL = "https://api.tradingeconomics.com"
GOOGLE_MAPS_GEOCODING_API = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_MAPS_PLACES_API = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
OPENSTREETMAP_NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
OPENWEATHERMAP_API = "https://api.openweathermap.org/data/2.5/forecast"

# Application settings
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
PORT = int(os.environ.get("PORT", 5000))
