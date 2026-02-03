from machine import UART, Pin, I2C, SPI
from ht16k33segment import HT16K33Segment
from micropyGPS import MicropyGPS
import time
import st7789py as st7789
import config
import fonts.vga1_16x32 as font

# Debug print control
DEBUG = True  # Set to False to disable [DEBUG] messages
def debug_print(msg):
    if DEBUG:
        print(msg)


# Helper function to process GPS data and update fix state
def process_gps(gps_uart, my_gps, had_fix):
    """
    Reads and parses GPS data from UART, updates my_gps, and manages fix state.
    Returns updated had_fix value.
    """
    if gps_uart.any():
        raw_data = gps_uart.read()
        if raw_data:
            for b in raw_data:
                try:
                    my_gps.update(chr(b))
                except Exception:
                    continue
    # Check for State Changes in 3D Fix
    if my_gps.fix_type < 3 and had_fix:
        print("ALERT: 3D Fix Lost! Time may drift.")
        had_fix = False
    elif my_gps.fix_type == 3 and not had_fix:
        print("SUCCESS: 3D Fix Regained.")
        had_fix = True
    return had_fix


# Helper function for 7-segment display update
def update_7segment_display(display, hours, minutes, seconds, had_fix):
    if had_fix:
        display.set_number(hours // 10, 0)
        display.set_number(hours % 10, 1)
        display.set_number(minutes // 10, 2)
        display.set_number(minutes % 10, 3)
        # Colon Logic: Flash if 3D Fix is active
        colon_state = int(seconds) % 2 == 0
        display.set_colon(colon_state)
    else:
        for pos in range(4):
            #display.set_number(0, pos)  # Show zero when no fix
            display.set_character('-', pos)
    display.draw()

# Helper function for LCD display update
def update_lcd_display(tft, font, new_date, new_lat, new_lon, new_alt, new_sats):
    global _prev_lcd_lines
    if tft is not None:
        if '_prev_lcd_lines' not in globals():
            _prev_lcd_lines = {
                'date': '',
                'lat': '',
                'lon': '',
                'alt': '',
                'sats': ''
            }
        lcd_lines = [
            ('date', new_date, 10),
            ('lat', new_lat, 50),
            ('lon', new_lon, 90),
            ('alt', new_alt, 130),
            ('sats', new_sats, 170)
        ]
        try:
            for key, value, y in lcd_lines:
                if _prev_lcd_lines[key] != value:
                    tft.fill_rect(10, y, 220, 38, st7789.BLUE)
                    tft.text(font, value, 10, y, st7789.WHITE, st7789.BLUE)
                    _prev_lcd_lines[key] = value
        except Exception as e:
            print(f"[ERROR] LCD update failed: {e}")

# Helper to get local time with offset
def get_local_time(gps_obj):
    h, m, s = gps_obj.timestamp
    return (h + config.STD_OFFSET) % 24, m, s

# Main function
def main():
    # 1. SETUP I2C and 7-segment Display
    i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN), freq=config.I2C_FREQ)
    devices = i2c.scan()
    if devices:
        print(f"[I2C] Found devices at addresses: {[hex(addr) for addr in devices]}")
    else:
        print("[I2C] No I2C devices found!")
    display = HT16K33Segment(i2c, 0x70)
    for pos in range(4):
        #display.set_number(0, pos)  # Show zero when no fix
        display.set_character('-', pos)
        
    # 2. SETUP LCD with debug and error handling
    try:
        debug_print("[LCD] Initializing TFT display...")
        spi = SPI(config.SPI_ID, baudrate=config.SPI_BAUDRATE, polarity=0, phase=0, sck=Pin(config.SPI_SCK_PIN), mosi=Pin(config.SPI_MOSI_PIN))
        tft = st7789.ST7789(
            spi,
            240, 320,  # width, height updated for your display
            reset=Pin(config.ST7789_RST, Pin.OUT),
            dc=Pin(config.ST7789_DC, Pin.OUT),
            cs=Pin(config.ST7789_CS, Pin.OUT),
            backlight=Pin(config.ST7789_BL, Pin.OUT),
            rotation=1
        )
        if tft is not None:
            debug_print("[LCD] TFT display initialized successfully.")
            tft.fill(st7789.BLUE)
            time.sleep(1)
        else:
            debug_print("[LCD] TFT display initialization returned None.")
    except Exception as e:
        print(f"[ERROR] TFT display initialization failed: {e}")
        tft = None

    # 3. SETUP GPS  
    gps_uart = UART(0, baudrate=9600)
    my_gps = MicropyGPS()
    had_fix = False

    # 4. NTP SERVER REMOVED
    # NTP and network code removed

    def main_loop():
        nonlocal had_fix
        while True:
            had_fix = process_gps(gps_uart, my_gps, had_fix)

            hours, minutes, seconds = get_local_time(my_gps)
            day, month, year = my_gps.date if hasattr(my_gps, 'date') else (0, 0, 0)
            if hasattr(my_gps, 'coord_format'):
                my_gps.coord_format = 'dms'
            lat_dms = my_gps.latitude if hasattr(my_gps, 'latitude') else [0, 0, 0, 'N']
            lon_dms = my_gps.longitude if hasattr(my_gps, 'longitude') else [0, 0, 0, 'E']
            alt = my_gps.altitude if hasattr(my_gps, 'altitude') else 0.0
            sats_in_view = my_gps.satellites_in_view if hasattr(my_gps, 'satellites_in_view') else 0
            sats_used = 0
            if hasattr(my_gps, 'satellites_used'):
                su = my_gps.satellites_used
                if isinstance(su, (list, tuple)):
                    sats_used = len(su)
                elif isinstance(su, int):
                    sats_used = su

            # Prepare new values
            new_date = f"Date: {day:02}/{month:02}/20{year:02}"
            new_lat = f"Lat: {lat_dms[0]:02.0f}\u00b0{lat_dms[1]:02d}'{lat_dms[2]:02d}\" {lat_dms[3]}"
            new_lon = f"Lon: {lon_dms[0]:03.0f}\u00b0{lon_dms[1]:02d}'{lon_dms[2]:02d}\" {lon_dms[3]}"
            new_alt = f"Alt: {alt:.1f}m"
            new_sats = f"Sats: {sats_in_view}/{sats_used}"

            update_7segment_display(display, hours, minutes, seconds, had_fix)
            update_lcd_display(tft, font, new_date, new_lat, new_lon, new_alt, new_sats)

            time.sleep(0.1)


    # Start main loop (asyncio removed)
    try:
        main_loop()
    except KeyboardInterrupt:
        print("[INFO] Program terminated by user (CTRL-C)")
        time.sleep(0.1)

if __name__ == "__main__":
    main()

