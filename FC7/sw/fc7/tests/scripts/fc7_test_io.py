from PyChipsUser import *
import sys
import os
from time import sleep
from fc7_lib import *

def int2bin(n, count=24):
	return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])



# Read in an address table by creating an AddressTable object (Note the forward slashes, not backslashes!)
fc7AddrTable = AddressTable('./fc7AddrTable.dat')

f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)

#
debug=0
amc=0 #for p[15:12]
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug=1
if (arguments>2):
	if sys.argv[2]=="amc": amc=1
#


if debug==1: print "[info]: lpbk|std io test ..."
fc7.write("io_test_trigger", 1, 0)                                                  
fc7.write("io_test_trigger", 0, 0)                                                  

fmcL8_p_user_io_errors   = fc7.read("fmcL8_p_user_io_err")
fmcL8_p_user_io_correct  = fc7.read("fmcL8_p_user_io_corr")
if debug==1: print "[info]: lpbk|fmcL8P  errors     ->", int2bin(fmcL8_p_user_io_errors,17)

fmcL8_n_user_io_errors   = fc7.read("fmcL8_n_user_io_err")
fmcL8_n_user_io_correct  = fc7.read("fmcL8_n_user_io_corr")
if debug==1: print "[info]: lpbk|fmcL8N  errors     ->", int2bin(fmcL8_n_user_io_errors,17)

l8_err=0
if fmcL8_p_user_io_correct==0: l8_err=1
if fmcL8_n_user_io_correct==0: l8_err=1
if (l8_err==1):
	print "[TEST]: lpbk|std io test fmcL8  -> /FAIL/"
else:
	print "[TEST]: lpbk|std io test fmcL8  -> /PASS/"	


fmcL12_p_user_io_errors  = fc7.read("fmcL12_p_user_io_err")
fmcL12_p_user_io_correct = fc7.read("fmcL12_p_user_io_corr")
if debug==1: print "[info]: lpbk|fmcL12P errors     ->", int2bin(fmcL12_p_user_io_errors,17)

fmcL12_n_user_io_errors  = fc7.read("fmcL12_n_user_io_err")
fmcL12_n_user_io_correct = fc7.read("fmcL12_n_user_io_corr")
if debug==1: print "[info]: lpbk|fmcL12N errors     ->", int2bin(fmcL12_n_user_io_errors,17)

l12_err=0
if fmcL12_p_user_io_correct==0: l12_err=1
if fmcL12_n_user_io_correct==0: l12_err=1
if (l12_err==1):
	print "[TEST]: lpbk|std io test fmcL12 -> /FAIL/"
else:
	print "[TEST]: lpbk|std io test fmcL12 -> /PASS/"	

#############################
# when amc breakout is used
#############################
if amc==1:
	amc_p_user_io_errors  	 = fc7.read("amc_p_user_io_err")
	amc_p_user_io_correct    = fc7.read("amc_p_user_io_corr")
	if debug==1: print "[info]: lpbk|amcP errors        ->", int2bin(amc_p_user_io_errors,4)

	amc_n_user_io_errors  	 = fc7.read("amc_n_user_io_err")
	amc_n_user_io_correct    = fc7.read("amc_n_user_io_corr")
	if debug==1: print "[info]: lpbk|amcN errors        ->", int2bin(amc_n_user_io_errors,4)

	amc_stdio_err=0
	if amc_p_user_io_correct==0: amc_stdio_err=1
	if amc_n_user_io_correct==0: amc_stdio_err=1

	if (amc_stdio_err==1):
		print "[TEST]: lpbk|std io test amc    -> /FAIL/"
	else:
		print "[TEST]: lpbk|std io test amc    -> /PASS/"	

#############################
# when EDA-02432-V3 is used		
#############################

amc_p3=1
if amc_p3==1:
	p3_err = 0
	offset = 5
	for i in range(0,4):
		fc7.write("user_ipb_ctrl_regs", i ,offset)
		p3_status = fc7.read("user_ipb_stat_regs",offset)
		if p3_status!=i: p3_err=1

	if (p3_err==1):
		print "[TEST]: lpbk|std io test amc p3 -> /FAIL/"
	else:
		print "[TEST]: lpbk|std io test amc p3 -> /PASS/"	
#####	
if debug==1: print

