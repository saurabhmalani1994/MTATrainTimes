#!/usr/bin/env python3
"""
Test script for MTA Train Display
Useful for debugging and testing without LED hardware
"""

import sys
import logging
from mta_client import MTAClient, Train
from display_manager import DisplayManager
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_connection():
    """Test MTA API connection"""
    print("\n=== Testing MTA API Connection ===")
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    
    print(f"Connecting to feed: {config.FEED_PATH}")
    feed = client.get_feed(config.FEED_PATH)
    
    if feed:
        print(f"✓ Successfully fetched feed")
        print(f"  Entities: {len(feed.entity)}")
        print(f"  Timestamp: {feed.header.timestamp}")
        return True
    else:
        print("✗ Failed to fetch feed")
        return False


def test_parse_trains():
    """Test train data parsing"""
    print("\n=== Testing Train Data Parsing ===")
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    
    feed = client.get_feed(config.FEED_PATH)
    if not feed:
        print("✗ Could not fetch feed")
        return False
    
    print(f"Parsing feed for stop: {config.STOP_ID}, route: {config.ROUTE_ID}")
    train_data = client.parse_feed(feed, config.STOP_ID, config.ROUTE_ID)
    
    print(f"\nNorthbound trains: {len(train_data['northbound'])}")
    for i, train in enumerate(train_data['northbound'][:3]):
        print(f"  {i+1}. {train.route_id} → {train.destination} ({train.get_minutes_to_arrival()} min)")
    
    print(f"\nSouthbound trains: {len(train_data['southbound'])}")
    for i, train in enumerate(train_data['southbound'][:3]):
        print(f"  {i+1}. {train.route_id} → {train.destination} ({train.get_minutes_to_arrival()} min)")
    
    return len(train_data['northbound']) > 0 or len(train_data['southbound']) > 0


def test_display_rendering():
    """Test display rendering"""
    print("\n=== Testing Display Rendering ===")
    
    # Create test trains
    import time
    now = int(time.time())
    
    test_trains = [
        Train('R', 'Whitehall', now + 300, 'northbound'),   # 5 min
        Train('R', 'Cortlandt', now + 600, 'northbound'),   # 10 min
    ]
    
    display = DisplayManager()
    print(f"Display initialized in {'test mode' if display.test_mode else 'hardware mode'}")
    
    print("Rendering test frame...")
    display.render_frame('northbound', test_trains)
    
    if display.test_mode:
        print("✓ Frame saved to /tmp/ (check for mta_display_northbound_*.png)")
    else:
        print("✓ Frame rendered to LED matrix")
    
    display.cleanup()
    return True


def test_real_time_display():
    """Run live display test"""
    print("\n=== Running Live Display Test ===")
    print("Displaying real train data for 30 seconds...")
    print("(Press Ctrl+C to stop)\n")
    
    config = Config()
    client = MTAClient(config.MTA_API_KEY)
    display = DisplayManager()
    
    try:
        for i in range(6):  # 30 seconds with 5 sec frames
            feed = client.get_feed(config.FEED_PATH)
            if not feed:
                print("✗ Failed to fetch feed")
                continue
            
            train_data = client.parse_feed(feed, config.STOP_ID, config.ROUTE_ID)
            
            # Show northbound
            direction = 'northbound'
            trains = train_data[direction][:2]
            print(f"\n[{i*5}s] Showing {direction.upper()}")
            for j, train in enumerate(trains):
                print(f"  Row {j+1}: {train.route_id} → {train.destination:15} {train.get_minutes_to_arrival():2} min")
            
            display.render_frame(direction, trains)
            
            import time
            time.sleep(2.5)
            
            # Show southbound
            direction = 'southbound'
            trains = train_data[direction][:2]
            print(f"[{i*5+2}s] Showing {direction.upper()}")
            for j, train in enumerate(trains):
                print(f"  Row {j+1}: {train.route_id} → {train.destination:15} {train.get_minutes_to_arrival():2} min")
            
            display.render_frame(direction, trains)
            
            time.sleep(2.5)
    
    except KeyboardInterrupt:
        print("\n\nTest stopped")
    finally:
        display.cleanup()
    
    return True


def main():
    """Run tests"""
    print("""
╔════════════════════════════════════════════════╗
║   MTA Train Display - Test Suite               ║
║   32x64 LED Matrix on Raspberry Pi              ║
╚════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Train Parsing", test_parse_trains),
        ("Display Rendering", test_display_rendering),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:30} {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Ask to run live test
    print("\n" + "="*50)
    response = input("Run live display test? (y/n): ").strip().lower()
    if response == 'y':
        test_real_time_display()
    
    print("\nTest suite complete!")


if __name__ == '__main__':
    main()
