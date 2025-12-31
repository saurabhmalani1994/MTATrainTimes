# Quick Start Guide - MTA Train Display

Get your MTA train display up and running in 15 minutes!

## 30-Second Setup (No Hardware Needed)

```bash
# 1. Install dependencies
pip3 install requests pillow protobuf gtfs-realtime-bindings

# 2. Run in test mode
python3 main.py

# See "Troubleshooting" if you get errors
```

That's it! The display will run and save test images.

## Full Setup with Raspberry Pi LED Matrix

### Prerequisites
- Raspberry Pi 3B+, 4, or 5
- 32x64 RGB LED matrix
- Adafruit RGB Matrix Bonnet (or know how to wire GPIO)
- 5V power supply for LED matrix

### Step 1: Download Files (5 minutes)

```bash
cd ~
git clone https://github.com/yourusername/mta-display.git
cd mta-display
# Or download all .py files manually
```

### Step 2: Install Dependencies (5 minutes)

```bash
# Update system
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3-pip

# Install Python packages
pip3 install -r requirements.txt

# Install LED matrix library
pip3 install rgbmatrix
# (See README.md for alternative installation methods)
```

### Step 3: Configure Your Station (2 minutes)

Edit `config.py`:

```python
# Default is 25th St R train (Brooklyn)
# No changes needed if that's what you want!

# Otherwise, find your STOP_ID and ROUTE_ID:
STOP_ID = '414'    # Change this
ROUTE_ID = 'R'     # Change this
FEED_PATH = 'gtfs-nqrw'  # Change if needed
```

**Finding your stop/route IDs:**
- Visit: https://new.mta.info/developers
- Download static GTFS data
- Search for your station in `stops.txt` to find STOP_ID
- Find your route in the same file

### Step 4: Test Without Hardware (2 minutes)

```bash
python3 test_display.py

# Follow prompts:
# 1. API Connection - should show ✓ PASS
# 2. Train Parsing - should show trains
# 3. Display Rendering - will save test images
# 4. Live Test - shows real train data
```

### Step 5: Connect LED Matrix Hardware (5 minutes)

**Option A: Using Adafruit Matrix Bonnet**
1. Solder header to bonnet
2. Plug bonnet into Raspberry Pi GPIO (40-pin header)
3. Connect matrix ribbon cable to bonnet IDC connector
4. Connect 5V power to matrix
5. Done!

**Option B: Direct Wiring**
- See wiring diagram in README.md
- Use level shifters for 5V signals!

### Step 6: Run the Display

```bash
# One-time test with hardware
python3 main.py

# Should see actual train times on your LED matrix!
# Press Ctrl+C to stop

# Or run as a service (starts on boot)
sudo systemctl enable mta-display
sudo systemctl start mta-display
sudo systemctl status mta-display
```

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| "No module named 'requests'" | `pip3 install requests` |
| "No module named 'rgbmatrix'" | `pip3 install rgbmatrix` |
| "Permission denied" on GPIO | Run with `sudo python3` or add user to gpio group |
| Black display / not showing | Check matrix power supply (5V), verify cables, increase `GPIO_SLOWDOWN` in config.py |
| API errors | Check internet, verify MTA API working at: https://new.mta.info/developers |
| Text too small on 32x64 | Reduce DISPLAY_FPS or adjust font sizes in display_manager.py |

## File Structure

```
mta-display/
├── main.py           ← Run this to start
├── test_display.py   ← Run this to test
├── config.py         ← Edit this to configure
├── mta_client.py     ← (Don't edit)
├── display_manager.py ← (Don't edit)
├── requirements.txt  ← (Install from this)
├── README.md         ← Full documentation
└── QUICKSTART.md     ← This file
```

## What Each File Does

| File | Purpose |
|------|---------|
| **main.py** | Main application - fetches train data, renders display, alternates frames every 5 seconds |
| **config.py** | Configuration - change station, display settings, API options here |
| **mta_client.py** | MTA API client - talks to MTA servers, parses train data |
| **display_manager.py** | Display rendering - draws frames to LED matrix or saves test images |
| **test_display.py** | Testing tool - verify everything works before running main.py |

## Common Customizations

### Change frame duration (how long each direction shows)

Edit `config.py`:
```python
FRAME_DURATION = 5  # seconds (was 5, change to 10 for longer)
```

### Change display refresh rate

Edit `config.py`:
```python
DISPLAY_FPS = 30  # frames per second (higher = smoother but more CPU)
```

### Fix flickering display

Edit `config.py`:
```python
GPIO_SLOWDOWN = 2  # Try: 1, 2, 3, 4 (higher = clearer)
```

### Change train number color from yellow

Edit `display_manager.py`, line ~90:
```python
draw.text(
    ...,
    fill=self.COLORS['cyan']  # Change 'cyan' to other colors
)
```

Available colors: black, white, yellow, red, green, cyan, magenta, gray

### Show 3 trains instead of 2

Edit `display_manager.py`, look for:
```python
for idx, train in enumerate(trains[:2]):  # Change :2 to :3
```

And adjust ROW_HEIGHT if needed.

## Getting Help

1. **Does it work without LED matrix?**
   ```bash
   python3 test_display.py
   ```
   If API tests pass, your software is OK. Issue is likely hardware.

2. **Check the logs:**
   ```bash
   # If running as service:
   sudo journalctl -u mta-display -f
   
   # Or just run directly:
   python3 main.py  # Shows all error messages
   ```

3. **Verify API is working:**
   ```bash
   curl "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct/gtfs-nqrw" \
     -H "x-api-key: your-key-here" -o feed.pb
   ls -lh feed.pb
   ```

4. **See full README.md** for complete troubleshooting guide

## Next Steps

1. ✅ Get it working with test mode
2. ✅ Connect LED matrix hardware
3. ✅ Run main.py and verify display
4. ✅ Set up as systemd service for auto-start
5. 🎉 Enjoy live NYC subway times on your display!

## Pro Tips

- **Multiple stations?** Duplicate config.py as config_station2.py, import and switch at runtime
- **Want to show multiple lines?** Modify mta_client.py to not filter by route
- **Power saving?** Add buttons to turn display on/off manually
- **Network unreliable?** Cache last good fetch and retry on error (already in code!)
- **Want APIs?** Add Flask to serve train data as JSON to other devices

## Still stuck?

Read the full **README.md** - it has:
- Complete hardware wiring diagram
- Detailed troubleshooting
- Advanced customization examples
- Performance metrics
- Future enhancement ideas

---

**You've got this! Happy NYC transit tracking! 🚇**
