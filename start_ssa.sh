#!/usr/bin/bash

if ! ifconfig | grep 'eno1:1'; then
	sudo /usr/sbin/rarpd -a
	sudo ifconfig eno1:1 192.168.01.03
fi

ping 192.168.1.33 -c 1
source ~/FC7/sw/fc7/setup.sh
echo ""
echo ""
echo "____________________________________________________"
echo ""
echo "from d19cScripts import *"                        >  LaunchPy.py
echo "from myScripts import *"                          >> LaunchPy.py
echo "from ssa_methods import *"                        >> LaunchPy.py
echo "  "                                               >> LaunchPy.py
echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('SSA') "  >> LaunchPy.py
echo "  "                                               >> LaunchPy.py
echo "ssa = SSA_handle() "                              >> LaunchPy.py

cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat
python -i LaunchPy.py
