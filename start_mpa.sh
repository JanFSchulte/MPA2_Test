#!/usr/bin/bash

# 08:00:30:00:22:58

if ! ifconfig | grep 'enp0s25:1'; then
	sudo /usr/sbin/rarpd -a
	sudo ifconfig enp0s25:1 192.168.5.87
fi

#ping 192.168.1.79 -c 1
ping 192.168.5.202 -c 1
source ~/FC7/sw/fc7/setup.sh
echo ""
echo ""
echo "____________________________________________________"
echo ""
echo "from d19cScripts import *"                        >  LaunchPy.py
echo "from myScripts import *"                          >> LaunchPy.py
echo "  "                                               >> LaunchPy.py
echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('MPA') "  >> LaunchPy.py
#echo "from mpa_methods.cal_utility import * "  >> LaunchPy.py
echo "from mpa_methods.mpa_i2c_conf import *"  >> LaunchPy.py
echo "from mpa_methods.fast_readout_utility import *"  >> LaunchPy.py
echo "from mpa_methods.bias_calibration import *"  >> LaunchPy.py
echo "from mpa_methods.power_utility import *"  >> LaunchPy.py
cp ./myScripts/ipaddr_mpa.dat  d19cScripts/ipaddr.dat
python -i LaunchPy.py
