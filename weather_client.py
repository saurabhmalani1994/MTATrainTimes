#!/usr/bin/env python3

"""
Weather API Client - Fetches current weather from NOAA/weather.gov
Uses public API without authentication
Fixed to parse OKX grid and points correctly
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
        """Initialize weather client with New York area coordinates"""
        # OKX Grid Point: 40.6625°N, 73.9978°W
        # Grid: OKX/34,33
        self.grid_url = "https://api.weather.gov/gridpoints/OKX/34,33"
        self.forecast_url = "https://api.weather.gov/gridpoints/OKX/34,33/forecast"
        self.hourly_forecast_url = "https://api.weather.gov/gridpoints/OKX/34,33/forecast/hourly"
        
    def fetch_weather(self):
        """
        Fetch current weather from NOAA API
        
        Returns:
            WeatherData object with current conditions, or None on error
        """
        try:
            weather = WeatherData()
            weather.timestamp = datetime.now()
            # Format date as "Fri, Jan 2 2026"
            weather.date_str = weather.timestamp.strftime("%a, %b %-d %Y")
            if " 0" in weather.date_str:  # Remove leading zero from day
                weather.date_str = weather.date_str.replace(" 0", " ")
            
            logger.info(f"Fetching weather from OKX gridpoints...")
            
            # Fetch gridpoint data (has current conditions)
            grid_response = requests.get(
                self.grid_url,
                timeout=10,
                headers={"User-Agent": "MTA-Display (https://github.com)"}
            )
            grid_response.raise_for_status()
            grid_data = grid_response.json()
            
            # Extract properties from gridpoint
            properties = grid_data.get("properties", {})
            
            # Temperature (already in Fahrenheit)
            temp_f = properties.get("temperature", {})
            if isinstance(temp_f, dict):
                weather.temperature = int(round(temp_f.get("value", 0)))
            else:
                weather.temperature = int(round(temp_f)) if temp_f else None
            
            # Apparent temperature / Real feel (wind chill equivalent)
            apparent_temp_f = properties.get("apparentTemperature", {})
            if isinstance(apparent_temp_f, dict):
                weather.real_feel = int(round(apparent_temp_f.get("value", 0)))
            else:
                weather.real_feel = int(round(apparent_temp_f)) if apparent_temp_f else None
            
            # If no apparent temp, use wind chill
            if not weather.real_feel:
                wind_chill_f = properties.get("windChill", {})
                if isinstance(wind_chill_f, dict):
                    weather.real_feel = int(round(wind_chill_f.get("value", 0)))
                else:
                    weather.real_feel = int(round(wind_chill_f)) if wind_chill_f else None
            
            # Weather condition from weatherSummary
            weather_summary = properties.get("weatherSummary", "Unknown")
            if weather_summary and weather_summary != "Unknown":
                weather.condition = weather_summary
            else:
                # Try shortForecast instead
                short_forecast = properties.get("shortForecast", "Unknown")
                if short_forecast and short_forecast != "Unknown":
                    weather.condition = short_forecast.split(",")[0].strip()
                else:
                    weather.condition = "Unknown"
            
            logger.info(f"Grid data - Temp: {weather.temperature}°F, RF: {weather.real_feel}°F, Condition: {weather.condition}")
            
            # Fetch forecast for high/low temps
            try:
                forecast_response = requests.get(
                    self.forecast_url,
                    timeout=10,
                    headers={"User-Agent": "MTA-Display (https://github.com)"}
                )
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()
                
                # Get today's forecast periods
                periods = forecast_data.get("properties", {}).get("periods", [])
                
                if periods:
                    # First period should be current/today
                    today_period = periods[0]
                    
                    # Get temperature from first period
                    if not weather.high_temp:
                        weather.high_temp = today_period.get("temperature")
                    
                    # Look for tonight's low
                    if len(periods) > 1:
                        tonight_period = periods[1]
                        if not weather.real_feel and tonight_period.get("isDaytime") == False:
                            # Use tonight's low as reference for real feel
                            pass
                    
                    # If we got high, try to infer low
                    if weather.high_temp and not weather.low_temp:
                        # Look through periods for different temperature (typically night)
                        for period in periods:
                            temp = period.get("temperature")
                            if temp and temp != weather.high_temp:
                                weather.low_temp = temp
                                break
                    
                    # Fallback if we only got one high temp
                    if weather.high_temp and not weather.low_temp:
                        weather.low_temp = max(weather.high_temp - 8, 32)  # Assume 8° drop, min 32°F
                
                logger.info(f"Forecast - High: {weather.high_temp}°F, Low: {weather.low_temp}°F")
                
            except Exception as e:
                logger.warning(f"Could not fetch forecast: {e}")
                # Use current temp ±5 as fallback
                if weather.temperature:
                    if not weather.high_temp:
                        weather.high_temp = weather.temperature + 2
                    if not weather.low_temp:
                        weather.low_temp = weather.temperature - 6
            
            logger.info(
                f"Weather complete - Temp: {weather.temperature}°F, "
                f"RF: {weather.real_feel}°F, Condition: {weather.condition}, "
                f"High: {weather.high_temp}°F, Low: {weather.low_temp}°F"
            )
            
            return weather
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch weather: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing weather data: {e}", exc_info=True)
            return None
    
    def get_weather_icon_code(self, condition_str):
        """
        Get weather icon code based on condition string
        
        Args:
            condition_str: Weather condition (e.g., "Sunny", "Cloudy", "Rainy")
            
        Returns:
            Icon code for rendering
        """
        if not condition_str:
            return "unknown"
            
        condition = condition_str.lower()
        
        # Check for each condition type
        if "sunny" in condition or "clear" in condition:
            return "sunny"
        elif "partly cloudy" in condition or "partly sunny" in condition:
            return "partly_cloudy"
        elif "cloudy" in condition or "overcast" in condition or "mostly cloudy" in condition:
            return "cloudy"
        elif "rain" in condition or "precipitation" in condition:
            return "rainy"
        elif "snow" in condition or "flurries" in condition or "sleet" in condition:
            return "snowy"
        elif "thunder" in condition or "storm" in condition:
            return "stormy"
        elif "fog" in condition or "mist" in condition:
            return "foggy"
        elif "wind" in condition or "breezy" in condition:
            return "windy"
        else:
            return "unknown"
