#!/usr/bin/env python3
"""
Debug script to find actual stop IDs in your GTFS data
"""

import csv
from collections import defaultdict

# Check if we have stop_times.txt
print("Searching for stop_times.txt...")

try:
    # Read trips.txt to see what trips we have
    print("\n=== CHECKING trips.txt ===")
    route_counts = defaultdict(int)
    sample_trips = defaultdict(list)
    
    with open('trips.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            route_id = row.get('route_id')
            trip_id = row.get('trip_id')
            route_counts[route_id] += 1
            if len(sample_trips[route_id]) < 2:
                sample_trips[route_id].append((trip_id, row.get('trip_headsign')))
    
    print(f"\nRoute counts in trips.txt:")
    for route in sorted(route_counts.keys()):
        print(f"  Route {route}: {route_counts[route]} trips")
        for trip_id, headsign in sample_trips[route]:
            print(f"    - {trip_id}")
            print(f"      Destination: {headsign}")
    
    # Try to read stop_times.txt
    print("\n=== CHECKING stop_times.txt ===")
    
    try:
        stops_at_r35 = defaultdict(set)
        
        with open('stop_times.txt', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stop_id = row.get('stop_id')
                trip_id = row.get('trip_id')
                
                # Look for any stop containing "35" or "R"
                if '35' in stop_id or 'R35' in stop_id or stop_id.startswith('R'):
                    stops_at_r35[stop_id].add(trip_id)
        
        if stops_at_r35:
            print(f"\nStops containing '35' or starting with 'R':")
            for stop_id in sorted(stops_at_r35.keys()):
                print(f"  {stop_id}: {len(stops_at_r35[stop_id])} trips")
        else:
            print("\nNo stops found with '35' or 'R'")
        
        # Get all unique stops
        print("\n=== ALL UNIQUE STOPS ===")
        all_stops = set()
        with open('stop_times.txt', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_stops.add(row.get('stop_id'))
        
        print(f"\nTotal unique stops: {len(all_stops)}")
        
        # Show first 20 stops
        print("\nFirst 20 stops:")
        for stop in sorted(list(all_stops))[:20]:
            print(f"  {stop}")
            
    except FileNotFoundError:
        print("\nERROR: stop_times.txt not found!")
        print("The stop_times.txt file is needed to map trip_id -> stop_id")
        print("\nWithout stop_times.txt, we cannot determine which stops each trip serves.")
        print("You need to:")
        print("  1. Download full MTA GTFS data (includes stop_times.txt)")
        print("  2. Place it in the same directory as main.py")
        
except FileNotFoundError:
    print("ERROR: trips.txt not found!")
