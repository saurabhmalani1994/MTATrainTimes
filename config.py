#!/usr/bin/env python3
"""
Configuration settings for MTA Train Display
"""
import os


class Config:
    """Configuration class for MTA Train Display application"""

    # MTA API Configuration
    MTA_API_KEY = os.getenv("MTA_API_KEY", "your_mta_api_key_here")
    """Register at https://new.mta.info/developers"""
    
    # Feed path for N, Q, R, W, B, D lines serving Brooklyn
    FEED_PATH = "gtfs-nqrw"
    """Feed path - adjust based on which lines you want to track"""
    
    # Stop configuration - supports multiple routes
    STOP_ID = "R35"
    """Base stop ID (e.g., R35 for 25th Street)
    Actual stops will be R35N (northbound) and R35S (southbound)
    """
    
    # MULTIPLE ROUTES SUPPORT
    # Set which routes to display at this stop
    ROUTE_IDS = []
    """
    List of route IDs to display. Can be:
    - ["R"] - Only R train
    - ["R", "N"] - R and N trains
    - ["R", "N", "D"] - R, N, and D trains
    - None - Show ALL trains at this stop
    """
    
    STOP_NAME = "25th St Brooklyn"
    """Display name for the stop"""
    
    # LED Matrix Configuration
    DISPLAY_WIDTH = 64
    DISPLAY_HEIGHT = 32
    """LED Matrix dimensions"""
    
    # Display Settings
    FRAME_DURATION = 5
    """Frame duration (seconds) to show each direction"""
    
    DISPLAY_FPS = 30
    """Display refresh rate (frames per second)"""
    
    # API Settings
    API_UPDATE_INTERVAL = 10
    """How often to fetch new train data (seconds)"""
    
    API_TIMEOUT = 10
    """Request timeout (seconds)"""
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    """Logging level - DEBUG, INFO, WARNING, ERROR"""
    
    # Advanced Configuration
    STATION_CONFIGS = {
        "25th-str-brooklyn": {
            "stop_id": "R35",
            "route_ids": ["R", "N", "D"],  # Show R, N, D trains
            "feed_path": "gtfs-nqrw",
            "stop_name": "25th St Brooklyn",
            "description": "R, N, D trains at 25th Street, Brooklyn",
        },
        "jay-st-brooklyn": {
            "stop_id": "R36",
            "route_ids": ["R", "N", "D"],  # Show R, N, D trains
            "feed_path": "gtfs-nqrw",
            "stop_name": "Jay St Brooklyn",
            "description": "R, N, D trains at Jay Street, Brooklyn",
        },
        "times-square": {
            "stop_id": "S642",
            "route_ids": ["N", "Q", "R", "W"],  # Times Square serves these
            "feed_path": "gtfs-nqrw",
            "stop_name": "Times Sq 42 St",
            "description": "N, Q, R, W trains at Times Square",
        },
    }
    """You can modify these for different stations"""
    
    # Matrix Library
    MATRIX_LIBRARY = os.getenv("MATRIX_LIBRARY", "rgbmatrix")
    """LED matrix library to use: rgbmatrix, rpi-rgb-led-matrix, or test"""
    
    GPIO_SLOWDOWN = 2
    """Increase if display flickers: 1, 2, 3, 4"""
    
    CHAIN_LENGTH = 1
    PARALLEL_CHAINS = 1
    """For chained displays"""
    
    @classmethod
    def get_station_config(cls, station_key):
        """Get configuration for a specific station
        
        Args:
            station_key: Key from STATION_CONFIGS
            
        Returns:
            Dict with station configuration
        """
        return cls.STATION_CONFIGS.get(
            station_key, 
            cls.STATION_CONFIGS["25th-str-brooklyn"]
        )
    
    @classmethod
    def set_station(cls, station_key):
        """Switch to a different station configuration
        
        Args:
            station_key: Key from STATION_CONFIGS
        """
        config = cls.get_station_config(station_key)
        cls.STOP_ID = config["stop_id"]
        cls.ROUTE_IDS = config["route_ids"]
        cls.FEED_PATH = config["feed_path"]
        cls.STOP_NAME = config["stop_name"]
