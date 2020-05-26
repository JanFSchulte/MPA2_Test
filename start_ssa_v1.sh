#!/bin/sh

start_tb='python3 -i LaunchPy.py'

source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export LC_ALL=C; unset LANGUAGE

#in /etc/ethers put
#sudo /etc/init.d/network restart

file="./utilities/ipaddr_ssa.dat"
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
echo "from d19cScripts import *" >  LaunchPy.py
echo "from myScripts import *" >> LaunchPy.py
echo "from ssa_methods import *" >> LaunchPy.py
#echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('ssa') "  >> LaunchPy.py
echo "from utilities import tbconfig " >  utilities/tbsettings.py
echo "tbconfig.VERSION['SSA'] = 1" >> utilities/tbsettings.py
echo "tbconfig.VERSION['MPA'] = 1" >> utilities/tbsettings.py

cp ./utilities/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unrichable\n    '
	if (! ifconfig | grep ${eth}:'1'); then
		read -r -p "    Do you want to configure the communication? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			sudo /usr/sbin/rarpd -a
			sudo ifconfig ${eth}:1 192.168.0.100
			sudo udevadm control --reload-rules
			sudo modprobe ni_usb_gpib
			ping -c 1 -W 1 $IP; rep=$?
			if ! (( $rep == 0 )); then
				printf   '\n->  SSA Testbench unrichable\n'
			else
				printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
				printf '______________________________________________________\n'
				$start_tb
			fi
		fi
	else
		printf "\n-> Communication configured  "
		echo ${eth}
		printf '\n'
	fi

	if [ -z "$1" ]; then
		read -r -p "    Do you want to proceed anyways? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			printf '______________________________________________________\n'
			$start_tb
		else
			printf '\nExiting.\n\n'
			printf '______________________________________________________\n'
		fi
	elif [[  $1 == y ]]; then
			printf '______________________________________________________\n'
			$start_tb
	fi
else
	printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
	$start_tb
fi
