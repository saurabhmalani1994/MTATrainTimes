#!/usr/bin/env python3
"""
Configuration settings for MTA Train Display
"""

import os


class Config:
    """Configuration class for MTA Train Display application"""
    
    # ============= MTA API Configuration =============
    # MTA API Key (optional for GTFS-RT, but recommended)
    # Register at: https://new.mta.info/developers
    MTA_API_KEY = os.getenv('MTA_API_KEY', '')
    
    # Feed path for N, Q, R, W lines serving Brooklyn
    FEED_PATH = 'gtfs-nqrw'
    
    # Stop ID for 25th Street station
    # For R train: '414' is the stop ID
    # Northbound: '414N', Southbound: '414S'
    STOP_ID = '414'
    
    # Route ID
    ROUTE_ID = 'R'
    
    # ============= Display Configuration =============
    # LED Matrix dimensions
    DISPLAY_WIDTH = 64
    DISPLAY_HEIGHT = 32
    
    # Frame duration (seconds to show each direction)
    FRAME_DURATION = 5
    
    # Display refresh rate (frames per second)
    DISPLAY_FPS = 30
    
    # ============= API Update Configuration =============
    # How often to fetch new train data (seconds)
    API_UPDATE_INTERVAL = 10
    
    # Request timeout (seconds)
    API_TIMEOUT = 10
    
    # ============= Logging Configuration =============
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # ============= Alternative Stations =============
    # You can modify these for different stations
    STATION_CONFIGS = {
        '25th_st_r_brooklyn': {
            'stop_id': '414',
            'route_id': 'R',
            'feed_path': 'gtfs-nqrw',
            'stop_name': '25th St (Brooklyn)',
            'description': 'R train at 25th Street, Brooklyn'
        },
        '25th_st_n_manhattan': {
            'stop_id': '101',
            'route_id': 'N',
            'feed_path': 'gtfs-nqrw',
            'stop_name': '25th St (Manhattan)',
            'description': 'N train at 25th Street, Manhattan'
        },
        'canal_st': {
            'stop_id': '301',
            'route_id': 'N',
            'feed_path': 'gtfs-nqrw',
            'stop_name': 'Canal St',
            'description': 'N train at Canal Street'
        },
    }
    
    # ============= Hardware Configuration =============
    # LED matrix library to use: 'rgbmatrix', 'rpi-rgb-led-matrix', or 'test'
    MATRIX_LIBRARY = os.getenv('MATRIX_LIBRARY', 'rgbmatrix')
    
    # GPIO slowdown factor (for RPi with rpi-rgb-led-matrix)
    # Increase if display flickers: 1, 2, 3, 4
    GPIO_SLOWDOWN = 2
    
    # For chained displays
    CHAIN_LENGTH = 1
    PARALLEL_CHAINS = 1
    
    @classmethod
    def get_station_config(cls, station_key):
        """
        Get configuration for a specific station
        
        Args:
            station_key: Key from STATION_CONFIGS
            
        Returns:
            Dict with station configuration
        """
        return cls.STATION_CONFIGS.get(station_key, cls.STATION_CONFIGS['25th_st_r_brooklyn'])
    
    @classmethod
    def set_station(cls, station_key):
        """
        Switch to a different station configuration
        
        Args:
            station_key: Key from STATION_CONFIGS
        """
        config = cls.get_station_config(station_key)
        cls.STOP_ID = config['stop_id']
        cls.ROUTE_ID = config['route_id']
        cls.FEED_PATH = config['feed_path']
