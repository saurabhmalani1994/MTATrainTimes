#!/usr/bin/env python3

"""
MAIN LOOP INTEGRATION - How to use the Nyan Cat frame

This shows how to modify your main.py to cycle between:
1. Northbound trains
2. Southbound trains  
3. Nyan Cat animation

All with equal display duration.
"""

import logging
import time
from display_manager import DisplayManager

logger = logging.getLogger(__name__)

class MainDisplay:
    """Main display controller with frame rotation"""
    
    def __init__(self, frame_duration=5.0):
        """
        Initialize display controller
        
        Args:
            frame_duration: Seconds to display each frame (northbound, southbound, nyan cat)
        """
        self.display_manager = DisplayManager()
        self.frame_duration = frame_duration  # How long to show each direction
        self.last_switch = time.time()
        self.current_frame = 0  # 0=northbound, 1=southbound, 2=nyan_cat
        
    def get_trains_for_direction(self, direction):
        """
        Get trains for the given direction
        
        Args:
            direction: 'northbound' or 'southbound'
            
        Returns:
            List of Train objects, or empty list if none available
        """
        # TODO: Replace with actual MTA API calls
        # For now, return empty list instead of None
        return []
    
    def run(self):
        """
        Main display loop - cycles between northbound, southbound, and nyan cat
        """
        try:
            while True:
                current_time = time.time()
                
                # Switch frames every frame_duration seconds
                if current_time - self.last_switch >= self.frame_duration:
                    self.current_frame = (self.current_frame + 1) % 3
                    self.last_switch = current_time
                    logger.info(f"Switching to frame {self.current_frame} (0=north, 1=south, 2=nyan)")
                
                # Render current frame
                try:
                    if self.current_frame == 0:
                        # Northbound trains
                        trains = self.get_trains_for_direction('northbound')
                        if trains is None:
                            trains = []
                        self.display_manager.render_frame('northbound', trains)
                        
                    elif self.current_frame == 1:
                        # Southbound trains
                        trains = self.get_trains_for_direction('southbound')
                        if trains is None:
                            trains = []
                        self.display_manager.render_frame('southbound', trains)
                        
                    elif self.current_frame == 2:
                        # Nyan Cat animation
                        self.display_manager.render_nyan_cat_frame()
                except Exception as e:
                    logger.error(f"Error rendering frame {self.current_frame}: {e}", exc_info=True)
                
                # Frame rate control (30 FPS)
                time.sleep(0.033)
                
        except KeyboardInterrupt:
            logger.info("Display interrupted by user")
            self.display_manager.cleanup()
        except Exception as e:
            logger.error(f"Display error: {e}", exc_info=True)
            self.display_manager.cleanup()


# Alternative: If you want different durations for each frame

class MainDisplayAdvanced:
    """Advanced display controller with per-frame duration control"""
    
    def __init__(self):
        """Initialize with custom durations for each frame"""
        self.display_manager = DisplayManager()
        
        # Duration (in seconds) to show each frame
        self.frame_durations = {
            'northbound': 5.0,   # Show northbound for 5 seconds
            'southbound': 5.0,   # Show southbound for 5 seconds
            'nyan_cat': 8.0,     # Show nyan cat for 8 seconds (more fun!)
        }
        
        self.last_switch = time.time()
        self.current_frame = 0  # 0=northbound, 1=southbound, 2=nyan_cat
        self.frame_names = ['northbound', 'southbound', 'nyan_cat']
        
    def get_trains_for_direction(self, direction):
        """Get trains for the given direction"""
        # TODO: Replace with actual MTA API calls
        # Return empty list instead of None
        return []
    
    def run(self):
        """Main display loop with per-frame durations"""
        try:
            while True:
                current_time = time.time()
                current_frame_name = self.frame_names[self.current_frame]
                frame_duration = self.frame_durations[current_frame_name]
                
                # Switch frames when duration expires
                if current_time - self.last_switch >= frame_duration:
                    self.current_frame = (self.current_frame + 1) % 3
                    self.last_switch = current_time
                    logger.info(f"Switching to frame: {self.frame_names[self.current_frame]}")
                
                # Render current frame
                try:
                    if self.current_frame == 0:
                        trains = self.get_trains_for_direction('northbound')
                        if trains is None:
                            trains = []
                        self.display_manager.render_frame('northbound', trains)
                        
                    elif self.current_frame == 1:
                        trains = self.get_trains_for_direction('southbound')
                        if trains is None:
                            trains = []
                        self.display_manager.render_frame('southbound', trains)
                        
                    elif self.current_frame == 2:
                        self.display_manager.render_nyan_cat_frame()
                except Exception as e:
                    logger.error(f"Error rendering frame {self.current_frame}: {e}", exc_info=True)
                
                # Frame rate control (30 FPS)
                time.sleep(0.033)
                
        except KeyboardInterrupt:
            logger.info("Display interrupted by user")
            self.display_manager.cleanup()
        except Exception as e:
            logger.error(f"Display error: {e}", exc_info=True)
            self.display_manager.cleanup()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Option 1: Equal duration for all frames (5 seconds each)
    # display = MainDisplay(frame_duration=5.0)
    # display.run()
    
    # Option 2: Different durations for each frame
    display = MainDisplayAdvanced()
    display.run()
