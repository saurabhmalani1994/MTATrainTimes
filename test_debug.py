#!/usr/bin/env python3
"""
Diagnostic test script for MTA API debugging
Helps identify why trains aren't being found
"""

import logging
from mta_client import MTAClient
from config import Config

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_raw_feed():
    """Examine raw feed entities"""
    print("\n" + "="*80)
    print("STEP 1: Examining Raw Feed Data")
    print("="*80)
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    
    feed = client.get_feed(config.FEED_PATH)
    if not feed:
        print("✗ Failed to fetch feed")
        return False
    
    print(f"✓ Got feed with {len(feed.entity)} entities")
    print(f"  Feed timestamp: {feed.header.timestamp}")
    
    # Count trip updates by route
    route_counts = {}
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            route_id = entity.trip_update.trip.route_id
            if route_id not in route_counts:
                route_counts[route_id] = 0
            route_counts[route_id] += 1
    
    print(f"\nTrips by route:")
    for route_id, count in sorted(route_counts.items()):
        print(f"  {route_id:5} : {count:3} trips")
    
    # Now look at R train specifically
    print(f"\n" + "="*80)
    print(f"STEP 2: Examining R Train Trips")
    print("="*80)
    
    r_trains = []
    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue
        trip = entity.trip_update.trip
        if trip.route_id == config.ROUTE_ID:
            r_trains.append(entity.trip_update)
    
    print(f"Found {len(r_trains)} R train trips")
    
    if len(r_trains) == 0:
        print("✗ No R train trips found in feed!")
        return False
    
    # Show first 5 R train trips in detail
    for i, trip_update in enumerate(r_trains[:5]):
        trip = trip_update.trip
        print(f"\n  Trip {i+1}:")
        print(f"    trip_id: {trip.trip_id}")
        print(f"    route_id: {trip.route_id}")
        if hasattr(trip, 'direction_id') and trip.direction_id is not None:
            print(f"    direction_id: {trip.direction_id}")
        if hasattr(trip, 'trip_headsign') and trip.trip_headsign:
            print(f"    trip_headsign: {trip.trip_headsign}")
        
        # Show stops in this trip
        print(f"    stops:")
        for stop_time in trip_update.stop_time_update[:5]:
            stop_id = stop_time.stop_id
            arrival = "?" if not stop_time.HasField('arrival') else stop_time.arrival.time
            print(f"      {stop_id:10} arrival={arrival}")
    
    return True


def test_stop_filtering():
    """Test if we're finding the right stops"""
    print("\n" + "="*80)
    print("STEP 3: Testing Stop Filtering")
    print("="*80)
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    
    feed = client.get_feed(config.FEED_PATH)
    if not feed:
        print("✗ Failed to fetch feed")
        return False
    
    # Collect all unique stop_ids for R train
    stop_ids = set()
    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue
        trip = entity.trip_update.trip
        if trip.route_id != config.ROUTE_ID:
            continue
        
        for stop_time in entity.trip_update.stop_time_update:
            stop_ids.add(stop_time.stop_id)
    
    print(f"Found {len(stop_ids)} unique stop IDs for R train:")
    
    # Look for stops containing 'R35' (25th St station ID)
    matching_stops = [s for s in stop_ids if 'R35' in s]
    other_stops = [s for s in stop_ids if 'R35' not in s]
    
    print(f"\n  Stops with 'R35' (25th St):")
    if matching_stops:
        for stop_id in sorted(matching_stops):
            print(f"    ✓ {stop_id}")
    else:
        print(f"    ✗ NONE FOUND!")
    
    print(f"\n  Sample of other stops:")
    for stop_id in sorted(other_stops)[:10]:
        print(f"    {stop_id}")
    
    if not matching_stops:
        print("\n⚠ WARNING: 25th St stop not found in feed!")
        print("   Possible causes:")
        print("   1. Stop ID 'R35' may be incorrect")
        print("   2. The R train may not serve 25th St (unlikely)")
        print("   3. There may be no service on this date/time")
        return False
    
    return True


def test_parsing():
    """Test the actual parsing logic"""
    print("\n" + "="*80)
    print("STEP 4: Testing Parsing Logic")
    print("="*80)
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    
    feed = client.get_feed(config.FEED_PATH)
    if not feed:
        print("✗ Failed to fetch feed")
        return False
    
    trains = client.parse_feed(feed, config.STOP_ID, config.ROUTE_ID)
    
    print(f"Northbound trains: {len(trains['northbound'])}")
    for i, train in enumerate(trains['northbound'][:3]):
        print(f"  {i+1}. {train.route_id} → {train.destination:15} {train.get_minutes_to_arrival()} min")
    
    print(f"\nSouthbound trains: {len(trains['southbound'])}")
    for i, train in enumerate(trains['southbound'][:3]):
        print(f"  {i+1}. {train.route_id} → {train.destination:15} {train.get_minutes_to_arrival()} min")
    
    if len(trains['northbound']) == 0 and len(trains['southbound']) == 0:
        print("\n✗ No trains found!")
        return False
    
    print("\n✓ Parsing successful!")
    return True


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║            MTA API Diagnostic Tool                                         ║
║            Debugging: "0 trains" problem                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run tests in sequence
    test1 = test_raw_feed()
    test2 = test_stop_filtering() if test1 else False
    test3 = test_parsing() if test2 else False
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if test3:
        print("✓ All tests passed!")
        print("\nYour setup should work. If main.py still shows 0 trains:")
        print("  1. Make sure config.py has correct STOP_ID and ROUTE_ID")
        print("  2. Check that your station actually serves the R line")
        print("  3. Verify there is service at the current time")
    else:
        print("✗ Issues found:")
        if not test1:
            print("  - Cannot connect to MTA API")
            print("  - Check your internet connection")
            print("  - Verify the MTA API is available")
        elif not test2:
            print("  - 25th St stop not found in R train data")
            print("  - Check if STOP_ID 'R35' is correct for 25th St")
            print("  - Verify R line actually stops at 25th St")
        elif not test3:
            print("  - Parsing logic is failing")
            print("  - Check stop_id format (should be like 'R35N', 'R35S')")
            print("  - Review the logs above for details")


if __name__ == '__main__':
    main()
