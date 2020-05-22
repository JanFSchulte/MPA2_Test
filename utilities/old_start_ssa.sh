#!/bin/sh

source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

file="./myScripts/ipaddr_ssa.dat"
while IFS= read -r line
do
	IP=$line
	printf 'IP=%s\n' "$line"
done <"$file"

eth=`ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}'`

printf '______________________________________________________\n'
printf '             Starting SSA Test System                 \n'
printf '                                                      \n'

echo ""
echo "from d19cScripts import *"    >  LaunchPy.py
echo "from myScripts import *"      >> LaunchPy.py
echo "from ssa_methods import *"    >> LaunchPy.py
cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unrichable\n    '
	if (! ifconfig | grep ${eth}:'1'); then
		printf '\n->  Ethernet interface not found\n'
		read -r -p "    Do you want to configure the communication? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			sudo /usr/sbin/rarpd -a
			sudo ifconfig ${eth}:1 192.168.0.90
			sudo udevadm control --reload-rules
			sudo modprobe ni_usb_gpib
			ping -c 1 -W 1 $IP; rep=$?
			if ! (( $rep == 0 )); then
				printf   '\n->  SSA Testbench unrichable\n'
			else
				printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
				printf '______________________________________________________\n'
				python -i LaunchPy.py
			fi
		fi
	else
		printf "\n->  Ethernet interface found  "
		echo ${eth}
		printf '\n'
	fi

	if [ -z "$1" ]; then
		read -r -p "    Do you want to proceed anyways? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			printf '______________________________________________________\n'
			python -i LaunchPy.py
		else
			printf '\nExiting.\n\n'
			printf '______________________________________________________\n'
		fi
	elif [[  $1 == y ]]; then
			printf '______________________________________________________\n'
			python -i LaunchPy.py
	fi
else
	printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
	python -i LaunchPy.py
fi
