#!/usr/bin/env python3
"""
Southbound Train Debugging Script
Diagnoses why southbound trains aren't being detected
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


def diagnose_southbound():
    """Diagnose the southbound detection issue"""
    print("\n" + "="*80)
    print("SOUTHBOUND TRAIN DEBUGGING")
    print("="*80)
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    
    feed = client.get_feed(config.FEED_PATH)
    if not feed:
        print("✗ Failed to fetch feed")
        return
    
    print(f"\n✓ Fetched feed with {len(feed.entity)} entities")
    print(f"  Stop ID: {config.STOP_ID}")
    print(f"  Route ID: {config.ROUTE_ID}")
    
    # Find all R train trips and analyze direction
    print("\n" + "="*80)
    print("ANALYZING R TRAIN TRIPS & DIRECTIONS")
    print("="*80)
    
    direction_analysis = {
        'northbound': {'direction_id_0': 0, 'direction_id_1': 0, 'headsign_based': 0, 'unknown': 0},
        'southbound': {'direction_id_0': 0, 'direction_id_1': 0, 'headsign_based': 0, 'unknown': 0}
    }
    
    r_train_samples = []
    
    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue
        
        trip = entity.trip_update.trip
        if trip.route_id != config.ROUTE_ID:
            continue
        
        # Analyze how direction is determined
        trip_headsign = trip.trip_headsign if hasattr(trip, 'trip_headsign') else "N/A"
        direction_id = trip.direction_id if hasattr(trip, 'direction_id') else None
        
        # Manually classify
        detected_direction = None
        detection_method = None
        
        if direction_id is not None:
            if direction_id == 0:
                detected_direction = 'northbound'
                detection_method = f'direction_id={direction_id}'
            elif direction_id == 1:
                detected_direction = 'southbound'
                detection_method = f'direction_id={direction_id}'
        
        if detected_direction is None and trip_headsign:
            headsign_lower = trip_headsign.lower()
            if any(word in headsign_lower for word in ['whitehall', 'downtown', 'forest', 'cortlandt']):
                detected_direction = 'northbound'
                detection_method = f'headsign: {trip_headsign[:20]}'
            elif any(word in headsign_lower for word in ['bay ridge', 'brooklyn', '95 st']):
                detected_direction = 'southbound'
                detection_method = f'headsign: {trip_headsign[:20]}'
        
        if detected_direction is None:
            detected_direction = 'unknown'
            detection_method = 'unknown'
        
        if detected_direction in direction_analysis:
            if detection_method.startswith('direction_id=0'):
                direction_analysis[detected_direction]['direction_id_0'] += 1
            elif detection_method.startswith('direction_id=1'):
                direction_analysis[detected_direction]['direction_id_1'] += 1
            elif detection_method.startswith('headsign'):
                direction_analysis[detected_direction]['headsign_based'] += 1
            else:
                direction_analysis[detected_direction]['unknown'] += 1
        
        # Store sample trips for detailed analysis
        if len(r_train_samples) < 10:
            r_train_samples.append({
                'trip_id': trip.trip_id,
                'direction_id': direction_id,
                'headsign': trip_headsign,
                'detected_direction': detected_direction,
                'detection_method': detection_method
            })
    
    # Print analysis
    print("\nDirection Detection Analysis:")
    print("\nNORTHBOUND trips detected by:")
    for method, count in direction_analysis['northbound'].items():
        if count > 0:
            print(f"  {method:20}: {count} trips")
    
    print("\nSOUTHBOUND trips detected by:")
    for method, count in direction_analysis['southbound'].items():
        if count > 0:
            print(f"  {method:20}: {count} trips")
    
    # Show sample trips in detail
    print("\n" + "="*80)
    print("SAMPLE TRIPS (First 10)")
    print("="*80)
    
    for i, sample in enumerate(r_train_samples):
        print(f"\nTrip {i+1}:")
        print(f"  trip_id:           {sample['trip_id']}")
        print(f"  direction_id:      {sample['direction_id']}")
        print(f"  headsign:          {sample['headsign']}")
        print(f"  detected as:       {sample['detected_direction']}")
        print(f"  detection method:  {sample['detection_method']}")
    
    # Now check which trips actually have stop R35S and R35N
    print("\n" + "="*80)
    print(f"CHECKING FOR STOPS R35N AND R35S IN FEED")
    print("="*80)
    
    r35n_trips = []
    r35s_trips = []
    
    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue
        
        trip = entity.trip_update.trip
        if trip.route_id != config.ROUTE_ID:
            continue
        
        for stop_time in entity.trip_update.stop_time_update:
            if stop_time.stop_id == 'R35N':
                r35n_trips.append({
                    'trip_id': trip.trip_id,
                    'headsign': trip.trip_headsign if hasattr(trip, 'trip_headsign') else 'N/A',
                    'direction_id': trip.direction_id if hasattr(trip, 'direction_id') else None
                })
                break
            elif stop_time.stop_id == 'R35S':
                r35s_trips.append({
                    'trip_id': trip.trip_id,
                    'headsign': trip.trip_headsign if hasattr(trip, 'trip_headsign') else 'N/A',
                    'direction_id': trip.direction_id if hasattr(trip, 'direction_id') else None
                })
                break
    
    print(f"\nTrips with stop R35N: {len(r35n_trips)}")
    if r35n_trips:
        for trip in r35n_trips[:3]:
            print(f"  {trip['trip_id']:30} | headsign={trip['headsign'][:25]:25} | dir_id={trip['direction_id']}")
    
    print(f"\nTrips with stop R35S: {len(r35s_trips)}")
    if r35s_trips:
        for trip in r35s_trips[:3]:
            print(f"  {trip['trip_id']:30} | headsign={trip['headsign'][:25]:25} | dir_id={trip['direction_id']}")
    
    # The key insight
    print("\n" + "="*80)
    print("KEY FINDING")
    print("="*80)
    
    if r35s_trips and r35n_trips:
        # Check what direction_id values they have
        r35n_dir_ids = set(t['direction_id'] for t in r35n_trips)
        r35s_dir_ids = set(t['direction_id'] for t in r35s_trips)
        
        print(f"\nR35N stops have direction_id values: {r35n_dir_ids}")
        print(f"R35S stops have direction_id values: {r35s_dir_ids}")
        
        if r35n_dir_ids and r35s_dir_ids:
            if 0 in r35n_dir_ids and 0 in r35s_dir_ids:
                print("\n⚠️  PROBLEM FOUND!")
                print("    Both R35N and R35S have direction_id=0")
                print("    This means direction_id doesn't properly distinguish them")
                print("    SOLUTION: Use headsign parsing instead")
            elif 1 in r35n_dir_ids and 1 in r35s_dir_ids:
                print("\n⚠️  PROBLEM FOUND!")
                print("    Both R35N and R35S have direction_id=1")
                print("    This means direction_id doesn't properly distinguish them")
                print("    SOLUTION: Use headsign parsing instead")
            elif (0 in r35n_dir_ids and 1 in r35s_dir_ids) or (1 in r35n_dir_ids and 0 in r35s_dir_ids):
                print("\n✓ Direction ID properly distinguishes north/south")
                print("  But check if mapping is correct (may be reversed)")


if __name__ == '__main__':
    diagnose_southbound()
