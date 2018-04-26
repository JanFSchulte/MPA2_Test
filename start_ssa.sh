#!/usr/bin/bash

if ! ifconfig | grep 'enp0s31f6:1'; then
	sudo /usr/sbin/rarpd -a
	sudo ifconfig enp0s31f6:1 192.168.01.04
fi

ping 192.168.1.33 -c 1
source ~/FC7/sw/fc7/setup.sh
echo ""
echo "from d19cScripts import *"                                              >  LaunchPy.py
echo "from myScripts import *"                                                >> LaunchPy.py
echo "from ssa_methods import *"                                              >> LaunchPy.py
#echo "  "                                                                     >> LaunchPy.py
#echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('SSA') "                        >> LaunchPy.py
#echo "from ssa_methods.cal_utility import * "                                 >> LaunchPy.py
#echo "from ssa_methods.readout_utility import * "                             >> LaunchPy.py
#echo "  "                                                                     >> LaunchPy.py
#echo "ssa = SSA_handle(I2C, fc7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map) " >> LaunchPy.py
#echo "init_all() "                                      >> LaunchPy.py
cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
python -i LaunchPy.py
