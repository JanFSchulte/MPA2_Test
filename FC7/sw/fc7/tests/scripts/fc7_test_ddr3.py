import os
import sys
from PyChipsUser import *
from time import sleep
from fc7_lib import *

# Read in an address table by creating an AddressTable object (Note the forward slashes, not backslashes!)
fc7AddrTable = AddressTable('./fc7AddrTable.dat')

f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)


debug=0
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug=1

# reset
fc7.write("user_ipb_ctrl_regs", 0x00, 0)
fc7.write("user_ipb_ctrl_regs", 0x01, 0)
sleep(0.5)


ddr3_status = fc7.read("user_ipb_stat_regs", 1)
ddr3_init_done = ddr3_status & 0x01
if debug==1: print "[info]: ddr3|init status        ->",ddr3_init_done

if ddr3_init_done==1:
	# start bist
	fc7.write("user_ipb_ctrl_regs", 0x11)
	fc7.write("user_ipb_ctrl_regs", 0x01)
	#
	ddr3_status = fc7.read("user_ipb_stat_regs", 1)
	bist_done = ddr3_status >> 8
	if debug==1: print "[info]: ddr3|bist completed     ->",bist_done
	#
	sleep(3)
	#
	ddr3_status = fc7.read("user_ipb_stat_regs", 1)
	bist_done = ddr3_status >> 8
	if debug==1: print "[info]: ddr3|bist completed     ->",bist_done
	#
	nb_of_err = fc7.read("user_ipb_stat_regs", 3)
	if debug==1: print "[info]: ddr3|bist nbr of errors ->",nb_of_err
	#
	nb_of_wrd = fc7.read("user_ipb_stat_regs", 8)
	if debug==1: print "[info]: ddr3|bist nbr of words  ->",nb_of_wrd

	if bist_done==1 and nb_of_err==0: 
		print "[TEST]: ddr3|bist               -> /PASS/"
	else:
		print "[TEST]: ddr3|bist               -> /FAIL/"

else:
	print "[TEST]: ddr3|bist               -> /FAIL/"
		
		
#########################################
# IPbus accesses
#########################################

offset	= 0
entries	= 8192 # of 128 bits each

################
# counter 
################
wrBuffer = []
for i in range(0, entries*8):
	wrBuffer.append(0xdcba0000+i) 

wren = 1
if wren==1: 
	fc7.blockWrite("user_ddr3", wrBuffer, offset)

rdBuffer= []
rdBuffer  = fc7.blockRead("user_ddr3", (entries*8), offset)

printout=0
if (printout==1):
	print
	for i in range (0,entries):
		print uInt32HexStr(rdBuffer[8*i+7]),\
			uInt32HexStr(rdBuffer[8*i+6]),\
			uInt32HexStr(rdBuffer[8*i+5]),\
			uInt32HexStr(rdBuffer[8*i+4]),\
			uInt32HexStr(rdBuffer[8*i+3]),\
			uInt32HexStr(rdBuffer[8*i+2]),\
			uInt32HexStr(rdBuffer[8*i+1]),\
			uInt32HexStr(rdBuffer[8*i+0])

################
# marching ones
################
wrBuffer2 = []
for i in range(0, entries*8):
	i_5bit = i & 0x1f
	wrBuffer2.append(2**i_5bit) 

wren = 1
if wren==1: 
	fc7.blockWrite("user_ddr3", wrBuffer2, offset)

rdBuffer2= []
rdBuffer2  = fc7.blockRead("user_ddr3", (entries*8), offset)

printout=0
if (printout==1):
	print
	for i in range (0,entries):
		print uInt32HexStr(rdBuffer2[8*i+7]),\
			uInt32HexStr(rdBuffer2[8*i+6]),\
			uInt32HexStr(rdBuffer2[8*i+5]),\
			uInt32HexStr(rdBuffer2[8*i+4]),\
			uInt32HexStr(rdBuffer2[8*i+3]),\
			uInt32HexStr(rdBuffer2[8*i+2]),\
			uInt32HexStr(rdBuffer2[8*i+1]),\
			uInt32HexStr(rdBuffer2[8*i+0])

# test the comparison
#wrBuffer[4]=0
if (rdBuffer!=wrBuffer or rdBuffer2 != wrBuffer2 ):	
	print "[TEST]: ddr3|ipbus access test  -> /FAIL/"
else: 
	print "[TEST]: ddr3|ipbus access test  -> /PASS/"