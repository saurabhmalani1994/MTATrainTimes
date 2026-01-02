#!/usr/bin/env python3

"""
Weather API Client - Fetches current weather from NOAA/weather.gov
Uses public API without authentication
Fixed to use forecast endpoints with wind chill calculation
"""

import logging
import requests
import math
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
        self.forecast_url = "https://api.weather.gov/gridpoints/OKX/34,33/forecast"
        self.hourly_forecast_url = "https://api.weather.gov/gridpoints/OKX/34,33/forecast/hourly"
        
    def calculate_wind_chill(self, temperature_f, windspeed_mph):
        """
        Calculate wind chill using National Weather Service formula
        
        Formula: 35.74 + 0.6215*T - 35.75*(V^0.16) + 0.4275*T*(V^0.16)
        where T = temperature in Fahrenheit, V = windspeed in mph
        
        Only applies when T <= 50°F and V > 3 mph
        
        Args:
            temperature_f: Temperature in Fahrenheit
            windspeed_mph: Wind speed in mph
            
        Returns:
            Wind chill temperature in Fahrenheit, or original temp if conditions don't apply
        """
        try:
            if temperature_f is None or windspeed_mph is None:
                return temperature_f
            
            # Wind chill only applies when temp <= 50°F and wind > 3 mph
            if temperature_f > 50 or windspeed_mph <= 3:
                return temperature_f
            
            T = float(temperature_f)
            V = float(windspeed_mph)
            
            # NWS Wind Chill Formula
            wind_chill = 35.74 + (0.6215 * T) - (35.75 * (V ** 0.16)) + (0.4275 * T * (V ** 0.16))
            
            return int(round(wind_chill))
        except Exception as e:
            logger.warning(f"Error calculating wind chill: {e}")
            return temperature_f
        
    def fetch_weather(self):
        """
        Fetch current weather from NOAA API
        Uses forecast endpoint for current conditions and hourly for 24-hour high/low
        
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
            
            logger.info(f"Fetching weather from OKX forecast endpoint...")
            
            # Fetch forecast data (has current conditions in first period)
            forecast_response = requests.get(
                self.forecast_url,
                timeout=10,
                headers={"User-Agent": "MTA-Display (https://github.com)"}
            )
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Get first period (current/today)
            periods = forecast_data.get("properties", {}).get("periods", [])
            
            if not periods:
                logger.error("No forecast periods found")
                return None
            
            current_period = periods[0]
            
            # Extract temperature (Fahrenheit)
            weather.temperature = current_period.get("temperature")
            if weather.temperature:
                weather.temperature = int(weather.temperature)
            
            logger.debug(f"Temperature from forecast: {weather.temperature}°F")
            
            # Extract wind speed and calculate real feel (wind chill)
            wind_speed_str = current_period.get("windSpeed", "0 mph")
            wind_speed_mph = self._extract_wind_speed(wind_speed_str)
            
            logger.debug(f"Wind speed: {wind_speed_mph} mph")
            
            # Calculate real feel using NWS wind chill formula
            weather.real_feel = self.calculate_wind_chill(weather.temperature, wind_speed_mph)
            
            logger.debug(f"Real feel (wind chill): {weather.real_feel}°F")
            
            # Extract weather condition from shortForecast
            weather.condition = current_period.get("shortForecast", "Unknown")
            
            logger.info(
                f"Forecast data - Temp: {weather.temperature}°F, "
                f"RF: {weather.real_feel}°F, Condition: {weather.condition}"
            )
            
            # Fetch hourly data for 24-hour high/low temperatures
            self._fetch_24hour_temps(weather)
            
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
    
    def _extract_wind_speed(self, wind_speed_str):
        """
        Extract numeric wind speed from string like "9 mph" or "10 to 15 mph"
        
        Args:
            wind_speed_str: Wind speed string from API
            
        Returns:
            Wind speed as float in mph, or 0 if unable to parse
        """
        try:
            if not wind_speed_str:
                return 0
            
            wind_str = str(wind_speed_str).lower().strip()
            
            # Remove "mph" and extract first number
            wind_str = wind_str.replace("mph", "").strip()
            
            # Handle "X to Y" format - use the higher value
            if "to" in wind_str:
                parts = wind_str.split("to")
                if len(parts) >= 2:
                    # Get second number (upper range)
                    wind_speed = float(parts[1].strip())
                else:
                    wind_speed = float(parts[0].strip())
            else:
                # Single number
                wind_speed = float(wind_str)
            
            return wind_speed
        except (ValueError, AttributeError, IndexError):
            logger.warning(f"Could not parse wind speed: '{wind_speed_str}'")
            return 0
    
    def _fetch_24hour_temps(self, weather):
        """
        Fetch hourly forecast and extract high/low temps for next 24 hours
        
        Args:
            weather: WeatherData object to populate with high/low temps
        """
        try:
            hourly_response = requests.get(
                self.hourly_forecast_url,
                timeout=10,
                headers={"User-Agent": "MTA-Display (https://github.com)"}
            )
            hourly_response.raise_for_status()
            hourly_data = hourly_response.json()
            
            periods = hourly_data.get("properties", {}).get("periods", [])
            
            if not periods:
                logger.warning("No hourly periods found")
                return
            
            # Get next 24 hours (24 hourly periods)
            temps_24h = []
            for i, period in enumerate(periods[:24]):  # Next 24 hours
                temp = period.get("temperature")
                if temp is not None:
                    temps_24h.append(int(temp))
            
            if temps_24h:
                weather.high_temp = max(temps_24h)
                weather.low_temp = min(temps_24h)
                logger.info(f"24-hour temps - High: {weather.high_temp}°F, Low: {weather.low_temp}°F")
            else:
                logger.warning("Could not extract temperatures from hourly forecast")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch hourly forecast: {e}")
            # Fallback: use current temp ±5
            if weather.temperature:
                weather.high_temp = weather.temperature + 5
                weather.low_temp = weather.temperature - 5
        except Exception as e:
            logger.warning(f"Error parsing hourly forecast: {e}")
            # Fallback: use current temp ±5
            if weather.temperature:
                weather.high_temp = weather.temperature + 5
                weather.low_temp = weather.temperature - 5
    
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
        elif "rain" in condition or "precipitation" in condition or "shower" in condition:
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
