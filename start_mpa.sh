#!/usr/bin/bash

if ! ifconfig | grep 'enp0s31f6:1'; then
	sudo /usr/sbin/rarpd -a
	sudo ifconfig enp0s31f6:1 192.168.1.82
fi

ping 192.168.1.79 -c 1
#ping 192.168.5.202 -c 1
source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

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
echo "from mpa_methods.mpa_power_utility import *"  >> LaunchPy.py
echo "from mpa_methods.fast_readout_utility import *"  >> LaunchPy.py
echo "from mpa_methods.bias_calibration import *"  >> LaunchPy.py
echo "from mpa_methods.krum_test import *"  >> LaunchPy.py

cp ./myScripts/ipaddr_mpa.dat  d19cScripts/ipaddr.dat
python -i LaunchPy.py
