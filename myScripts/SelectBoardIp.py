from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *

def SelectBoard(name):
	global ipaddr
	global fc7AddrTable
	global fc7
	if name == 'mpa' or name == 'MPA' or name == 0:
		f = open('./utilities/ipaddr_mpa.dat', 'r')
		ipaddr = f.readline()
		f.close()
	elif name == 'ssa' or name == 'SSA' or name == 1:
		f = open('./utilities/ipaddr_ssa.dat', 'r')
		ipaddr = f.readline()
		f.close()
	ipaddr = ipaddr.replace('\n', '')
	ipaddr = ipaddr.replace('\t', '')
	ipaddr = ipaddr.replace(' ' , '')
	fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
	fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
	print('->  Board Selected on IP address: [' + str(ipaddr) + ']')
	return ipaddr, fc7AddrTable, fc7
