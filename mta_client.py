#!/usr/bin/env python3
"""
MTA GTFS-RT API Client
Fetches and parses real-time train data from MTA
"""

import logging
import requests
from datetime import datetime
from google.transit import gtfs_realtime_pb2

logger = logging.getLogger(__name__)


class Train:
    """Represents a train with arrival information"""
    
    def __init__(self, route_id, destination, arrival_time, direction):
        self.route_id = route_id
        self.destination = destination
        self.arrival_time = arrival_time  # Unix timestamp
        self.direction = direction
    
    def get_minutes_to_arrival(self):
        """Get minutes until train arrival"""
        import time
        current_time = time.time()
        seconds_to_arrival = self.arrival_time - current_time
        minutes = max(0, int(seconds_to_arrival / 60))
        return minutes
    
    def __repr__(self):
        return f"Train(route={self.route_id}, dest={self.destination}, arrives_in={self.get_minutes_to_arrival()}m)"


class MTAClient:
    """Client for MTA GTFS-RT API"""
    
    # Stop IDs for 25th St station
    STOP_MAPPING = {
        'R14_N': {  # 25th St - Northbound (Manhattan)
            'name': '25th Street',
            'direction': 'northbound'
        },
        'R14_S': {  # 25th St - Southbound (Brooklyn)
            'name': '25th Street',
            'direction': 'southbound'
        }
    }
    
    # Known R train destinations
    DESTINATION_MAPPING = {
        '2': 'Whitehall',
        '3': 'Whitehall',
        '4': 'Cortlandt',
        '5': 'Cortlandt',
        '6': 'Canal',
        '7': 'Canal',
        '8': 'Prince',
        '9': 'Prince',
        '10': 'Union Sq',
        '11': 'Union Sq',
        '12': 'Herald Sq',
        '13': 'Herald Sq',
        '14': '14th St',
        '15': '14th St',
        '16': 'Union Sq',
        '17': '28th St',
        '18': '28th St',
        '19': '34th St',
        '20': 'Herald Sq',
        '21': 'Herald Sq',
        '22': '42nd St',
        '23': '42nd St',
        '24': '49th St',
        '25': '49th St',
        '26': '59th St',
        '27': '59th St',
        '28': '42nd St',
        '29': '57th St',
        '30': 'Lexington',
        '31': 'Jamaica',
        '32': 'Jamaica',
        '33': 'Jamaica',
        '34': 'Jamaica',
        '35': 'Far Rock',
        '36': 'Astoria',
        '37': 'Astoria',
        '38': 'Forest H',
        '39': 'Forest H',
        '40': 'Bay Ridge',
        '41': 'Bay Ridge',
    }
    
    def __init__(self, api_key=None):
        """
        Initialize MTA client
        
        Args:
            api_key: Optional MTA API key (not required for GTFS-RT)
        """
        self.api_key = api_key
        self.base_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds%2Fnyct"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'x-api-key': self.api_key})
    
    def get_feed(self, feed_path):
        """
        Fetch GTFS-RT feed from MTA
        
        Args:
            feed_path: Feed path (e.g., 'gtfs-nqrw' for NQRW lines)
            
        Returns:
            Parsed FeedMessage or None on error
        """
        try:
            url = f"{self.base_url}/{feed_path}"
            logger.debug(f"Fetching from {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            logger.debug(f"Successfully fetched feed with {len(feed.entity)} entities")
            return feed
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching feed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing feed: {e}")
            return None
    
    def parse_feed(self, feed, stop_id, route_id):
        """
        Parse GTFS-RT feed to extract train arrivals
        
        Args:
            feed: FeedMessage from MTA
            stop_id: Stop ID to filter (e.g., 'R14')
            route_id: Route ID (e.g., 'R' for R train)
            
        Returns:
            Dict with 'northbound' and 'southbound' lists of Train objects
        """
        trains = {
            'northbound': [],
            'southbound': []
        }
        
        try:
            for entity in feed.entity:
                if not entity.HasField('trip_update'):
                    continue
                
                trip_update = entity.trip_update
                trip = trip_update.trip
                
                # Filter by route
                if trip.route_id != route_id:
                    continue
                
                # Extract destination and direction from trip descriptor
                destination = self._get_destination(trip)
                direction = self._get_direction(trip)
                
                # Find stops matching our stop ID
                for stop_time in trip_update.stop_time_update:
                    if stop_id in stop_time.stop_id:
                        # Verify direction matches
                        if self._matches_stop_direction(stop_time.stop_id, direction):
                            arrival_time = stop_time.arrival.time if stop_time.HasField('arrival') else None
                            
                            if arrival_time:
                                train = Train(
                                    route_id=route_id,
                                    destination=destination,
                                    arrival_time=arrival_time,
                                    direction=direction
                                )
                                trains[direction].append(train)
                                logger.debug(f"Added train: {train}")
                            break
            
            # Sort by arrival time and limit to next trains
            for direction in ['northbound', 'southbound']:
                trains[direction].sort(key=lambda t: t.arrival_time)
                trains[direction] = trains[direction][:5]  # Keep top 5
            
            return trains
            
        except Exception as e:
            logger.error(f"Error parsing feed: {e}")
            return trains
    
    def _get_destination(self, trip):
        """
        Extract destination from trip
        
        For GTFS-RT, we infer from stop sequence
        """
        # Try to use destination display
        if hasattr(trip, 'trip_headsign') and trip.trip_headsign:
            return trip.trip_headsign[:12]  # Limit to 12 chars
        
        # Fallback: Try to map from trip ID
        return "Unknown"
    
    def _get_direction(self, trip):
        """
        Determine direction from trip descriptor
        
        R train: Odd stop sequences = Northbound, Even = Southbound
        or based on trip ID pattern
        """
        trip_id = trip.trip_id
        
        # For R train at 25th St (stop 414):
        # Northbound trains go to Whitehall/Cortlandt (odd sequences)
        # Southbound trains go to Bay Ridge (even sequences)
        
        if 'N' in trip_id or trip_id.endswith('N'):
            return 'northbound'
        elif 'S' in trip_id or trip_id.endswith('S'):
            return 'southbound'
        
        # Default heuristic: check first character of trip_id
        # This is hackish but GTFS-RT doesn't explicitly provide direction
        return 'northbound'
    
    def _matches_stop_direction(self, stop_id, direction):
        """
        Check if stop ID matches expected direction
        """
        if direction == 'northbound':
            return 'N' in stop_id or stop_id.endswith('N')
        else:
            return 'S' in stop_id or stop_id.endswith('S')
    
    @staticmethod
    def get_display_name(route_id):
        """Get display name for route"""
        return route_id
