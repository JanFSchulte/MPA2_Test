
#!/usr/bin/bash

source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export LC_ALL=C; unset LANGUAGE

#   file="./utilities/ipaddr_ssa.dat"
#   while IFS= read -r line
#   do
#           IP=$line
#   	printf 'IP=%s\n' "$line"
#   done <"$file"

IP="192.168.0.79"
eth=`ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}'`

printf '______________________________________________________\n'
printf '           Starting SSA-MPA Test System               \n'
printf '                                                      \n'

cp ./myScripts/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unrichable\n    '
	if (! ifconfig | grep ${eth}:'1'); then
		read -r -p "    Do you want to configure the communication? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			sudo /usr/sbin/rarpd -a
			sudo ifconfig ${eth}:1 192.168.0.100
			ping -c 1 -W 1 $IP; rep=$?
			if ! (( $rep == 0 )); then
				printf '\n->  Testbench unrichable\n'
			else
				printf '\n->  Testbench correctly found on %s\n' "$IP"
			fi
		fi
	fi
fi

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf '\n->  Testbench unreachable. Verify connectivity\n'
else
	printf '\n->  Testbench correctly found on %s\n' "$IP"
	printf '\n->  Starting loading the firmware\n'
	cd ~/FC7/sw/fc7/tests
	#./bin/fc7-d19c.exe  -i $IP -n d19c_2ssa_none_14082019.bit -f ~/MPA-SSA_Test/bitfiles/d19c_2ssa_none_14082019.bit
	./bin/fc7-d19c.exe  -i $IP -n d19c_2ssa_none_14082019.bit 

	cd -
fi
