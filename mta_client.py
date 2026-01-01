#!/usr/bin/env python3
"""
MTA GTFS-RT API Client
Fetches and parses real-time train data from MTA
"""

import logging
import requests
import time
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
    
    # MTA Direction IDs (from GTFS)
    DIRECTION_NAMES = {
        0: 'northbound',
        1: 'southbound',
        'NORTH': 'northbound',
        'SOUTH': 'southbound',
    }
    
    # Stop IDs for 25th St station
    # Format: parent_station + direction_letter
    STOP_MAPPING = {
        'R35N': {'name': '25th Street', 'direction': 'northbound'},
        'R35S': {'name': '25th Street', 'direction': 'southbound'},
    }
    
    def __init__(self, api_key=None):
        """
        Initialize MTA client
        
        Args:
            api_key: Optional MTA API key
        """
        self.api_key = api_key
        self.base_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds%2fnyct"
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
                
                # Get direction from trip descriptor
                # GTFS-RT direction_id: 0=one direction, 1=opposite
                # For R train: 0=northbound, 1=southbound (typically)
                direction = self._get_direction_from_trip(trip)
                
                if direction not in ['northbound', 'southbound']:
                    continue
                
                # Get the destination (headsign)
                destination = self._get_destination(trip)
                
                # Determine which suffix to look for
                stop_suffix = 'N' if direction == 'northbound' else 'S'
                target_stop_id = f"{stop_id}{stop_suffix}"
                
                logger.debug(f"Trip {trip.trip_id}: route={route_id}, "
                           f"direction={direction}, destination={destination}, "
                           f"looking for stop_id={target_stop_id}")
                
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
                                destination=destination,
                                arrival_time=arrival_time,
                                direction=direction
                            )
                            trains[direction].append(train)
                            logger.debug(f"✓ Added train: {train}")
                            found = True
                        break
                
                if not found:
                    logger.debug(f"  Stop {target_stop_id} not found in trip")
            
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
    
    def _get_direction_from_trip(self, trip):
        """
        Determine direction from trip descriptor
        
        Uses direction_id from GTFS when available, falls back to headsign parsing
        
        Args:
            trip: TripDescriptor from GTFS-RT
            
        Returns:
            'northbound' or 'southbound'
        """
        # Try direction_id first (more reliable)
        if hasattr(trip, 'direction_id') and trip.direction_id is not None:
            # For most NYC routes: 0=northbound/outbound, 1=southbound/inbound
            # But this can vary by route
            if trip.direction_id == 0:
                return 'northbound'
            elif trip.direction_id == 1:
                return 'southbound'
        
        # Fallback: parse headsign for keywords
        if hasattr(trip, 'trip_headsign') and trip.trip_headsign:
            headsign = trip.trip_headsign.lower()
            if any(word in headsign for word in ['whitehall', 'downtown', 'forest', 'cortlandt']):
                return 'northbound'
            elif any(word in headsign for word in ['bay ridge', 'brooklyn', '95 st']):
                return 'southbound'
        
        # Final fallback: look at trip_id pattern
        if hasattr(trip, 'trip_id'):
            trip_id = trip.trip_id.upper()
            if trip_id.endswith('N') or 'N0' in trip_id:
                return 'northbound'
            elif trip_id.endswith('S') or 'S0' in trip_id:
                return 'southbound'
        
        logger.warning(f"Could not determine direction for trip {trip.trip_id}")
        return 'northbound'  # Default fallback
    
    def _get_destination(self, trip):
        """
        Extract destination from trip
        
        Args:
            trip: TripDescriptor from GTFS-RT
            
        Returns:
            Destination string (e.g., 'Whitehall', 'Bay Ridge')
        """
        if hasattr(trip, 'trip_headsign') and trip.trip_headsign:
            # Use the headsign, limiting to first 15 characters
            return trip.trip_headsign[:15]
        
        # Fallback
        return "Unknown"
    
    @staticmethod
    def get_display_name(route_id):
        """Get display name for route"""
        return route_id