source ~/FC7/sw/fc7/setup.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

if [ $# -eq 0 ]
	then
		echo "No wafer name provided."
		exit 1
fi

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

echo ""
echo "from d19cScripts import *"    >  LaunchPy.py
echo "from myScripts import *"      >> LaunchPy.py
echo "from ssa_methods import *"    >> LaunchPy.py
echo "AP = AUTOPROBER('$1', 'N' , 'SSA')"  >> LaunchPy.py
echo "AP.MSR_ALL(90)"             >> LaunchPy.py

cp ./utilities/ipaddr_ssa.dat  d19cScripts/ipaddr.dat

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

ping -c 1 -W 1 $IP; rep=$?

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
	printf '\n->  SSA Testbench correctly found on %s\n' "$IP"
	python -i LaunchPy.py
fi
