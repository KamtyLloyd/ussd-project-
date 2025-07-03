import requests
import os
from datetime import datetime
from geopy.geocoders import Nominatim

OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geolocator = Nominatim(user_agent="farmer_weather_app")
        self.weather_cache = {}
        
    def _get_coordinates(self, location):
        """Get latitude and longitude from location name"""
        try:
            location_data = self.geolocator.geocode(location)
            if location_data:
                return location_data.latitude, location_data.longitude
            return None, None
        except Exception as e:
            print(f"Error getting coordinates: {e}")
            return None, None

    def _get_weather_data(self, endpoint, params):
        """Make request to OpenWeatherMap API with enhanced error handling"""
        try:
            if not OPENWEATHERMAP_API_KEY:
                print("ERROR: OpenWeatherMap API key is not configured")
                return None
                
            # Add timeout to prevent hanging (10 seconds for connect, 30 seconds for read)
            response = requests.get(
                endpoint, 
                params=params,
                timeout=(10, 30)  # 10s connect timeout, 30s read timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print("ERROR: Request to weather API timed out")
            return None
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            return None
        except Exception as e:
            print(f"Unexpected error in _get_weather_data: {e}")
            return None

    def get_weather(self, location):
        """Get current weather for a location"""
        if not location:
            return {"error": "No location provided"}
            
        print(f"Getting weather for location: {location}")
        lat, lon = self._get_coordinates(location)
        if not lat or not lon:
            return {"error": f"Could not find coordinates for location: {location}"}
            
        params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHERMAP_API_KEY,
            'units': 'metric'
        }
        
        current_weather = self._get_weather_data(
            f"{self.base_url}/weather",
            params
        )
        
        if not current_weather:
            return {"error": "Failed to get weather data"}
            
        return {
            "temperature": current_weather['main']['temp'],
            "description": current_weather['weather'][0]['description'],
            "humidity": current_weather['main']['humidity'],
            "wind_speed": current_weather['wind']['speed'],
            "timestamp": datetime.now().isoformat()
        }

    def get_forecast(self, location):
        """Get 5-day weather forecast"""
        if not location:
            return {"error": "No location provided"}
            
        print(f"Getting forecast for location: {location}")
        lat, lon = self._get_coordinates(location)
        if not lat or not lon:
            return {"error": f"Could not find coordinates for location: {location}"}
            
        params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHERMAP_API_KEY,
            'units': 'metric'
        }
        
        forecast = self._get_weather_data(
            f"{self.base_url}/forecast",
            params
        )
        
        if not forecast:
            return {"error": "Failed to get forecast data"}
            
        return {
            "city": forecast['city']['name'],
            "forecast": forecast['list'][:5]  # Get first 5 days
        }
