
# Create a visual reference showing the display layout

layout_reference = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    MTA TRAIN DISPLAY - LAYOUT REFERENCE                   ║
║                         32x64 LED Matrix Visual                           ║
╚════════════════════════════════════════════════════════════════════════════╝

PHYSICAL DIMENSIONS:
  • 64 pixels wide × 32 pixels high
  • Recommended mounting: Above doorway or in corner
  • Display area: ~12" × 6" depending on LED pixel size

═══════════════════════════════════════════════════════════════════════════════

DISPLAY LAYOUT (Text Representation):

┌────────────────────────────────────────────────────────────┐
│ NORTHBOUND                                                 │  ← Row 0-7 (Header)
├────────────────────────────────────────────────────────────┤
│ [R]  Whitehall            5 Min                            │  ← Row 8-19 (Train 1)
├────────────────────────────────────────────────────────────┤
│ [R]  Cortlandt            11 Min                           │  ← Row 20-31 (Train 2)
└────────────────────────────────────────────────────────────┘

Actual pixel representation (simplified):

  0         10         20         30         40         50        64
  |         |          |          |          |          |         |
0 ├─────────────────────────────────────────────────────────────────┤
  │ NORTHBOUND [Header text]                                        │
8 ├──────┬──────────────────────┬────────────────────────────────────┤
  │  [R] │ Whitehall           │ 5 Min                             │
  │ (red)│ (white text)        │ (cyan text)                       │
20├──────┼──────────────────────┼────────────────────────────────────┤
  │  [R] │ Cortlandt           │ 11 Min                            │
  │ (red)│ (white text)        │ (cyan text)                       │
32└──────┴──────────────────────┴────────────────────────────────────┘
  Col 0  Col 12                 Col 44

═══════════════════════════════════════════════════════════════════════════════

COLOR SCHEME:

  Train Number Badge:
    ┌─────────────────┐
    │  [R]            │
    │  Yellow text    │  ← Text color: YELLOW (255, 255, 0)
    │  Red circle     │  ← Background: RED (255, 0, 0)
    │  Black fill     │  ← Fill: BLACK
    └─────────────────┘

  Destination Text:
    WHITE (255, 255, 255)

  Arrival Time:
    CYAN (0, 255, 255)

  Entire Background:
    BLACK (0, 0, 0)

  Direction Header:
    WHITE text on BLACK background

═══════════════════════════════════════════════════════════════════════════════

ALTERNATING FRAMES (5 seconds each):

  TIME 0-5 SEC:
  ┌──────────────────────────────────────────────────────────┐
  │ NORTHBOUND                                               │
  │ [R]  Whitehall            5 Min                          │
  │ [R]  Herald Sq            10 Min                         │
  └──────────────────────────────────────────────────────────┘

  TIME 5-10 SEC:
  ┌──────────────────────────────────────────────────────────┐
  │ SOUTHBOUND                                               │
  │ [R]  Bay Ridge            3 Min                          │
  │ [R]  Borough Hall         9 Min                          │
  └──────────────────────────────────────────────────────────┘

  TIME 10-15 SEC:
  (Back to NORTHBOUND)
  ┌──────────────────────────────────────────────────────────┐
  │ NORTHBOUND                                               │
  │ [R]  Whitehall            8 Min (updated)               │
  │ [R]  Herald Sq            13 Min (updated)              │
  └──────────────────────────────────────────────────────────┘

  (Pattern repeats every 10 seconds with fresh data)

═══════════════════════════════════════════════════════════════════════════════

LAYOUT DIMENSIONS:

  Layout Variable              Value (pixels)    Purpose
  ──────────────────────────────────────────────────────────
  HEADER_HEIGHT                8                 Direction header area
  ROW_HEIGHT                   12                Height of each train row
  COLUMN_1 WIDTH              12                 Train number badge
  COLUMN_2 WIDTH              32                 Destination text
  COLUMN_3 WIDTH              20                 Arrival time

  Total Height: 8 + (2 × 12) = 32 pixels ✓
  Total Width: 12 + 32 + 20 = 64 pixels ✓

═══════════════════════════════════════════════════════════════════════════════

COLUMN LAYOUT DETAILS:

  Column 1 (Train Badge): Pixels 0-11
    • Red circle (radius 5) centered at pixel 6
    • Yellow "R" text in center
    • Fixed width

  Column 2 (Destination): Pixels 12-43
    • White text, left-aligned with 2px padding
    • Font: Monospace 7-8pt
    • Longer names truncated (TODO: marquee scrolling)
    • Example: "Whitehall", "Cortlandt", "Herald Sq", "Bay Ridge"

  Column 3 (Time): Pixels 44-63
    • Cyan text, left-aligned with 2px padding
    • Font: Bold monospace 9pt
    • Right-justified in column
    • Format: "N Min" or "NOW" or "1 Min"

═══════════════════════════════════════════════════════════════════════════════

SAMPLE DISPLAY STATES:

STATE 1: Normal - Two trains arriving
┌────────────────────────────────────────────────────────────┐
│ NORTHBOUND                                                 │
├────────────────────────────────────────────────────────────┤
│ [R]  Whitehall            5 Min                            │
├────────────────────────────────────────────────────────────┤
│ [R]  Herald Sq            11 Min                           │
└────────────────────────────────────────────────────────────┘

STATE 2: One train arriving soon
┌────────────────────────────────────────────────────────────┐
│ SOUTHBOUND                                                 │
├────────────────────────────────────────────────────────────┤
│ [R]  Bay Ridge            NOW                              │
├────────────────────────────────────────────────────────────┤
│ [R]  Borough Hall         8 Min                            │
└────────────────────────────────────────────────────────────┘

STATE 3: No trains (unlikely but handled)
┌────────────────────────────────────────────────────────────┐
│ NORTHBOUND                                                 │
├────────────────────────────────────────────────────────────┤
│ (empty)                                                    │
├────────────────────────────────────────────────────────────┤
│ (empty)                                                    │
└────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

RENDERING PIPELINE:

  1. API Fetch                    (every 10 seconds)
     └─ Get MTA GTFS-RT feed
     └─ Extract northbound & southbound trains
     └─ Calculate arrival times

  2. Frame Selection              (every 5 seconds)
     └─ Alternate between northbound and southbound
     └─ Get top 2 trains for display direction

  3. Image Generation
     └─ Create 64x32 RGB PIL Image
     └─ Draw header with direction text
     └─ Draw train row 1: badge + destination + time
     └─ Draw train row 2: badge + destination + time

  4. Display Output
     ├─ Hardware mode:  Send to LED matrix via rgbmatrix library
     └─ Test mode:      Save PNG image to /tmp/

  5. Refresh                      (30 FPS)
     └─ Update display continuously
     └─ Clear and redraw each frame

═══════════════════════════════════════════════════════════════════════════════

RESPONSIVE ADAPTATION:

  • Text is automatically formatted for 32px height
  • Long destination names truncated to fit 32 pixels
  • Font sizes optimized for readability at typical viewing distance
  • Times update in real-time (1 sec refresh cycle)
  • New API data fetched every 10 seconds

═══════════════════════════════════════════════════════════════════════════════

TYPICAL VIEWING SCENARIOS:

Distance:        Details Visible:              Typical Location:
─────────────────────────────────────────────────────────────────────
2-3 feet         All text readable             Desktop, shelf
4-6 feet         Train # and time clear       Wall mount, entryway
8-10 feet        Train # visible (time small) Across room
15+ feet         Colors visible (text unclear) Hallway at distance

  Note: Actual visibility depends on LED pixel pitch and brightness

═══════════════════════════════════════════════════════════════════════════════

CUSTOMIZATION OPTIONS:

  To add a 3rd train row:
    • Increase display height to 44 pixels (if available)
    • Or reduce font sizes
    • Update ROW_HEIGHT and layout calculations

  To change colors:
    • Modify COLORS dict in display_manager.py
    • E.g., change yellow to green, red to blue

  To change frame duration:
    • Edit FRAME_DURATION in config.py
    • Default: 5 seconds (try 3-10 range)

  To change refresh rate:
    • Edit DISPLAY_FPS in config.py
    • Higher = smoother (default 30 is good)

═══════════════════════════════════════════════════════════════════════════════

Remember: The display is optimized for a 32x64 LED matrix specifically!
All dimensions, fonts, and colors are tailored for this resolution.
"""

print(layout_reference)

# Save this reference
with open('/tmp/DISPLAY_LAYOUT_REFERENCE.txt', 'w') as f:
    f.write(layout_reference)

print("\n✓ Layout reference saved to /tmp/DISPLAY_LAYOUT_REFERENCE.txt")
