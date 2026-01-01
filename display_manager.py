#!/usr/bin/env python3
"""
LED Display Manager - CRISP SINGLE-LAYER TEXT WITH TUNABLE SIZES
Handles rendering to 32x64 RGB LED matrix using SetPixel() method
FEATURES:
- Single-layer crisp text (using load_default() font)
- Tunable font sizes via configuration
- All previous fixes maintained
"""

import logging
import time
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class DisplayManager:
    """Manages rendering to LED matrix display"""
    
    # Display dimensions
    DISPLAY_WIDTH = 64
    DISPLAY_HEIGHT = 32
    
    # Color definitions (RGB tuples)
    COLORS = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'yellow': (255, 255, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'gray': (128, 128, 128),
        'dark_gray': (64, 64, 64),
    }
    
    # Layout dimensions
    HEADER_HEIGHT = 8
    ROW_HEIGHT = 12
    COL_WIDTHS = [12, 32, 20]  # Train #, Destination, Time
    DEST_MAX_WIDTH = 30  # Max pixels for destination text
    
    # Font configuration - TUNABLE
    # Using load_default() which is single-layer crisp
    # These values control spacing/layout, not font size
    FONT_CONFIG = {
        'header_spacing': 2,      # Pixels between letters in header
        'badge_spacing': 1,       # Pixels between letters in badge
        'dest_spacing': 2,        # Pixels between letters in destination
        'time_spacing': 2,        # Pixels between letters in time
    }
    
    def __init__(self):
        """Initialize display manager"""
        self.matrix = None
        self.try_init_matrix()
        
        # For testing/development without hardware
        self.test_mode = self.matrix is None
        
        # Cache default font
        try:
            self.font = ImageFont.load_default(size=7)
        except:
            self.font = ImageFont.load_default()
        
        if self.test_mode:
            logger.warning("Running in test mode - no LED matrix detected")
        else:
            logger.info("✓ LED matrix initialized successfully")
            logger.info(f"  Resolution: {self.matrix.width}x{self.matrix.height}")
    
    def try_init_matrix(self):
        """
        Try to initialize the LED matrix hardware
        Uses same API as basic_test.py which is proven to work
        """
        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
            
            logger.debug("rgbmatrix library found, initializing...")
            
            # Create options (same as basic_test.py)
            options = RGBMatrixOptions()
            options.rows = self.DISPLAY_HEIGHT
            options.cols = self.DISPLAY_WIDTH
            options.chain_length = 1
            options.parallel = 1
            options.hardware_mapping = "regular"
            options.gpio_slowdown = 2
            options.brightness = 80
            
            # Create matrix
            self.matrix = RGBMatrix(options=options)
            logger.info("✓ LED matrix initialized with correct API")
            
        except ImportError as e:
            logger.debug(f"rgbmatrix library not available: {e}")
            self.matrix = None
            
        except Exception as e:
            logger.error(f"Failed to initialize LED matrix: {e}")
            logger.debug(f"Full error: {e}", exc_info=True)
            self.matrix = None
    
    def render_frame(self, direction, trains):
        """
        Render a complete frame to the LED matrix
        
        Args:
            direction: 'northbound' or 'southbound'
            trains: List of Train objects (up to 2)
        """
        try:
            # Create image for rendering
            img = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), self.COLORS['black'])
            draw = ImageDraw.Draw(img)
            
            # Draw header
            self.draw_header(draw, direction)
            
            # Draw train rows
            for idx, train in enumerate(trains[:2]):
                row_y = self.HEADER_HEIGHT + (idx * self.ROW_HEIGHT) + 1
                self.draw_train_row(draw, train, row_y, idx)
            
            # Display or save
            if self.test_mode:
                self.save_test_image(img, direction)
            else:
                self.display_image(img)
                
        except Exception as e:
            logger.error(f"Error rendering frame: {e}", exc_info=True)
    
    def draw_header(self, draw, direction):
        """
        Draw header row showing full NORTHBOUND/SOUTHBOUND text
        Positioned 2 pixels higher than before
        Using CRISP single-layer load_default() font
        
        Args:
            draw: PIL ImageDraw object
            direction: 'northbound' or 'southbound'
        """
        try:
            # Use crisp single-layer font (load_default)
            font = self.font
            
            # Full direction text
            direction_text = "NORTHBOUND" if direction == 'northbound' else "SOUTHBOUND"
            
            # Draw border rectangle
            draw.rectangle(
                [(0, 0), (self.DISPLAY_WIDTH - 1, self.HEADER_HEIGHT - 1)],
                outline=self.COLORS['dark_gray'],
                fill=self.COLORS['black']
            )
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), direction_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center horizontally, position 2 pixels higher (use y=0)
            x_pos = max(0, (self.DISPLAY_WIDTH - text_width) // 2)
            y_pos = 0  # 2 pixels higher than default centered position
            
            # Draw text - single-layer crisp rendering
            draw.text(
                (x_pos, y_pos),
                direction_text,
                font=font,
                fill=self.COLORS['white']
            )
            
        except Exception as e:
            logger.error(f"Error drawing header: {e}")
    
    def draw_train_row(self, draw, train, y_pos, row_idx):
        """
        Draw a single train row with three columns
        
        Layout: [Train # in red circle] [Destination] [Time]
        Using CRISP single-layer load_default() font
        
        Args:
            draw: PIL ImageDraw object
            train: Train object
            y_pos: Y position of row
            row_idx: Row index (0 or 1)
        """
        try:
            # Use crisp single-layer font
            font = ImageFont.load_default(size=9)
            
            # Column 1: Train number in red circle
            self.draw_train_badge(draw, train.route_id, y_pos)
            
            # Column 2: Destination
            col2_x = self.COL_WIDTHS[0]
            self.draw_destination(draw, train.destination, col2_x, y_pos, font)
            
            # Column 3: Time to arrival
            col3_x = self.COL_WIDTHS[0] + self.COL_WIDTHS[1]
            minutes = train.get_minutes_to_arrival()
            time_text = self.format_time_text(minutes)
            
            # Get bounding box for proper alignment
            bbox = draw.textbbox((0, 0), time_text, font=font)
            text_height = bbox[3] - bbox[1]
            
            # Vertically center time in row
            time_y = y_pos + (self.ROW_HEIGHT - text_height) // 2
            
            draw.text(
                (col3_x + 2, time_y),
                time_text,
                font=font,
                fill=self.COLORS['cyan']
            )
            
        except Exception as e:
            logger.error(f"Error drawing train row: {e}")
    
    def draw_train_badge(self, draw, route_id, y_pos):
        """
        Draw train number in yellow text with red circle
        Positioned 2 pixels higher and 1 pixel to the right
        Using CRISP single-layer load_default() font
        
        Args:
            draw: PIL ImageDraw object
            route_id: Train route ID (e.g., 'R')
            y_pos: Y position of row
        """
        try:
            # Use crisp single-layer font
            font = self.font
            
            # Circle parameters
            circle_x = 5
            # 2 pixels higher: subtract 2 from center calculation
            circle_y = y_pos + self.ROW_HEIGHT // 2 - 0
            circle_radius = 5
            
            # Draw red circle outline only
            draw.ellipse(
                [(circle_x - circle_radius, circle_y - circle_radius),
                 (circle_x + circle_radius, circle_y + circle_radius)],
                outline=self.COLORS['red'],
                fill=self.COLORS['black']
            )
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), route_id, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center in circle, with +1 pixel right and -2 pixels up (already applied to circle_y)
            text_x = circle_x - text_width // 2 + 0  # 1 pixel right
            text_y = circle_y - text_height // 2 - 2  # 2 pixels up
            
            # Draw text - single-layer crisp rendering
            draw.text(
                (text_x, text_y),
                route_id,
                font=font,
                fill=self.COLORS['yellow']
            )
            
        except Exception as e:
            logger.error(f"Error drawing train badge: {e}")
    
    def draw_destination(self, draw, destination, x_pos, y_pos, font):
        """
        Draw destination text with truncation if too long
        Using CRISP single-layer load_default() font
        
        Args:
            draw: PIL ImageDraw object
            destination: Destination string
            x_pos: X position of column
            y_pos: Y position
            font: Font to use
        """
        try:
            # Get text dimensions
            bbox = draw.textbbox((0, 0), destination, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Max width for destination column
            max_width = self.DEST_MAX_WIDTH
            
            # Vertically center text in row
            text_y = y_pos + (self.ROW_HEIGHT - text_height) // 2
            
            # If text fits, just draw it
            if text_width <= max_width:
                draw.text(
                    (x_pos + 2, text_y),
                    destination,
                    font=font,
                    fill=self.COLORS['white']
                )
            else:
                # Text is too long - truncate
                truncated = destination
                while len(truncated) > 0:
                    bbox = draw.textbbox((0, 0), truncated + ".", font=font)
                    if bbox[2] - bbox[0] <= max_width - 2:
                        break
                    truncated = truncated[:-1]
                
                if not truncated:
                    truncated = destination[0] if destination else "?"
                
                draw.text(
                    (x_pos + 2, text_y),
                    truncated + ".",
                    font=font,
                    fill=self.COLORS['white']
                )
            
        except Exception as e:
            logger.error(f"Error drawing destination: {e}")
    
    def format_time_text(self, minutes):
        """Format arrival time for display"""
        if minutes == 0:
            return "NOW"
        elif minutes == 1:
            return "1m"
        else:
            return f"{minutes}m"
    
    def display_image(self, pil_image):
        """
        Display PIL Image on LED matrix using SetPixel() API
        
        Args:
            pil_image: PIL Image object (RGB mode, 64x32)
        """
        try:
            if not self.matrix:
                logger.error("Matrix not initialized")
                return
            
            # Ensure image is in RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Get image data
            pixels = pil_image.load()
            
            # Set each pixel on the matrix using SetPixel()
            for x in range(self.DISPLAY_WIDTH):
                for y in range(self.DISPLAY_HEIGHT):
                    r, g, b = pixels[x, y]
                    self.matrix.SetPixel(x, y, r, g, b)
            
            logger.debug("Frame displayed on matrix using SetPixel()")
            
        except AttributeError as e:
            logger.error(f"Matrix method error: {e}")
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}", exc_info=True)
    
    def save_test_image(self, img, direction):
        """
        Save image to file for testing (in test mode)
        
        Args:
            img: PIL Image object
            direction: Direction name for filename
        """
        try:
            filename = f"/tmp/mta_display_{direction}_{int(time.time())}.png"
            img.save(filename)
            logger.debug(f"Saved test image: {filename}")
            
        except Exception as e:
            logger.debug(f"Could not save test image: {e}")
    
    def cleanup(self):
        """Clean up display resources"""
        try:
            if self.matrix:
                # Clear display
                self.matrix.Clear()
                logger.info("Display cleared on shutdown")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
