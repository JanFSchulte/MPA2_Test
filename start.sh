#!/usr/bin/bash
sudo /usr/sbin/rarpd -a
sudo ifconfig em1:1 192.168.01.81
ping 192.168.1.79
source ~/FC7/sw/fc7/setup.sh
python -i LaunchPy.py
