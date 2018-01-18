from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *

def SelectBoard(name): 
	global ipaddr
	global fc7AddrTable
	global fc7
	if name == 'mpa' or name == 'MPA' or name == 0:   
		f = open('./myScripts/ipaddr_mpa.dat', 'r')
		ipaddr = f.readline()
		f.close()
		print 'MPA Board Selected on IP address: ' + str(ipaddr)
	elif name == 'ssa' or name == 'SSA' or name == 1:   
		f = open('./myScripts/ipaddr_ssa.dat', 'r')
		ipaddr = f.readline()
		f.close()
		print 'SSA Board Selected on IP address: ' + str(ipaddr)
	fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
	fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
	return ipaddr, fc7AddrTable, fc7 