from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
from time import sleep
import sys
import os
from fc7_lib import *

########################################
# IP address
########################################
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
########################################

debug=0
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug=1
#

fc7.write("gtx_bert_reset", 1, 0)
fc7.write("gtx_bert_reset", 0, 0)

fc7.write("fmc_l8_gtx_reset",  0x00000000)		# assert rst for gtx of fmc l8 (2bits per channel) 		  
fc7.write("fmc_l12_gtx_reset", 0x00000000)		# assert rst for gtx of fmc l12(2bits per channel)
fc7.write("amc_gtx_reset",     0x00000000)		# assert rst for gtx of amc    (2bits per channel)

sleep(0.5)

fc7.write("fmc_l8_gtx_pd",  0x00000000)			# pwrdown gtx of fmc l8 (2bits per channel) 		  
fc7.write("fmc_l12_gtx_pd", 0x00000000)			# pwrdown gtx of fmc l12(2bits per channel) 
fc7.write("amc_gtx_pd",     0x00000000)			# pwrdown gtx of amc    (2bits per channel) 

sleep(0.5)

fc7.write("gtx_pll_pd", 0x00000000) 			# pwrdown plls 		  

sleep(0.5)

fmc_l8_ready  = fc7.read("ready_fmcL8_gtx")		# check gtx of fmc l8 (2bits per channel)
fmc_l12_ready = fc7.read("ready_fmcL12_gtx")	# check gtx of fmc l12(2bits per channel)
amc_ready     = fc7.read("ready_amc_gtx")		# check gtx of amc    (2bits per channel)

if debug==1: print
if debug==1: print "[info]: gtx |disabling ..."
if debug==1: print
