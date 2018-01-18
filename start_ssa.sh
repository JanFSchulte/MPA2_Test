#!/usr/bin/bash
sudo /usr/sbin/rarpd -a
sudo ifconfig eno1:1 192.168.01.03
ping 192.168.1.33 -c 1
source ~/FC7/sw/fc7/setup.sh
echo ""
echo ""
echo "____________________________________________________"
echo ""
echo "from d19cScripts import *"                        >  LaunchPy.py
echo "from myScripts import *"                          >> LaunchPy.py
echo "  "                                               >> LaunchPy.py
echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('SSA') "  >> LaunchPy.py
python -i LaunchPy.py
