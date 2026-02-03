
# Pico-NTP-Server

This project implements a MicroPython-based NTP server using a GPS module for accurate time, displaying live GPS data on both an ST7789V color LCD and a 4-digit 7-segment display (HT16K33). Designed for the Raspberry Pi Pico (or similar), with WIZNET5K Ethernet, GPS, and display modules.


## Features
- NTP server using GPS as a time source
- Live display of:
	- Date (from GPS)
	- Position (latitude, longitude)
	- Altitude
	- Satellites (used/visible)
	- Time (on 7-segment display)
- ST7789V color LCD for full info
- HT16K33 7-segment display for time
- Ethernet configuration for WIZNET5K
- Modular configuration via `config.py`


## Hardware Requirements
- MicroPython-compatible board (e.g., Raspberry Pi Pico)
- WIZNET5K Ethernet module
- ST7789V SPI color display
- GPS module (UART)
- HT16K33 I2C segment display (for time)


## File Overview
- `main.py`: Main application logic, hardware setup, and main loop
- `config.py`: All hardware pin assignments and global constants
- `st7789py.py`: ST7789V display driver
- `ht16k33.py`, `ht16k33segment.py`: 7-segment display drivers
- `micropyGPS.py`: GPS parsing library
- `ntp_server.py`: NTP server implementation


## Usage
1. Edit `config.py` to match your hardware pinout and network settings.
2. Flash all files to your MicroPython device.
3. Connect the required hardware (Ethernet, GPS, LCD, 7-segment display).
4. Run `main.py`.


## Notes
- The LCD shows date, position, altitude, and satellite info live from GPS.
- The 7-segment display shows the current time.
- The NTP server will only serve accurate time after a GPS 3D fix is acquired.


## License
MIT License. See source files for details.

---

GitHub: [https://github.com/dancingbear1965/Pico-NTP-Server](https://github.com/dancingbear1965/Pico-NTP-Server)
