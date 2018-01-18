#!/usr/bin/bash

if ! ifconfig | grep 'em1:1'; then
	sudo /usr/sbin/rarpd -a
	sudo ifconfig em1:1 192.168.01.81
fi

ping 192.168.1.79 -c 1
source ~/FC7/sw/fc7/setup.sh
echo ""
echo ""
echo "____________________________________________________"
echo ""
echo "from d19cScripts import *"                        >  LaunchPy.py
echo "from myScripts import *"                          >> LaunchPy.py
echo "  "                                               >> LaunchPy.py
echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('MPA') "  >> LaunchPy.py
cp ./myScripts/ipaddr_mpa.dat  d19cScripts/ipaddr.dat
python -i LaunchPy.py
