#!/usr/bin/env python3
"""
MTA Train Display for 32x64 LED Matrix
Main application entry point
Displays real-time train arrivals for multiple routes at a station
"""

import time
import logging
from threading import Thread

from config import Config
from mta_client import MTAClient
from display_manager import DisplayManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MTATrainDisplay:
    """Main application controller for MTA train display"""
    
    def __init__(self):
        """Initialize the display application"""
        self.config = Config
        self.mta_client = MTAClient(self.config.MTA_API_KEY)
        self.display_manager = DisplayManager()
        
        self.running = False
        self.current_frame = "northbound"  # Start with northbound
        self.train_data = {"northbound": [], "southbound": []}
        self.last_update = 0
        
        logger.info("MTATrainDisplay initialized")
        logger.info(f"  Stop: {self.config.STOP_NAME}")
        logger.info(f"  Routes: {self.config.ROUTE_IDS}")
        logger.info(f"  Display: {self.config.DISPLAY_WIDTH}x{self.config.DISPLAY_HEIGHT}")
    
    def fetch_train_data(self):
        """Fetch train data from MTA API
        
        Supports multiple route IDs - will fetch trains for all configured routes
        """
        try:
            feed = self.mta_client.get_feed(self.config.FEED_PATH)
            if feed is None:
                logger.warning("Failed to fetch feed data")
                return
            
            # Parse feed with support for multiple routes
            # Pass ROUTE_IDS (can be list like ["R", "N", "D"] or None for all)
            self.train_data = self.mta_client.parse_feed(
                feed, 
                self.config.STOP_ID,
                route_ids=self.config.ROUTE_IDS
            )
            self.last_update = time.time()
            
            logger.info(
                f"Updated train data - "
                f"Northbound: {len(self.train_data['northbound'])} trains, "
                f"Southbound: {len(self.train_data['southbound'])} trains"
            )
            
        except Exception as e:
            logger.error(f"Error fetching train data: {e}")
    
    def update_loop(self):
        """Background thread to update train data periodically"""
        while self.running:
            try:
                self.fetch_train_data()
                time.sleep(self.config.API_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def display_loop(self):
        """Main display loop - alternates between northbound and southbound"""
        frame_duration = self.config.FRAME_DURATION
        last_frame_switch = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Switch frames every frame_duration seconds
                if current_time - last_frame_switch > frame_duration:
                    self.current_frame = (
                        "southbound" 
                        if self.current_frame == "northbound" 
                        else "northbound"
                    )
                    last_frame_switch = current_time
                
                # Get the trains for current frame
                direction = self.current_frame
                trains = self.train_data[direction][:2]  # Get first 2 trains
                
                # Render the frame
                self.display_manager.render_frame(direction, trains)
                
                time.sleep(1 / self.config.DISPLAY_FPS)
                
            except Exception as e:
                logger.error(f"Error in display loop: {e}")
                time.sleep(0.1)
    
    def run(self):
        """Start the application"""
        logger.info("Starting MTA Train Display application")
        self.running = True
        
        try:
            # Start update thread (fetches new data every API_UPDATE_INTERVAL seconds)
            update_thread = Thread(target=self.update_loop, daemon=True)
            update_thread.start()
            
            # Initial fetch
            self.fetch_train_data()
            
            # Run display loop (main thread)
            self.display_loop()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        logger.info("Shutting down...")
        self.running = False
        self.display_manager.cleanup()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    app = MTATrainDisplay()
    app.run()
