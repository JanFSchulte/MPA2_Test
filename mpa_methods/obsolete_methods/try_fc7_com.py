import time
from PyChipsUser import *

print("---------------------------------------")

fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTableSeuCorrect.dat")
fc7 = ChipsBusUdp(fc7AddrTable, '192.168.0.79' , 50001)

for i in range(4):
	fc7.write("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq", i)
	time.sleep(0.001)
	r = fc7.read("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq")
	time.sleep(0.001)
	if(r == i): st = 'Pass'
	else: st = 'Fail'
	print('{:s}: {:d}-{:d}'.format(st, i, r))

print("---------------------------------------")

def comconfig(name):
	global ipaddr
	global fc7AddrTable
	global fc7
	f = open('./utilities/ipaddr_ssa.dat', 'r')
	ipaddr = f.readline()
	ipaddr = ipaddr.replace('\n', '')
	ipaddr = ipaddr.replace(' ' , '')
	f.close()
	print('SSA Board Selected on IP address: [' + str(ipaddr) + ']' )
	fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
	fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
	return ipaddr, fc7AddrTable, fc7

ipaddr, fc7AddrTable, fc7  = comconfig('ssa')

for i in range(4):
	fc7.write("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq", i)
	time.sleep(0.001)
	r = fc7.read("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq")
	time.sleep(0.001)
	if(r == i): st = 'Pass'
	else: st = 'Fail'
	print('{:s}: {:d}-{:d}'.format(st, i, r))

print("---------------------------------------")
