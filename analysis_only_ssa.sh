#!/bin/sh

source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
#in /etc/ethers put
#sudo /etc/init.d/network restart

printf '______________________________________________________\n'
printf '             Starting SSA Test System                 \n'
printf '             analysis only mode                       \n'

echo ""
echo "from myScripts import *"      > LaunchPy.py
echo "from ssa_methods import *"    >> LaunchPy.py

cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

printf '______________________________________________________\n'
python -i LaunchPy.py
