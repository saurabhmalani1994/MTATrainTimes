#!/usr/bin/env python3
"""
MTA GTFS-RT API Client
Fetches and parses real-time train data from MTA
Uses static trips.txt for destination and direction mapping
"""

import logging
import requests
import time
import csv
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
        current_time = time.time()
        seconds_to_arrival = self.arrival_time - current_time
        minutes = max(0, int(seconds_to_arrival / 60))
        return minutes
    
    def __repr__(self):
        return f"Train(route={self.route_id}, dest={self.destination}, arrives_in={self.get_minutes_to_arrival()}m)"


class MTAClient:
    """Client for MTA GTFS-RT API"""
    
    def __init__(self, api_key=None, trips_file="trips.txt"):
        """Initialize MTA client
        
        Args:
            api_key: Optional MTA API key
            trips_file: Path to trips.txt GTFS static file
        """
        self.api_key = api_key
        self.base_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds%2fnyct"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})
        
        # Load trips.txt for destination and direction mapping
        self.trips_map = {}
        self.load_trips_file(trips_file)
    
    def load_trips_file(self, trips_file):
        """Load trips.txt to map trip_id -> (destination, direction)
        
        Args:
            trips_file: Path to trips.txt GTFS file
        """
        try:
            with open(trips_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trip_id = row.get('trip_id')
                    route_id = row.get('route_id')
                    trip_headsign = row.get('trip_headsign', 'Unknown')
                    direction_id = row.get('direction_id', '0')
                    
                    if trip_id:
                        # Determine direction from direction_id
                        direction = "northbound" if direction_id == '0' else "southbound"
                        
                        # Store mapping
                        self.trips_map[trip_id] = {
                            'destination': trip_headsign,
                            'direction': direction,
                            'route_id': route_id
                        }
            
            logger.info(f"✓ Loaded {len(self.trips_map)} trips from {trips_file}")
            
        except FileNotFoundError:
            logger.error(f"trips.txt not found at {trips_file}")
        except Exception as e:
            logger.error(f"Error loading trips.txt: {e}", exc_info=True)
    
    def get_feed(self, feed_path):
        """Fetch GTFS-RT feed from MTA
        
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
    
    def parse_feed(self, feed, stop_id, route_ids=None):
        """Parse GTFS-RT feed to extract train arrivals
        
        Uses trips.txt static file for destination and direction info
        
        Args:
            feed: FeedMessage from MTA
            stop_id: Base stop ID to filter (e.g., 'R35' for 25th St)
            route_ids: List of route IDs to include, or None for all routes
                      
        Returns:
            Dict with 'northbound' and 'southbound' lists of Train objects
        """
        trains = {"northbound": [], "southbound": []}
        
        try:
            logger.debug(f"Parsing feed for stop_id={stop_id}, route_ids={route_ids}")
            
            for entity in feed.entity:
                if not entity.HasField("trip_update"):
                    continue
                
                trip_update = entity.trip_update
                trip = trip_update.trip
                trip_id = trip.trip_id
                route_id = trip.route_id
                
                # MULTIPLE ROUTES SUPPORT
                if route_ids is not None:
                    if route_id not in route_ids:
                        continue
                
                # Get destination and direction from trips.txt
                if trip_id not in self.trips_map:
                    logger.debug(f"Trip {trip_id}: Not found in trips.txt, skipping")
                    continue
                
                trip_info = self.trips_map[trip_id]
                destination = trip_info['destination']
                direction = trip_info['direction']
                
                logger.debug(f"Trip {trip_id}: route={route_id}, direction={direction}, destination='{destination}'")
                
                # Determine which suffix to look for based on direction
                stop_suffix = "N" if direction == "northbound" else "S"
                target_stop_id = f"{stop_id}{stop_suffix}"
                
                logger.debug(f"  Looking for stop {target_stop_id}")
                
                # Find this stop in the trip's stops
                found = False
                for stop_time in trip_update.stop_time_update:
                    if stop_time.stop_id == target_stop_id:
                        # Found the stop we're looking for
                        arrival_time = None
                        if stop_time.HasField("arrival"):
                            arrival_time = stop_time.arrival.time
                        elif stop_time.HasField("departure"):
                            arrival_time = stop_time.departure.time
                        
                        if arrival_time:
                            train = Train(
                                route_id=route_id,
                                destination=destination,
                                arrival_time=arrival_time,
                                direction=direction
                            )
                            trains[direction].append(train)
                            logger.debug(f"  ✓ Added {direction} train: {route_id} to {destination}")
                        
                        found = True
                        break
                
                if not found:
                    logger.debug(f"  Stop {target_stop_id} not found in this trip")
            
            # Sort by arrival time and limit to top 5
            for direction in ["northbound", "southbound"]:
                trains[direction].sort(key=lambda t: t.arrival_time)
                trains[direction] = trains[direction][:5]
            
            logger.info(f"Parsed trains - Northbound: {len(trains['northbound'])}, Southbound: {len(trains['southbound'])}")
            
            if len(trains['northbound']) == 0 and len(trains['southbound']) == 0:
                logger.warning("No trains found! Check stop_id and route_ids settings.")
            
            return trains
            
        except Exception as e:
            logger.error(f"Error parsing feed: {e}", exc_info=True)
            return trains
    
    @staticmethod
    def get_display_name(route_id):
        """Get display name for route"""
        return route_id
