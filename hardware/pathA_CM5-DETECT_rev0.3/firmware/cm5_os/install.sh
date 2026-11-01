#!/bin/sh
# run on the CM5 once (from the PC over USB-C #1: ssh pi@raspberrypi.local)
set -e
cat config.txt.append >> /boot/firmware/config.txt
rpi-eeprom-config --apply eeprom.conf
install -m755 cm5-heartbeat.py /usr/local/bin/
install -m644 cm5-heartbeat.service birdwatch.service /etc/systemd/system/
mkdir -p /data/state
systemctl enable cm5-heartbeat birdwatch
# read-only root with overlay: power loss can not corrupt the OS; /data is a separate ext4 partition
raspi-config nonint do_overlayfs 0 || true
echo "done, reboot"
