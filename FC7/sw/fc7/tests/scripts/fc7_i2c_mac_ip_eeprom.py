########################################
# library calls
########################################
import sys
from PyChipsUser import *
from time import sleep
from fc7_lib import *
########################################


########################################
# define fc7 object
########################################
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
########################################




wren=0
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="wr": wren=1

brd_nbr=0
if (arguments>2):
	brd_nbr=int(sys.argv[2])

debug_str = ""	
if (arguments>3):
	if sys.argv[3]=="debug": debug_str="debug"


########################################
# main
########################################
load_nothing  = 0
load_mac_ip   = 3
load_mac_only = 1
load_ip_only  = 2
st = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
dt = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

mac = [0x08,0x00,0x30,0x00,0x22,0x0b]
if brd_nbr!=0: mac[5]=brd_nbr

ip =  [0,0,0,0]
mode = load_mac_only
IpMacAddrBuffer =  [0xf5,mac[0],mac[1],mac[2],mac[3],mac[4],mac[5],ip[0],ip[1],ip[2],ip[3],mode,0x00,0x00,0x00,0x00]

i2c_en    = 1
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)


i2c_str   = 1
i2c_m16   = 0
i2c_slv   = 0x50
reg_addr  = 0x00


wr     = 1
rd     = 0
unused = 0x00
reg    = 0x00

if wren==1:
	for i in range(0,16):
		#  (slvaddr,r/w, regaddr, wrdata,             m, 16b, debug)
		i2c(i2c_slv, wr, reg+i  , IpMacAddrBuffer[i], 1,   0, 0)
		sleep(0.05)

rden = 1
if rden==1:
	for i in range(0,16):
		#                 (slvaddr,r/w, regaddr, wrdata, m,16b, debug)
		st[i] = i2c(i2c_slv, wr, unused , reg+i,  0,  0, 0)
		dt[i] = i2c(i2c_slv, rd, unused , unused, 0,  0, 0)
		sleep(0.05)
#		print uInt32HexStr(dt[i])
		
mac_addr = ':'.join([uInt8HexStr(dt[1]),uInt8HexStr(dt[2]),uInt8HexStr(dt[3]),uInt8HexStr(dt[4]),uInt8HexStr(dt[5]),uInt8HexStr(dt[6])])	
ip_addr  = '.'.join([str(dt[7]), str(dt[8]), str(dt[9]), str(dt[10])])	

if IpMacAddrBuffer==dt:		
	if debug_str=="debug": print "[info]: id  |mac address set to ->",mac_addr
	print "[TEST]: id  |mac address config -> /PASS/"
else:
	print "[TEST]: id  |mac address config -> /FAIL/"

	
i2c_en    = 0
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)
