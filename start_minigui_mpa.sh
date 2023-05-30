#!/bin/sh

# first argument

start_tb='python3.6 -i LaunchMiniGUI.py'

source ./FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export LC_ALL=C; unset LANGUAGE

BOARD_MAC='08:00:30:00:29:8e'
MPA_ADR_0=0b1000000
SSA_ADR_0="0b0100000"
SSA_ADR_1="0b0100111"
CHIP_SELECT="MPA"

file="./utilities/ipaddr.dat"
while IFS= read -r line
do
	IP=$line
	printf 'IP=%s\n' "$line"
done <"$file"

eth=`ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}'`

printf '______________________________________________________\n'
printf '             Starting MPA2 Test System                 \n'
printf '                                                      \n'

echo ""
echo "from utilities import *" >  LaunchPy.py
#echo "from myScripts import *" >> LaunchPy.py
echo "from main import *" >> LaunchPy.py
#echo "ipaddr, fc7AddrTable, fc7 = SelectBoard('ssa') "  >> LaunchPy.py
echo "from utilities import tbconfig " >  utilities/tbsettings.py



# override default values
echo "tbconfig.VERSION['SSA'] = 2" >> utilities/tbsettings.py
echo "tbconfig.VERSION['MPA'] = 1" >> utilities/tbsettings.py
echo "tbconfig.BOARD_SELECT = '$BOARD_MAC'" >> utilities/tbsettings.py
echo "tbconfig.MPA_ADR[0] = $MPA_ADR_0" >> utilities/tbsettings.py
#echo "tbconfig.SSA_ADR[0] = $SSA_ADR_0" >> utilities/tbsettings.py
#echo "tbconfig.SSA_ADR[1] = $SSA_ADR_1" >> utilities/tbsettings.py

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf '\n=>  MPA Testbench unreachable\n    '
	if (! ifconfig | grep ${eth}:'1'); then
		read -r -p "    Do you want to configure the communication? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			sudo /usr/sbin/rarpd -a
			sudo ifconfig ${eth}:1 192.168.1.100
			sudo udevadm control --reload-rules
			sudo modprobe ni_usb_gpib
			ping -c 1 -W 1 $IP; rep=$?
			if ! (( $rep == 0 )); then
				printf '=>  MPA Testbench unreachable'
			else
				printf '=>  MPA Testbench correctly found on %s' "$IP"
				#printf '______________________________________________________\n'
				printf '=>  Loading scripts\n'
				$start_tb
			fi
		fi
	else
		printf '=>  The communication is configured  '
		echo ${eth}
	fi

	if [ -z "$1" ]; then
		#read -r -p "    Do you want to proceed anyways? [y/N] " response
		response='y'
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			#printf '______________________________________________________\n'
			printf '=>  Loading scripts\n'
			$start_tb
		else
			printf '=> Exiting.\n\n'
			#printf '______________________________________________________\n'
		fi
	elif [[  $1 == y ]]; then
			#printf '______________________________________________________\n'
			printf '=>  Loading scripts\n'
			$start_tb
	fi
else
	printf '=>  MPA Testbench correctly found at address %s\n' "$IP"
	printf '=>  Loading scripts\n'
	$start_tb
fi
