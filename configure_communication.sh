#!/bin/sh

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

cp ./utilities/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

sudo /usr/sbin/rarpd -a
sudo ifconfig ${eth}:1 192.168.0.100
sudo udevadm control --reload-rules
sudo modprobe ni_usb_gpib
ping -c 1 -W 1 $IP; rep=$?
if ! (( $rep == 0 )); then
	printf   '\n->  SSA Testbench unrichable\n'
else
	printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
	$start_tb
fi
printf '______________________________________________________\n'
