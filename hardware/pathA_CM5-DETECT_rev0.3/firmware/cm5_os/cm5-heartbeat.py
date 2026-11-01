#!/usr/bin/env python3
"""Heartbeat for the hardware watchdog (supervisor MCU). Toggles GPIO22 every 0.5 s while the
application is alive. The application touches /run/birdwatch.alive (or set WATCH_FILE=""
to only check that the OS is alive). If the file is older than 10 s, toggling stops and the
supervisor cold-resets the CM5 after its timeout (default 20 s). Also drives RUN LED (GPIO20)."""
import os, time
import gpiod
from gpiod.line import Direction, Value
WATCH = os.environ.get('WATCH_FILE', '/run/birdwatch.alive')
chip = gpiod.request_lines('/dev/gpiochip0', consumer='heartbeat',
        config={22: gpiod.LineSettings(direction=Direction.OUTPUT), 20: gpiod.LineSettings(direction=Direction.OUTPUT)})
s = False
while True:
    alive = (not WATCH) or (os.path.exists(WATCH) and time.time() - os.path.getmtime(WATCH) < 10)
    if alive:
        s = not s
        chip.set_value(22, Value.ACTIVE if s else Value.INACTIVE)
        chip.set_value(20, Value.INACTIVE if s else Value.ACTIVE)   # RUN LED blinks 1 Hz
    else:
        chip.set_value(20, Value.ACTIVE)                             # RUN LED off (active low)
    time.sleep(0.5)
