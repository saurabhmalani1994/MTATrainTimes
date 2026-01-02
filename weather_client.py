#!/usr/bin/env python3

"""
Weather API Client - Fetches current weather from NOAA/weather.gov
Uses public API without authentication
"""

import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class WeatherData:
    """Container for weather information"""
    
    def __init__(self):
        self.temperature = None
        self.real_feel = None
        self.condition = None
        self.high_temp = None
        self.low_temp = None
        self.timestamp = None
        self.date_str = None

class WeatherClient:
    """Client for NOAA Weather.gov API"""
    
    def __init__(self):
        """Initialize weather client"""
        # Station: KWO35 (Chicago area)
        # SAME Code: 036047 (Cook County, IL)
        self.station_id = "KWO35"
        self.same_code = "036047"
        
        # NOAA API endpoints
        self.observations_url = f"https://api.weather.gov/stations/{self.station_id}/observations/latest"
        self.points_url = f"https://api.weather.gov/points/41.8781,-87.6298"  # Chicago coords for KWO35
        
    def fetch_weather(self):
        """
        Fetch current weather from NOAA API
        
        Returns:
            WeatherData object with current conditions, or None on error
        """
        try:
            weather = WeatherData()
            weather.timestamp = datetime.now()
            weather.date_str = weather.timestamp.strftime("%a, %b %-d %Y").replace(" 0", " ")
            # Format: "Fri, Jan 2 2026"
            
            # Fetch observations
            obs_response = requests.get(
                self.observations_url,
                timeout=10,
                headers={"User-Agent": "MTA-Display (https://github.com)"}
            )
            obs_response.raise_for_status()
            obs_data = obs_response.json()
            
            # Extract data from properties
            properties = obs_data.get("properties", {})
            
            # Temperature (convert from Celsius to Fahrenheit if needed)
            temp_c = properties.get("temperature", {}).get("value")
            if temp_c is not None:
                weather.temperature = int(round(temp_c * 9/5 + 32))
            
            # Wind chill / Real feel (use windChill or apparentTemperature)
            wind_chill_c = properties.get("windChill", {}).get("value")
            if wind_chill_c is not None:
                weather.real_feel = int(round(wind_chill_c * 9/5 + 32))
            
            # Weather condition from shortForecast
            short_forecast = properties.get("shortForecast", "Unknown")
            weather.condition = short_forecast.split(",")[0].strip()  # Get first part
            
            # Try to get forecast for high/low temps
            forecast_url = properties.get("forecast")
            if forecast_url:
                forecast_response = requests.get(
                    forecast_url,
                    timeout=10,
                    headers={"User-Agent": "MTA-Display (https://github.com)"}
                )
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()
                
                # Get today's forecast (first two periods = day and night)
                periods = forecast_data.get("properties", {}).get("periods", [])
                if len(periods) >= 2:
                    # Find daytime forecast
                    for period in periods:
                        if period.get("isDaytime"):
                            temp = period.get("temperature")
                            if temp and not weather.high_temp:
                                weather.high_temp = temp
                        else:
                            temp = period.get("temperature")
                            if temp and not weather.low_temp:
                                weather.low_temp = temp
                    
                    # If we got both, we're done
                    if weather.high_temp and weather.low_temp:
                        pass
            
            # Fallback: if no forecast, use current temp ±5
            if not weather.high_temp and weather.temperature:
                weather.high_temp = weather.temperature + 2
            if not weather.low_temp and weather.temperature:
                weather.low_temp = weather.temperature - 3
            
            logger.info(
                f"Weather fetched - Temp: {weather.temperature}°F, "
                f"Condition: {weather.condition}, "
                f"High: {weather.high_temp}°F, Low: {weather.low_temp}°F"
            )
            
            return weather
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch weather: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing weather data: {e}")
            return None
    
    def get_weather_icon_code(self, condition_str):
        """
        Get weather icon code based on condition string
        
        Args:
            condition_str: Weather condition (e.g., "Sunny", "Cloudy", "Rainy")
            
        Returns:
            Icon code for rendering
        """
        condition = condition_str.lower() if condition_str else ""
        
        if "sunny" in condition or "clear" in condition:
            return "sunny"
        elif "cloudy" in condition or "overcast" in condition:
            return "cloudy"
        elif "rain" in condition or "wet" in condition:
            return "rainy"
        elif "snow" in condition or "flurries" in condition:
            return "snowy"
        elif "thunder" in condition:
            return "stormy"
        elif "fog" in condition or "mist" in condition:
            return "foggy"
        elif "wind" in condition:
            return "windy"
        elif "partly" in condition:
            return "partly_cloudy"
        else:
            return "unknown"
