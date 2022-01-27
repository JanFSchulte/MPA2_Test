#!/usr/bin/bash

# Makes use of new addressing scheme and Ph2_ACF Middleware to program FC7
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export LC_ALL=C; unset LANGUAGE

#   file="./utilities/ipaddr_ssa.dat"
#   while IFS= read -r line
#   do
#           IP=$line
#   	printf 'IP=%s\n' "$line"
#   done <"$file"

IP="192.168.1.79"
eth=`ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}'`

printf '______________________________________________________\n'
printf '           Starting SSA-MPA Test System               \n'
printf '                                                      \n'

IP=$(<utilities/ipaddr.dat)

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unreachable\n    '
	if (! ifconfig | grep ${eth}:'1'); then
		read -r -p "    Do you want to configure the communication? [y/N] " response
		if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
			sudo /usr/sbin/rarpd -a
			sudo ifconfig ${eth}:1 192.168.1.79
			ping -c 1 -W 1 $IP; rep=$?
			if ! (( $rep == 0 )); then
				printf '\n->  Testbench unreachable\n'
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
	cd ~/Ph2_ACF
    source ~/Ph2_ACF/setup.sh
	# check if FC7/D19C_MPA_PreCalib.xml has correct IP address in header!
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_04082021.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i d19c_mpa_none_28042019.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_configDelay.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_noDelay_wSEU.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_wDelay_wSEU_s.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA2_130122.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_wSEU_postMerge.bin
	fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_SEU_Dev_PM.bin 
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_configDelay_wSEU.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i uDTC_MPA_20102021.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i mpa_scanchain_20MHz_221021.bin #good for carrier board
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i mpa_scanchain_5MHz_221021.bin #good for carrier board
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i mpa_board_on_l12_211021.bin
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i mpa_scanchain_20MHz_281021.bin #good for probe card
	#fpgaconfig -c FC7/D19C_MPA_PreCalib.xml -i mpa_scanchain_5MHz_281021.bin #good for probe card

	cd
fi