
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
	./bin/fc7-d19c.exe  -i $IP -n  MPA_SEU_L1_9.bin  #-f /home/acaratel/D19C/MPA_Test/fw_bitfiles/MPA_SEU_L1_9.bit
	
	
	cd -
fi

#./bin/fc7-d19c.exe  -i $IP -n SSA_SEU_11.bin
#./bin/fc7-d19c.exe  -i $IP -n d19c_SSA_SEU_P2.bit -f ~/MPA-SSA_Test/bitfiles/d19c_SSA_SEU_P1.bit
#./bin/fc7-d19c.exe  -i $IP -n d19c_SSA_SEU_P2.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA2_SEU_20200825.bit -f ~/MPA-SSA_Test/bitfiles/uDTC_SSA2_SEU_20200825.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA2_SEU_20200825.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA_SEU_20200824.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA_SEU_20200824.bit -f ~/MPA-SSA_Test/bitfiles/uDTC_SSA_SEU_20200824.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA_SEU_master.bit -f ~/MPA-SSA_Test/bitfiles/uDTC_SSA_SEU_master.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA_SEU_master.bit
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA1_SEU.bin
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA1_SEU.bin
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA2_SEU_10092020.bin
#./bin/fc7-d19c.exe  -i $IP -n uDTC_SSA2_SEU_10092020_v2.bin
#./bin/fc7-d19c.exe  -i $IP -n SSAx1_SEU_oldFW_newPhT.bit -f ~/MPA-SSA_Test/bitfiles/SSAx1_SEU_oldFW_newPhT_14092020.bit


#./bin/fc7-d19c.exe  -i $IP -n d19c_SSA_SEU_2020.08.19.bit
#./bin/fc7-d19c.exe  -i $IP -n SSA_SEU_11.bin
#./bin/fc7-d19c.exe  -i $IP -n d19c_SSA_SEU_2020.08.19.bit -f ~/MPA-SSA_Test/bitfiles/d19c_SSA_SEU_2020.08.19.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_11 -f ~/MPA-SSA_Test/bitfiles/SSA_SEU_11.bit
#./bin/fc7-d19c.exe  -i $IP -n  D19C_SSA_V-2018-06-12.bin -f ~/D19C/MPA_Test/fw_bitfiles/D19C_SSA_V-2018-06-12.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_7.bin -f ~/D19C/bitfiles/SEU/SSA_SEU_7.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_10.bin -f ~/D19C/bitfiles/SEU/SSA_SEU_10.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_11.bin -f ~/D19C/bitfiles/SEU/SSA_SEU_11.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_12.bin -f ~/D19C/bitfiles/SEU/SEU_SSA_12.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_11.bit -f ~/Desktop/SSA_SEU_11.bit
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_7.bin
#./bin/fc7-d19c.exe  -i $IP -n  MPA_SEU_L1_9.bin -f ~/D19C/MPA_Test/fw_bitfiles/MPA_SEU_L1_9.bit
# USE SSA_SEU_11.bin for SSA tests on carrier board
#./bin/fc7-d19c.exe  -i $IP -n  SSA_SEU_11.bin
# USE d19c_ssa_none_16052019.bin for SSA tests on wafer (swapped signals on probe card)
#./bin/fc7-d19c.exe  -i $IP -n  d19c_ssa_none_16052019_v2.bin -f ~/MPA_Test/fw_bitfiles/d19c_ssa_none_16052019_v2.bit
#./bin/fc7-d19c.exe  -i $IP -n  d19c_ssa_none_16052019_v2.bin
