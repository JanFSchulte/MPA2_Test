#!/usr/bin/bash

source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

if ! ifconfig | grep 'enp0s31f6:1'; then
	sudo /usr/sbin/rarpd -a
	sudo ifconfig enp0s31f6:1 192.168.1.4
	sudo udevadm control --reload-rules	
	sudo modprobe ni_usb_gpib
fi



ping 192.168.1.33 -c 1

echo ""
echo "from d19cScripts import *"                                              >  LaunchPy.py
echo "from myScripts import *"                                                >> LaunchPy.py
echo "from ssa_methods import *"                                              >> LaunchPy.py

cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

python -i LaunchPy.py
