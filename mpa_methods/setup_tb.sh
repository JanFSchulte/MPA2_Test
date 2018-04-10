#!/usr/bin/bash

source ~/FC7/sw/fc7/setup.sh
cd ~/FC7/sw/fc7/tests
./bin/fc7-d19c.exe -i 192.168.1.79 -l
./bin/fc7-d19c.exe -i 192.168.1.79 -n d19c_mpa_test_long_counters.bin
sudo udevadm control --reload-rules
modprobe ni_usb_gpib
cd ~/MPA_Test
./start_rtb.py
