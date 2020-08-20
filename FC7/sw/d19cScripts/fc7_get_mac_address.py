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

########################################
# main
########################################
i2c_en    = 1
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)


i2c_slv   = 0x50
reg_addr  = 0x00
reg	  = 0x00
wr     = 1
rd     = 0
unused = 0x00

st = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
dt = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
for i in range(0,16):
	st[i] = i2c(i2c_slv, wr, unused , reg+i,  0,  0, 0)
	dt[i] = i2c(i2c_slv, rd, unused , unused, 0,  0, 0)
	sleep(0.05)
		
mac_addr = ':'.join([uInt8HexStr(dt[1]),uInt8HexStr(dt[2]),uInt8HexStr(dt[3]),uInt8HexStr(dt[4]),uInt8HexStr(dt[5]),uInt8HexStr(dt[6])])	

print "Current MAC address: ", mac_addr
