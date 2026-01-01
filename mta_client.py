#!/usr/bin/env python3
"""
MTA GTFS-RT API Client - TRIP_ID PATTERN PARSING VERSION
Fetches and parses real-time train data from MTA
Uses trip_id pattern (e.g., S71R, N93R) for accurate direction detection
"""

import logging
import requests
import time
import csv
import os
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
    
    def __init__(self, api_key=None, trips_file='trips.txt'):
        """
        Initialize MTA client
        
        Args:
            api_key: Optional MTA API key
            trips_file: Path to trips.txt GTFS file for lookups
        """
        self.api_key = api_key
        self.base_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds%2fnyct"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'x-api-key': self.api_key})
        
        # Load trips data from CSV
        self.trips_lookup = {}
        self._load_trips_data(trips_file)
    
    def _load_trips_data(self, trips_file):
        """
        Load trips.txt CSV file and create lookup dictionary
        
        Maps trip_id pattern to destination information
        
        Args:
            trips_file: Path to trips.txt file
        """
        if not os.path.exists(trips_file):
            logger.warning(f"trips.txt file not found at {trips_file}")
            return
        
        try:
            with open(trips_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trip_id = row['trip_id']
                    trip_headsign = row['trip_headsign']
                    
                    # Extract the pattern from trip_id (e.g., "082250_R..S71R" → "S71R")
                    # Format: some_prefix_ROUTE..PATTERNR
                    if '_' in trip_id and '..' in trip_id:
                        # Get the part after ".."
                        parts = trip_id.split('..')
                        if len(parts) >= 2:
                            pattern = parts[-1]  # Get the last part (e.g., "S71R")
                            
                            # Extract direction from pattern
                            # Format: [N or S][code]R
                            if len(pattern) > 0:
                                direction_char = pattern[0]  # First character
                                
                                if direction_char == 'N':
                                    direction = 'northbound'
                                elif direction_char == 'S':
                                    direction = 'southbound'
                                else:
                                    continue
                                
                                # Store mapping by the pattern (e.g., "S71R", "N93R")
                                self.trips_lookup[pattern] = {
                                    'direction': direction,
                                    'destination': trip_headsign,
                                    'trip_id': trip_id
                                }
            
            logger.debug(f"Loaded {len(self.trips_lookup)} trip patterns from {trips_file}")
            
        except Exception as e:
            logger.error(f"Error loading trips.txt: {e}", exc_info=True)
    
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
    
    def _extract_pattern_from_trip_id(self, trip_id):
        """
        Extract the direction pattern from trip_id
        
        Format: "082250_R..S71R" → "S71R"
        
        Args:
            trip_id: Full trip ID from GTFS-RT
            
        Returns:
            Pattern string (e.g., "S71R", "N93R") or None
        """
        try:
            if '..' not in trip_id:
                return None
            
            # Get the part after ".."
            parts = trip_id.split('..')
            if len(parts) >= 2:
                pattern = parts[-1]  # Last part (e.g., "S71R")
                return pattern
        except Exception as e:
            logger.debug(f"Error extracting pattern from {trip_id}: {e}")
        
        return None
    
    def parse_feed(self, feed, stop_id, route_id):
        """
        Parse GTFS-RT feed to extract train arrivals
        
        Uses trip_id pattern lookup for accurate direction mapping
        
        Args:
            feed: FeedMessage from MTA
            stop_id: Base stop ID to filter (e.g., 'R35' for 25th St)
                     The actual stop_ids in the feed will be 'R35N' and 'R35S'
            route_id: Route ID (e.g., 'R' for R train)
            
        Returns:
            Dict with 'northbound' and 'southbound' lists of Train objects
        """
        trains = {
            'northbound': [],
            'southbound': []
        }
        
        try:
            logger.debug(f"Parsing feed for stop_id base: {stop_id}, route: {route_id}")
            
            for entity in feed.entity:
                if not entity.HasField('trip_update'):
                    continue
                
                trip_update = entity.trip_update
                trip = trip_update.trip
                
                # Filter by route
                if trip.route_id != route_id:
                    continue
                
                # Extract pattern from trip_id (e.g., "S71R", "N93R")
                pattern = self._extract_pattern_from_trip_id(trip.trip_id)
                
                if not pattern:
                    logger.debug(f"Trip {trip.trip_id}: Cannot extract pattern from trip_id")
                    continue
                
                # Look up in trips.txt dictionary
                if pattern not in self.trips_lookup:
                    logger.debug(f"Trip {trip.trip_id}: Pattern {pattern} not in trips.txt")
                    continue
                
                trip_info = self.trips_lookup[pattern]
                direction = trip_info['direction']
                destination = trip_info['destination']
                
                logger.debug(f"Trip {trip.trip_id}: pattern={pattern}, "
                           f"direction={direction}, destination={destination}")
                
                # Determine which suffix to look for based on direction
                stop_suffix = 'N' if direction == 'northbound' else 'S'
                target_stop_id = f"{stop_id}{stop_suffix}"
                
                # Find stops matching our stop ID
                found = False
                for stop_time in trip_update.stop_time_update:
                    if stop_time.stop_id == target_stop_id:
                        # Found the stop we're looking for
                        arrival_time = None
                        if stop_time.HasField('arrival'):
                            arrival_time = stop_time.arrival.time
                        elif stop_time.HasField('departure'):
                            # If no arrival, use departure
                            arrival_time = stop_time.departure.time
                        
                        if arrival_time:
                            train = Train(
                                route_id=route_id,
                                destination=destination[:20],  # Limit to 20 chars
                                arrival_time=arrival_time,
                                direction=direction
                            )
                            trains[direction].append(train)
                            logger.debug(f"✓ Added {direction} train: {train}")
                            found = True
                        break
                
                if not found:
                    logger.debug(f"  Stop {target_stop_id} not found in trip stops")
            
            # Sort by arrival time and limit to next trains
            for direction in ['northbound', 'southbound']:
                trains[direction].sort(key=lambda t: t.arrival_time)
                trains[direction] = trains[direction][:5]  # Keep top 5
            
            logger.info(f"Parsed trains - Northbound: {len(trains['northbound'])}, "
                       f"Southbound: {len(trains['southbound'])}")
            
            return trains
            
        except Exception as e:
            logger.error(f"Error parsing feed: {e}", exc_info=True)
            return trains
    
    @staticmethod
    def get_display_name(route_id):
        """Get display name for route"""
        return route_id
