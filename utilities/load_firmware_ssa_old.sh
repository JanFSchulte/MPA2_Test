#!/usr/bin/bash

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

if ! ifconfig | grep ${eth}:'1'; then
	printf '\n->  Ethernet interface =' ${eth}':1' 'not found\n'
	sudo /usr/sbin/rarpd -a
	sudo ifconfig ${eth}:1 192.168.0.4
	sudo udevadm control --reload-rules
	sudo modprobe ni_usb_gpib
else
	printf '\n->  Ethernet interface found  '
	echo ${eth}
	printf '\n'
fi

ping -c 1 -W 1 $IP; rep=$?

if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unreachable. Verify connectivity\n'

else
	printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
	printf '\n->  Starting loading the firmware\n'
	cd ~/FC7/sw/fc7/tests
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
	./bin/fc7-d19c.exe  -i $IP -n  d19c_ssa_none_17052019.bin -f ~/MPA_Test/fw_bitfiles/d19c_ssa_none_17052019.bit

fi