#!/bin/bash
# exit on command failure
set -e

/usr/bin/v4l2-ctl --set-dv-bt-timings query
/usr/bin/v4l2-ctl --log-status

echo "performance" | tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

/usr/bin/python3 /home/pi/backlight