from utilities.fc7_uhal import fc7_interface
from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
from utilities.tbsettings import *
import uhal 

def configure_communication():
	global ipaddr
	global fc7AddrTable
	global fc7

	ipaddr = tbconfig.ETHERS[tbconfig.BOARD_SELECT]['IP']
	fc7AddrTable = AddressTable("./utilities/fc7AddrTable.dat")
	ipaddr = ipaddr.replace('\n', '')
	ipaddr = ipaddr.replace('\t', '')
	ipaddr = ipaddr.replace(' ' , '')
	# UDP Connection
	#fc7 = fc7_interface("fc7", "ipbusudp-2.0://"+ipaddr+":50001", "file://utilities/uDTC_OT_address_table_v2.xml")
	# TCP with ControlHub
	fc7 = fc7_interface("fc7", "chtcp-2.0://localhost:10203?target="+ipaddr+":50001", "file://utilities/uDTC_OT_address_table_v2.xml") 


	print('->  Board Selected MAC > {:s} IP > {:s}'.format(tbconfig.BOARD_SELECT, ipaddr))
	
	return ipaddr, fc7AddrTable, fc7

#def SelectBoard(name):
#	global ipaddr
#	global fc7AddrTable
#	global fc7
#	if name == 'mpa' or name == 'MPA' or name == 0:
#		f = open('./utilities/ipaddr_mpa.dat', 'r')
#		ipaddr = f.readline()
#		f.close()
#	elif name == 'ssa' or name == 'SSA' or name == 1:
#		f = open('./utilities/ipaddr_ssa.dat', 'r')
#		ipaddr = f.readline()
#		f.close()
#	ipaddr = ipaddr.replace('\n', '')
#	ipaddr = ipaddr.replace('\t', '')
#	ipaddr = ipaddr.replace(' ' , '')
#	fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
#	fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
#	print('->  Board Selected on IP address: [' + str(ipaddr) + ']')
#	return ipaddr, fc7AddrTable, fc7
