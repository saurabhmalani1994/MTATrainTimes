#!/usr/bin/env python3
"""
LED Display Manager
Handles rendering to 32x64 RGB LED matrix
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
    
    def __init__(self):
        """Initialize display manager"""
        self.matrix = None
        self.try_init_matrix()
        
        # For testing/development without hardware
        self.test_mode = self.matrix is None
        
        if self.test_mode:
            logger.warning("Running in test mode - no LED matrix detected")
        else:
            logger.info("LED matrix initialized successfully")
    
    def try_init_matrix(self):
        """
        Try to initialize the LED matrix hardware
        
        Supports both rpi-rgb-led-matrix and rgbmatrix libraries
        """
        try:
            # Try adafruit rgbmatrix library first
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
            
            options = RGBMatrixOptions()
            options.rows = self.DISPLAY_HEIGHT
            options.cols = self.DISPLAY_WIDTH
            options.chain_length = 1
            options.parallel = 1
            options.hardware_mapping = 'adafruit-hat'
            options.gpio_slowdown = 2
            
            self.matrix = RGBMatrix(options=options)
            logger.info("Initialized with rgbmatrix library")
            return
            
        except ImportError:
            logger.debug("rgbmatrix library not available")
        except Exception as e:
            logger.debug(f"Failed to init rgbmatrix: {e}")
        
        # Fallback: other matrix initialization methods can be added here
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
                row_y = self.HEADER_HEIGHT + (idx * self.ROW_HEIGHT)
                self.draw_train_row(draw, train, row_y, idx)
            
            # Display or save
            if self.test_mode:
                self.save_test_image(img, direction)
            else:
                self.display_image(img)
            
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
    
    def draw_header(self, draw, direction):
        """
        Draw header row showing direction
        
        Args:
            draw: PIL ImageDraw object
            direction: 'northbound' or 'southbound'
        """
        try:
            # Try to load font, fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 8)
            except:
                font = ImageFont.load_default()
            
            # Format direction text
            direction_text = direction.upper()
            
            # Draw on black background
            draw.rectangle(
                [(0, 0), (self.DISPLAY_WIDTH - 1, self.HEADER_HEIGHT - 1)],
                outline=self.COLORS['dark_gray'],
                fill=self.COLORS['black']
            )
            
            # Draw text left-aligned
            draw.text(
                (2, 1),
                direction_text,
                font=font,
                fill=self.COLORS['white']
            )
            
        except Exception as e:
            logger.error(f"Error drawing header: {e}")
    
    def draw_train_row(self, draw, train, y_pos, row_idx):
        """
        Draw a single train row with three columns
        
        Layout:
        [Train # in red circle] [Destination] [Time]
        
        Args:
            draw: PIL ImageDraw object
            train: Train object
            y_pos: Y position of row
            row_idx: Row index (0 or 1)
        """
        try:
            # Try to load font
            try:
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 7)
                font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 9)
            except:
                font_small = ImageFont.load_default()
                font_bold = ImageFont.load_default()
            
            # Column 1: Train number in red circle
            self.draw_train_badge(draw, train.route_id, y_pos)
            
            # Column 2: Destination with marquee if needed
            col2_x = self.COL_WIDTHS[0]
            col2_width = self.COL_WIDTHS[1]
            self.draw_destination(draw, train.destination, col2_x, y_pos, col2_width, font_small)
            
            # Column 3: Time to arrival
            col3_x = self.COL_WIDTHS[0] + self.COL_WIDTHS[1]
            minutes = train.get_minutes_to_arrival()
            time_text = self.format_time_text(minutes)
            
            draw.text(
                (col3_x + 2, y_pos + 2),
                time_text,
                font=font_bold,
                fill=self.COLORS['cyan']
            )
            
        except Exception as e:
            logger.error(f"Error drawing train row: {e}")
    
    def draw_train_badge(self, draw, route_id, y_pos):
        """
        Draw train number in yellow text with red circle
        
        Args:
            draw: PIL ImageDraw object
            route_id: Train route ID (e.g., 'R')
            y_pos: Y position
        """
        try:
            # Load font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            # Circle parameters
            circle_x = 6
            circle_y = y_pos + 6
            circle_radius = 5
            
            # Draw red circle
            draw.ellipse(
                [(circle_x - circle_radius, circle_y - circle_radius),
                 (circle_x + circle_radius, circle_y + circle_radius)],
                outline=self.COLORS['red'],
                fill=self.COLORS['black']
            )
            
            # Draw yellow text in center
            bbox = draw.textbbox((0, 0), route_id, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw.text(
                (circle_x - text_width // 2, circle_y - text_height // 2),
                route_id,
                font=font,
                fill=self.COLORS['yellow']
            )
            
        except Exception as e:
            logger.error(f"Error drawing train badge: {e}")
    
    def draw_destination(self, draw, destination, x_pos, y_pos, max_width, font):
        """
        Draw destination text, with scrolling if needed
        
        Args:
            draw: PIL ImageDraw object
            destination: Destination string
            x_pos: X position
            y_pos: Y position
            max_width: Maximum width available
            font: Font to use
        """
        try:
            # Truncate or add marquee
            display_text = destination[:18]  # Limit to reasonable length
            
            draw.text(
                (x_pos + 2, y_pos + 2),
                display_text,
                font=font,
                fill=self.COLORS['white']
            )
            
            # TODO: Implement marquee scrolling for longer names
            
        except Exception as e:
            logger.error(f"Error drawing destination: {e}")
    
    def format_time_text(self, minutes):
        """Format arrival time for display"""
        if minutes == 0:
            return "NOW"
        elif minutes == 1:
            return "1 Min"
        else:
            return f"{minutes} Min"
    
    def display_image(self, img):
        """
        Display image on LED matrix
        
        Args:
            img: PIL Image object
        """
        try:
            if self.matrix:
                # Convert PIL image to matrix format and display
                self.matrix.SetImage(img)
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
    
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
                img = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), self.COLORS['black'])
                self.matrix.SetImage(img)
                logger.info("Display cleared")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
