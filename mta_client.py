#!/usr/bin/env python3
"""
MTA GTFS-RT API Client
Fetches and parses real-time train data from MTA
Uses route + direction mapping to provide destinations
"""

import logging
import requests
import time
from collections import defaultdict
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
    
    # Destination mapping by route and direction
    # Based on typical NYC MTA route patterns
    DESTINATIONS = {
        'R': {
            'northbound': 'Whitehall Terminal',
            'southbound': 'Bay Ridge-95 St'
        },
        'N': {
            'northbound': 'Astoria-Ditmars Blvd',
            'southbound': 'Coney Island-Stillwell'
        },
        'Q': {
            'northbound': 'Astoria-Ditmars Blvd',
            'southbound': 'Coney Island-Stillwell'
        },
        'W': {
            'northbound': 'Astoria-Ditmars Blvd',
            'southbound': 'Whitehall Terminal'
        },
        'D': {
            'northbound': 'Norwood-205 St',
            'southbound': 'Coney Island-Stillwell'
        },
        'B': {
            'northbound': 'Bedford Park Blvd',
            'southbound': 'Coney Island-Stillwell'
        },
        'M': {
            'northbound': 'Forest Hills-71 Ave',
            'southbound': 'Jamaica Center'
        },
        'F': {
            'northbound': 'Jamaica-Van Wyck',
            'southbound': 'Coney Island-Stillwell'
        },
        '1': {
            'northbound': 'Van Cortlandt Park-242 St',
            'southbound': 'South Ferry'
        },
        '2': {
            'northbound': 'Wakefield-241 St',
            'southbound': 'Flatbush Ave-Brooklyn College'
        },
        '3': {
            'northbound': 'Harlem-148 St',
            'southbound': 'New Lots Ave'
        },
        '4': {
            'northbound': 'Woodlawn',
            'southbound': 'New Lots Ave'
        },
        '5': {
            'northbound': 'Eastchester-Dyre Ave',
            'southbound': 'Flatbush Ave-Brooklyn College'
        },
        'A': {
            'northbound': 'Inwood-207 St',
            'southbound': 'Far Rockaway-Mott Ave'
        },
        'C': {
            'northbound': 'West 168 St',
            'southbound': 'Euclid Ave'
        },
        'E': {
            'northbound': 'Jamaica Center',
            'southbound': 'World Trade Center'
        },
        'G': {
            'northbound': 'Court Square',
            'southbound': 'Coney Island-Stillwell'
        },
        'J': {
            'northbound': 'Jamaica Center',
            'southbound': 'Broad St'
        },
        'Z': {
            'northbound': 'Jamaica Center',
            'southbound': 'Broad St'
        },
        'L': {
            'northbound': '8 Ave',
            'southbound': 'Canarsie-Rockaway'
        },
    }
    
    def __init__(self, api_key=None):
        """Initialize MTA client
        
        Args:
            api_key: Optional MTA API key
        """
        self.api_key = api_key
        self.base_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds%2fnyct"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})
    
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
        
        Uses route + direction mapping for destinations
        
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
            
            # First pass: collect candidate stops
            all_stops = defaultdict(int)
            for entity in feed.entity:
                if not entity.HasField("trip_update"):
                    continue
                
                for stop_time in entity.trip_update.stop_time_update:
                    stop = stop_time.stop_id
                    if stop_id.upper() in stop.upper() or stop.startswith(stop_id):
                        all_stops[stop] += 1
            
            if all_stops:
                logger.debug(f"Found {len(all_stops)} candidate stops matching '{stop_id}':")
                for stop in sorted(all_stops.keys()):
                    logger.debug(f"  {stop}: {all_stops[stop]} trips")
            
            # Second pass: extract trains
            processed = 0
            matched = 0
            
            for entity in feed.entity:
                if not entity.HasField("trip_update"):
                    continue
                
                trip_update = entity.trip_update
                trip = trip_update.trip
                route_id = trip.route_id
                
                processed += 1
                
                # MULTIPLE ROUTES SUPPORT
                if route_ids is not None:
                    if route_id not in route_ids:
                        continue
                
                # Check each stop in the trip
                for stop_time in trip_update.stop_time_update:
                    stop_id_check = stop_time.stop_id
                    
                    # Check if this stop matches our target
                    matches = False
                    
                    if stop_id.upper() in stop_id_check.upper():
                        matches = True
                    elif stop_id_check.startswith(stop_id):
                        matches = True
                    elif stop_id in stop_id_check:
                        matches = True
                    
                    if matches:
                        # Determine direction from stop_id suffix
                        stop_upper = stop_id_check.upper()
                        direction = None
                        
                        if stop_upper.endswith('N') or stop_upper.endswith('1'):
                            direction = "northbound"
                        elif stop_upper.endswith('S') or stop_upper.endswith('2'):
                            direction = "southbound"
                        elif stop_upper.endswith('0') or stop_upper.endswith('3'):
                            # Use direction_id as fallback
                            direction_id = trip.direction_id if hasattr(trip, 'direction_id') else 0
                            direction = "northbound" if direction_id == 0 else "southbound"
                        
                        # Get destination from mapping (or Unknown as fallback)
                        destination = "Unknown"
                        if route_id in self.DESTINATIONS:
                            destination = self.DESTINATIONS[route_id].get(direction, "Unknown")
                        
                        # Get arrival time
                        arrival_time = None
                        if stop_time.HasField("arrival"):
                            arrival_time = stop_time.arrival.time
                        elif stop_time.HasField("departure"):
                            arrival_time = stop_time.departure.time
                        
                        if arrival_time and direction:
                            train = Train(
                                route_id=route_id,
                                destination=destination,
                                arrival_time=arrival_time,
                                direction=direction
                            )
                            trains[direction].append(train)
                            matched += 1
                            logger.debug(f"✓ Added {direction} train: {route_id} to '{destination}' (stop: {stop_id_check})")
                        
                        break  # Found this trip's stop, move to next trip
            
            logger.info(f"Processed {processed} trips, matched {matched} to stop '{stop_id}'")
            
            # Sort by arrival time and limit to top 5
            for direction in ["northbound", "southbound"]:
                trains[direction].sort(key=lambda t: t.arrival_time)
                trains[direction] = trains[direction][:5]
            
            logger.info(f"Parsed trains - Northbound: {len(trains['northbound'])}, Southbound: {len(trains['southbound'])}")
            
            if len(trains['northbound']) == 0 and len(trains['southbound']) == 0:
                logger.warning("⚠ No trains found!")
                logger.warning(f"  Stop ID: '{stop_id}'")
                logger.warning(f"  Routes: {route_ids}")
                logger.warning(f"  Processed {processed} total trips")
            
            return trains
            
        except Exception as e:
            logger.error(f"Error parsing feed: {e}", exc_info=True)
            return trains
    
    @staticmethod
    def get_display_name(route_id):
        """Get display name for route"""
        return route_id
