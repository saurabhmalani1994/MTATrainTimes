#!/usr/bin/env python3

"""
LED Display Manager - OPENSANS TRUETYPE FONT WITH SLIDING DESTINATIONS
Handles rendering to 32x64 RGB LED matrix using SetPixel() method

FEATURES:
- OpenSans TrueType font rendering
- Sliding destination text animation with proper clipping
- Tunable font sizes via configuration
- All previous fixes maintained
- Smaller font for 'NOW' time display
"""

import logging
import time
import os
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
    HEADER_HEIGHT = 5
    ROW_HEIGHT = 12
    COL_WIDTHS = [12, 30, 22]  # Train #, Destination, Time
    DEST_MAX_WIDTH = 28  # Max pixels for destination text
    DEST_COL_X = 12  # Starting X position of destination column
    
    # Font configuration - TUNABLE SIZES
    FONT_CONFIG = {
        'header_size': 8,      # Header font size
        'badge_size': 9,       # Train badge font size
        'dest_size': 9,        # Destination font size
        'time_size': 10,        # Time font size
        'time_now_size': 7,    # Smaller size for 'NOW' text
        'weather_size': 8,    # Weather info font size
        'weather_temp_size': 9,    # Weather info font size
    }
    
    # Sliding animation configuration
    SLIDE_CONFIG = {
        'enabled': True,           # Enable sliding animation
        'speed': 2,                # Pixels per frame
        'pause_frames': 30,        # Frames to pause at edges
        'cycle_duration': 120,     # Total frames per complete cycle
    }
    
    def __init__(self):
        """Initialize display manager"""
        self.matrix = None
        self.try_init_matrix()
        
        # For testing/development without hardware
        self.test_mode = self.matrix is None
        
        # Load OpenSans TrueType fonts
        self.fonts = self._load_fonts()
        
        # Animation state for destinations
        self.slide_state = {}  # destination -> slide position
        self.frame_count = 0   # Global frame counter for animation
        
        if self.test_mode:
            logger.warning("Running in test mode - no LED matrix detected")
        else:
            logger.info("✓ LED matrix initialized successfully")
            logger.info(f"  Resolution: {self.matrix.width}x{self.matrix.height}")
    
    def _load_fonts(self):
        """Load OpenSans TrueType fonts
        
        Returns:
            Dict of font name -> ImageFont object
        """
        fonts = {}
        
        # Try to find OpenSans font file
        font_paths = [
            # "/usr/share/fonts/truetype/nunito-sans/NunitoSans-VariableFont_YTLC,opsz,wdth,wght.ttf",
            # "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
            # "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            # "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            # "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        
        # First try to find OpenSans specifically
        opensans_paths = [
            "/usr/share/fonts/truetype/opensans/OpenSans-Regular.ttf",
            "/usr/share/fonts/opentype/opensans/OpenSans-Regular.otf",
            "/usr/local/share/fonts/OpenSans-Regular.ttf",
        ]
        
        # Check for OpenSans first
        font_file = None
        for path in opensans_paths:
            if os.path.exists(path):
                font_file = path
                logger.info(f"Found OpenSans font: {path}")
                break
        
        # Fall back to other fonts if OpenSans not found
        if not font_file:
            logger.warning("OpenSans not found, trying fallback fonts...")
            for path in font_paths:
                if os.path.exists(path):
                    font_file = path
                    logger.info(f"Using fallback font: {path}")
                    break

        dejavu_fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        nunito_fontfile = "/usr/share/fonts/truetype/nunito-sans/NunitoSans-VariableFont_YTLC,opsz,wdth,wght.ttf"
        noto_fontfile = "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf"
        liberation_fontfile = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        
        # Load fonts at different sizes
        if font_file:
            try:
                fonts['header'] = ImageFont.truetype(dejavu_fontfile, self.FONT_CONFIG['header_size'])
                fonts['badge'] = ImageFont.truetype(liberation_fontfile, self.FONT_CONFIG['badge_size'])
                fonts['dest'] = ImageFont.truetype(dejavu_fontfile, self.FONT_CONFIG['dest_size'])
                fonts['time'] = ImageFont.truetype(nunito_fontfile, self.FONT_CONFIG['time_size'])
                fonts['time_now'] = ImageFont.truetype(nunito_fontfile, self.FONT_CONFIG['time_now_size'])
                fonts['weather'] = ImageFont.truetype(nunito_fontfile, self.FONT_CONFIG['weather_size'])
                fonts['weather_temp'] = ImageFont.truetype(nunito_fontfile, self.FONT_CONFIG['weather_temp_size'])
                logger.info(f"✓ Loaded TrueType fonts from {font_file}")
            except Exception as e:
                logger.warning(f"Could not load TrueType font: {e}")
                fonts = self._get_fallback_fonts()
        else:
            logger.warning("No suitable font found, using default fonts")
            fonts = self._get_fallback_fonts()
        
        return fonts
    
    def _get_fallback_fonts(self):
        """Get fallback fonts (default PIL fonts)
        
        Returns:
            Dict of font name -> ImageFont object
        """
        fonts = {}
        try:
            fonts['header'] = ImageFont.load_default(size=9)
            fonts['badge'] = ImageFont.load_default(size=7)
            fonts['dest'] = ImageFont.load_default(size=9)
            fonts['time'] = ImageFont.load_default(size=9)
            fonts['time_now'] = ImageFont.load_default(size=7)
        except:
            # Very old PIL version
            default_font = ImageFont.load_default()
            fonts['header'] = default_font
            fonts['badge'] = default_font
            fonts['dest'] = default_font
            fonts['time'] = default_font
            fonts['time_now'] = default_font
        
        logger.info("Using fallback default fonts")
        return fonts
    
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
            options.brightness = 100
            
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
            # Increment frame counter for animations
            self.frame_count += 1
            
            # Create image for rendering
            img = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), self.COLORS['black'])
            draw = ImageDraw.Draw(img)
            
            # STEP 1: Draw all sliding destination text first
            for idx, train in enumerate(trains[:2]):
                row_y = self.HEADER_HEIGHT + (idx * self.ROW_HEIGHT) + 2
                col2_x = self.COL_WIDTHS[0]
                font = self.fonts['dest']
                self.draw_destination_text_only(draw, train.destination, col2_x, row_y, font)
            
            # STEP 2: Draw black clipping rectangles to hide overflow
            for idx, train in enumerate(trains[:2]):
                row_y = self.HEADER_HEIGHT + (idx * self.ROW_HEIGHT) + 2
                col2_x = self.COL_WIDTHS[0]
                self.draw_clipping_rectangles(draw, col2_x, row_y)
            
            # STEP 3: Draw badges and time (on top of clipping rectangles)
            for idx, train in enumerate(trains[:2]):
                row_y = self.HEADER_HEIGHT + (idx * self.ROW_HEIGHT) + 2
                self.draw_train_badge(draw, train.route_id, row_y)
                
                # Draw time with conditional font size
                col3_x = self.COL_WIDTHS[0] + self.COL_WIDTHS[1]
                minutes = train.get_minutes_to_arrival()
                time_text = self.format_time_text(minutes)
                
                # Use smaller font for 'NOW', regular font for minutes
                if time_text == "NOW":
                    time_font = self.fonts['time_now']
                else:
                    time_font = self.fonts['time']
                
                bbox = draw.textbbox((0, 0), time_text, font=time_font)
                text_height = bbox[3] - bbox[1]
                time_y = row_y + (self.ROW_HEIGHT - text_height) // 2 - 1
                
                draw.text(
                    (col3_x + 1, time_y),
                    time_text,
                    font=time_font,
                    fill=self.COLORS['cyan']
                )
            
            # STEP 4: Draw header (NORTHBOUND/SOUTHBOUND) on top of everything
            self.draw_header(draw, direction)
            
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
        Using OpenSans TrueType font
        
        Args:
            draw: PIL ImageDraw object
            direction: 'northbound' or 'southbound'
        """
        try:
            font = self.fonts['header']
            
            # Full direction text
            direction_text = "NORTH BOUND" if direction == 'northbound' else "SOUTH BOUND"
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), direction_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center horizontally, position 2 pixels higher (use y=0)
            x_pos = max(0, (self.DISPLAY_WIDTH - text_width) // 2)
            y_pos = -1  # 2 pixels higher than default centered position
            
            # Draw text
            draw.text(
                (x_pos, y_pos),
                direction_text,
                font=font,
                fill=self.COLORS['white']
            )
            
        except Exception as e:
            logger.error(f"Error drawing header: {e}")
    
    def draw_destination_text_only(self, draw, destination, x_pos, y_pos, font):
        """
        Draw ONLY the destination text with sliding animation if too long
        Does not draw clipping rectangles - those are drawn separately
        
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
            
            # Calculate offset for animation
            offset = self._calculate_slide_offset(destination, max_width)
            
            # Draw text with offset (handles both short and long text)
            draw.text(
                (x_pos + 2 - offset, text_y),
                destination,
                font=font,
                fill=self.COLORS['white']
            )
            
        except Exception as e:
            logger.error(f"Error drawing destination text: {e}")
    
    def draw_clipping_rectangles(self, draw, x_pos, y_pos):
        """
        Draw black rectangles to hide text overflow on both sides
        This is drawn AFTER the text but BEFORE badges and time
        
        Args:
            draw: PIL ImageDraw object
            x_pos: X position of destination column
            y_pos: Y position of row
        """
        try:
            max_width = self.DEST_MAX_WIDTH
            
            # Left clipping rectangle - hide overflow into badge column
            draw.rectangle(
                [(0, y_pos), (x_pos + 2 - 1, y_pos + self.ROW_HEIGHT - 1)],
                fill=self.COLORS['black']
            )
            
            # Right clipping rectangle - hide overflow into time column
            draw.rectangle(
                [(x_pos + 2 + max_width, y_pos), (self.DISPLAY_WIDTH - 1, y_pos + self.ROW_HEIGHT - 1)],
                fill=self.COLORS['black']
            )
            
        except Exception as e:
            logger.error(f"Error drawing clipping rectangles: {e}")
    
    def draw_train_badge(self, draw, route_id, y_pos):
        """
        Draw train number in yellow text with red circle
        Positioned 2 pixels higher and 1 pixel to the right
        Using OpenSans TrueType font
        
        Args:
            draw: PIL ImageDraw object
            route_id: Train route ID (e.g., 'R')
            y_pos: Y position of row
        """
        try:
            font = self.fonts['badge']
            
            # Circle parameters
            circle_x = 5
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
            
            # Center in circle, with +1 pixel right and -2 pixels up
            text_x = circle_x - text_width // 2 + 0  # 1 pixel right
            text_y = circle_y - text_height // 2 - 2  # 2 pixels up
            
            # Draw text
            draw.text(
                (text_x, text_y),
                route_id,
                font=font,
                fill=self.COLORS['yellow']
            )
            
        except Exception as e:
            logger.error(f"Error drawing train badge: {e}")
    
    def draw_destination_sliding(self, draw, destination, x_pos, y_pos, font):
        """
        Draw destination text with sliding animation if too long
        Text slides back and forth to show full length
        Clipped to stay within destination column bounds
        
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
                # Text is too long - animate sliding with clipping
                offset = self._calculate_slide_offset(destination, max_width)
                
                # Draw text directly on main image with offset
                # The text will naturally be clipped at the image boundaries
                # We offset it to create the sliding effect
                draw.text(
                    (x_pos + 2 - offset, text_y),
                    destination,
                    font=font,
                    fill=self.COLORS['white']
                )
                
                # Fill in areas outside the destination column to hide overflow
                # Left side (badge column) - draw black rectangle to hide overflow
                img = draw.im
                for py in range(y_pos, y_pos + self.ROW_HEIGHT):
                    for px in range(x_pos + 2):
                        if px >= 0:
                            img.putpixel((px, py), self.COLORS['black'])
                
                # Right side (time column) - draw black rectangle to hide overflow
                for py in range(y_pos, y_pos + self.ROW_HEIGHT):
                    for px in range(x_pos + 2 + max_width, self.DISPLAY_WIDTH):
                        if px < self.DISPLAY_WIDTH:
                            img.putpixel((px, py), self.COLORS['black'])
                
        except Exception as e:
            logger.error(f"Error drawing destination: {e}")
    
    def _calculate_slide_offset(self, text, max_width):
        """
        Calculate the horizontal offset for sliding text animation
        Text slides back and forth smoothly
        
        Args:
            text: Text to slide
            max_width: Maximum width available
            
        Returns:
            Pixel offset for text position
        """
        try:
            font = self.fonts['dest']
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox(
                (0, 0), text, font=font
            )
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                return 0
            
            # Distance to slide
            slide_distance = text_width - max_width + 5  # 5px margin
            
            # Get animation state
            cycle = self.SLIDE_CONFIG['cycle_duration']
            speed = self.SLIDE_CONFIG['speed']
            pause = self.SLIDE_CONFIG['pause_frames']
            
            # Calculate position in cycle
            frame = self.frame_count % cycle
            
            # Phases:
            # 0: Pause at start
            # pause: Slide right
            # pause + slide_frames: Pause at end
            # pause + slide_frames + pause: Slide left
            # Total = cycle
            
            slide_frames = (cycle - 2 * pause) // 2
            
            if frame < pause:
                # Pause at start
                offset = 0
            elif frame < pause + slide_frames:
                # Slide right
                progress = frame - pause
                offset = int((progress / slide_frames) * slide_distance)
            elif frame < pause + slide_frames + pause:
                # Pause at end
                offset = slide_distance
            else:
                # Slide left
                progress = frame - (pause + slide_frames + pause)
                offset = int(slide_distance - (progress / slide_frames) * slide_distance)
            
            return offset
            
        except Exception as e:
            logger.error(f"Error calculating slide offset: {e}")
            return 0
    
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

    def render_weather(self, weather_data):
        """
        Render weather frame (30 x 64 pixels, top/bottom rows unused)
        Left third (21 pixels): Weather icon
        Right two-thirds (43 pixels): Information in 4 rows
        
        Row 2 (Weather Condition) has dynamic scrolling marquee effect
        All other rows and icon remain static
        
        Args:
            weather_data: WeatherData object from weather_client
        """
        try:
            # Increment frame counter for animations
            self.frame_count += 1
            
            # Create image (top row unused: y=0, bottom row unused: y=31)
            # Active area: y=1 to y=30
            img = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), self.COLORS['black'])
            draw = ImageDraw.Draw(img)
            
            # Safety check
            if weather_data is None:
                # Show "No Data" message
                font = self.fonts['dest']
                text = "Weather Unavailable"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.DISPLAY_WIDTH - text_width) // 2
                y = 15
                draw.text((x, y), text, font=font, fill=self.COLORS['cyan'])
                
                if self.test_mode:
                    self.save_test_image(img, "weather")
                else:
                    self.display_image(img)
                return
            
            # Weather icon parameters (static, will not move)
            icon_x_center = 5
            icon_y_center = 20
            
            # Get weather condition and icon type
            condition = weather_data.condition if weather_data.condition else "Unknown"
            
            # Get icon code using the improved method
            icon_code = self._get_icon_code(condition)
            
            logger.debug(f"Weather condition: '{condition}' -> icon: '{icon_code}'")
            
            # RIGHT TWO-THIRDS: Information (x=21 to x=63)
            info_x = 15
            row_height = 7
            font_small = self.fonts['weather']
            
            # ============================================================================
            # ROW 1: Date (e.g., "Fri, Jan 2 2026") - STATIC
            # ============================================================================
            y_row1 = -2
            date_str = weather_data.date_str if weather_data.date_str else datetime.now().strftime("%a, %b %-d %Y").replace(" 0", " ")
            draw.text((0, y_row1), date_str, font=font_small, fill=self.COLORS['white'])
            
            # ============================================================================
            # ROW 2: Weather condition with DYNAMIC SCROLLING MARQUEE
            # ============================================================================
            y_row2 = y_row1 + row_height
            cond_text = condition if condition else "Unknown"
            
            # Use same scrolling logic as train destination
            # Step 1: Draw scrolling text
            scroll_offset = self._calculate_scroll_offset_weather(cond_text, font_small, info_x)
            text_x = info_x - scroll_offset
            draw.text((int(text_x), y_row2), cond_text, font=font_small, fill=self.COLORS['white'])
            
            # ============================================================================
            # ROW 3: Current temp and real feel (e.g., "62°F (RF: 57°F)") - STATIC
            # ============================================================================
            font_temp = self.fonts['weather_temp']

            y_row3 = y_row2 + row_height
            if weather_data.temperature is not None:
                if weather_data.real_feel is not None:
                    temp_text = f"{weather_data.temperature}°F ({weather_data.real_feel}°F)"
                else:
                    temp_text = f"{weather_data.temperature}°F"
            else:
                temp_text = "-- °F"
            
            # Truncate if too long
            if len(temp_text) > 20:
                temp_text = f"{weather_data.temperature}°"
            
            draw.text((info_x, y_row3), temp_text, font=font_temp, fill=self.COLORS['red'])
            
            # ============================================================================
            # ROW 4: High and Low temps (e.g., "H: 68° L: 52°") - STATIC
            # ============================================================================
            y_row4 = y_row3 + row_height
            if weather_data.high_temp is not None and weather_data.low_temp is not None:
                hi_lo_text = f"H:{weather_data.high_temp}° L:{weather_data.low_temp}°"
            else:
                hi_lo_text = "No forecast"
            
            draw.text((info_x, y_row4), hi_lo_text, font=font_temp, fill=self.COLORS['yellow'])
            
            # ============================================================================
            # DRAW BLACK BOX to mask scrolling text over icon area
            # ============================================================================
            # Black box covers left third where text scrolls
            black_box_x1 = 0
            black_box_y1 = y_row2 + 2
            black_box_x2 = info_x - 1  # Stop just before right-aligned info area
            black_box_y2 = y_row2 + 10
            draw.rectangle(
                [black_box_x1, black_box_y1, black_box_x2, black_box_y2],
                fill=self.COLORS['black']
            )
            
            # ============================================================================
            # DRAW WEATHER ICON LAST (on top of black box) - COMPLETELY STATIC
            # ============================================================================
            self._draw_weather_icon(draw, icon_code, icon_x_center, icon_y_center)
            
            # Display or save
            if self.test_mode:
                self.save_test_image(img, "weather")
            else:
                self.display_image(img)
                
        except Exception as e:
            logger.error(f"Error rendering weather: {e}", exc_info=True)

    def _calculate_scroll_offset_weather(self, text, font, start_x):
        """
        Calculate dynamic scroll offset for weather condition text
        Uses same logic as train destination scrolling
        
        Smooth per-frame updates with pauses at start/end positions
        
        Args:
            text: Text to scroll
            font: Font object for text measurement
            start_x: Starting X position (right side, x=22)
            
        Returns:
            Scroll offset in pixels (negative = scroll left)
        """
        try:
            # Calculate text width using same pattern as train destination scrolling
            # Create a dummy image and draw to measure text
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox(
                (0, 0), text, font=font
            )
            text_width = bbox[2] - bbox[0]
            
            # Available width from start_x to right edge of screen
            available_width = self.DISPLAY_WIDTH - start_x
            
            # If text fits in available space, no scrolling needed
            if text_width <= available_width - 2:
                return 0
            
            # Text is too long - calculate scroll animation
            # Same logic as destination scrolling for smooth continuous motion
            
            slide_distance = text_width - available_width + 4  # +4 for padding
            pause_frames = 30  # Frames to pause at each position (at 30 FPS = 1 second)
            slide_frames = 60  # Frames to slide across the full distance
            cycle = (pause_frames + slide_frames) * 2  # Full animation cycle
            
            # Get current frame in the animation cycle
            frame = self.frame_count % cycle
            
            if frame < pause_frames:
                # Pause at start position (text fully visible)
                return 0
                
            elif frame < pause_frames + slide_frames:
                # Scroll right to left (text exits left)
                progress = frame - pause_frames
                offset = int((progress / slide_frames) * slide_distance)
                return offset
                
            elif frame < (pause_frames * 2) + slide_frames:
                # Pause at end position (text fully hidden)
                return int(slide_distance)
                
            else:
                # Scroll back left to right (return to start)
                progress = frame - ((pause_frames * 2) + slide_frames)
                offset = int(slide_distance) - int((progress / slide_frames) * slide_distance)
                return offset
                
        except Exception as e:
            logger.warning(f"Error calculating scroll offset: {e}")
            return 0
     
    def _draw_weather_icon(self, draw, icon_code, center_x, center_y):
        """
        Draw pixel-art weather icon
        
        Args:
            draw: PIL ImageDraw object
            icon_code: Weather type code (sunny, cloudy, rainy, etc.)
            center_x: X coordinate of icon center
            center_y: Y coordinate of icon center
        """
        try:
            if icon_code == "sunny":
                # Draw sun: circle with rays
                draw.ellipse([center_x-3, center_y-3, center_x+3, center_y+3], fill=self.COLORS['yellow'])
                # Rays
                draw.line([center_x-5, center_y, center_x-4, center_y], fill=self.COLORS['yellow'], width=1)
                draw.line([center_x+4, center_y, center_x+5, center_y], fill=self.COLORS['yellow'], width=1)
                draw.line([center_x, center_y-5, center_x, center_y-4], fill=self.COLORS['yellow'], width=1)
                draw.line([center_x, center_y+4, center_x, center_y+5], fill=self.COLORS['yellow'], width=1)
                
            elif icon_code == "cloudy":
                # Draw cloud
                draw.ellipse([center_x-5, center_y-2, center_x-1, center_y+2], fill=self.COLORS['gray'])
                draw.ellipse([center_x-2, center_y-3, center_x+3, center_y+1], fill=self.COLORS['gray'])
                draw.ellipse([center_x+1, center_y-2, center_x+6, center_y+2], fill=self.COLORS['gray'])
                
            elif icon_code == "partly_cloudy":
                # Sun partially behind cloud
                draw.ellipse([center_x-2, center_y-2, center_x+1, center_y+1], fill=self.COLORS['yellow'])
                draw.ellipse([center_x, center_y-1, center_x+5, center_y+2], fill=self.COLORS['gray'])
                
            elif icon_code == "rainy":
                # Cloud with rain drops
                draw.ellipse([center_x-4, center_y-3, center_x+2, center_y], fill=self.COLORS['gray'])
                # Rain drops
                draw.line([center_x-4, center_y+1, center_x-3, center_y+3], fill=self.COLORS['cyan'], width=1)
                draw.line([center_x-1, center_y+1, center_x, center_y+3], fill=self.COLORS['cyan'], width=1)
                draw.line([center_x+2, center_y+1, center_x+3, center_y+3], fill=self.COLORS['cyan'], width=1)
                
            elif icon_code == "snowy":
                # Cloud with snowflakes
                draw.ellipse([center_x-4, center_y-3, center_x+2, center_y], fill=self.COLORS['white'])
                # Snowflakes (asterisk shapes)
                draw.line([center_x-3, center_y+1, center_x-2, center_y+3], fill=self.COLORS['cyan'], width=1)
                draw.line([center_x, center_y+1, center_x+1, center_y+3], fill=self.COLORS['cyan'], width=1)
                draw.line([center_x+3, center_y+1, center_x+4, center_y+3], fill=self.COLORS['cyan'], width=1)
                
            elif icon_code == "stormy":
                # Dark cloud with lightning
                draw.ellipse([center_x-4, center_y-3, center_x+2, center_y], fill=self.COLORS['gray'])
                # Lightning bolt (zigzag)
                draw.line([center_x+1, center_y+1, center_x+2, center_y+2], fill=self.COLORS['yellow'], width=1)
                draw.line([center_x+2, center_y+2, center_x+1, center_y+3], fill=self.COLORS['yellow'], width=1)
                draw.line([center_x+1, center_y+3, center_x+2, center_y+4], fill=self.COLORS['yellow'], width=1)
                
            elif icon_code == "foggy":
                # Horizontal lines (fog)
                for offset in [-3, 0, 3]:
                    draw.line([center_x-4, center_y+offset, center_x+4, center_y+offset], 
                            fill=self.COLORS['gray'], width=1)
                
            elif icon_code == "windy":
                # Curved lines (wind)
                draw.arc([center_x-3, center_y-2, center_x+3, center_y+2], 0, 180, fill=self.COLORS['cyan'], width=1)
                draw.arc([center_x-4, center_y-4, center_x+2, center_y], 0, 180, fill=self.COLORS['cyan'], width=1)
                
            else:  # unknown
                # Question mark or generic icon
                draw.ellipse([center_x-3, center_y-3, center_x+3, center_y+3], fill=self.COLORS['gray'])
                draw.text((center_x-2, center_y-3), "?", font=self.fonts['badge'], fill=self.COLORS['white'])
                
        except Exception as e:
            logger.error(f"Error drawing weather icon: {e}")


    def _get_icon_code(self, condition_str):
        """
        Get weather icon code based on condition string from NOAA shortForecast
        
        Args:
            condition_str: Weather condition string (e.g., from NOAA API)
            
        Returns:
            Icon code (sunny, cloudy, rainy, snowy, stormy, foggy, windy, partly_cloudy, unknown)
        """
        if not condition_str:
            return "unknown"
        
        condition = condition_str.lower().strip()
        
        logger.debug(f"Parsing weather condition: '{condition}'")
        
        # Check for each condition type (order matters - most specific first)
        
        # Thunderstorm/Storm - highest priority
        if "thunder" in condition or "storm" in condition or "tornado" in condition or "lightning" in condition:
            return "stormy"
        
        # Snow/Sleet/Winter
        if "snow" in condition or "sleet" in condition or "blizzard" in condition or "flurries" in condition:
            return "snowy"
        
        # Rain/Precipitation
        if "rain" in condition or "shower" in condition or "drizzle" in condition or "precipitation" in condition or "wet" in condition:
            return "rainy"
        
        # Partly Cloudy/Partly Sunny (must come before "sunny" and "cloudy")
        if "partly cloudy" in condition or "partly sunny" in condition or "mostly sunny" in condition:
            return "partly_cloudy"
        
        # Sunny/Clear
        if "sunny" in condition or "clear" in condition or "fair" in condition:
            return "sunny"
        
        # Cloudy/Overcast
        if "cloudy" in condition or "overcast" in condition or "mostly cloudy" in condition:
            return "cloudy"
        
        # Fog/Mist/Haze
        if "fog" in condition or "mist" in condition or "haze" in condition:
            return "foggy"
        
        # Wind/Breezy
        if "wind" in condition or "breezy" in condition or "gust" in condition:
            return "windy"
        
        # Default
        logger.warning(f"Unknown weather condition: '{condition}' - using default icon")
        return "unknown"