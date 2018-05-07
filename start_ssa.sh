#!/usr/bin/bash

source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

eth=`ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}'`
printf '______________________________________________________\n'
printf '             Starting SSA Test System                 \n'
printf '                                                      \n'

if ! ifconfig | grep ${eth}:'1'; then
	printf '\n->  Ethernet interface =' ${eth}':1' 'not found\n'
	sudo /usr/sbin/rarpd -a
	sudo ifconfig ${eth}:1 192.168.1.4
	sudo udevadm control --reload-rules	
	sudo modprobe ni_usb_gpib
else
	printf '\n->  Ethernet interface found  ' 
	echo ${eth}
	printf '\n'
fi

echo ""
echo "from d19cScripts import *"    >  LaunchPy.py
echo "from myScripts import *"      >> LaunchPy.py
echo "from ssa_methods import *"    >> LaunchPy.py
cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 192.168.1.33; rep=$?

if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unrichable\n'
	read -r -p "    Do you want to proceed anyways? [y/N] " response
	if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
		python -i LaunchPy.py
	else
		printf '\nExiting.\n\n'
		printf '______________________________________________________\n'
	fi
else
	printf '\n->  SSA Testbench correctly found on IP 192.168.1.33\n'
	python -i LaunchPy.py
fi



