from PyChipsUser import *
import sys
import os
from time import sleep

fc7AddrTable = AddressTable("./fc7AddrTable.dat")

########################################
# IP address
########################################
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
print
print "--=======================================--"
print "  Opening fc7 with IP", ipaddr
print "--=======================================--"
print

########################
#clk160, Vadj=2.5V
########################
#   0deg -> 3b
#  60deg -> 7e
# 120deg -> c0
# 180deg -> c0
# 240deg -> c0
# 300deg -> 7e



#os.system('c:\python27\python fc7_cdce_powerup_and_sync.py')
#sleep (0.1)

clk_sel = 0 # 160MHz
#clk_sel = 1 # 240MHz

fc7.write("phase_mon_auto",   0) 		# disable the auto-triggering of the phase monitoring when cdce loses its lock

fc7.write("cdce_xpoint_out2", 1) 		# configure xpoint switch to select CDCE u1
fc7.write("cdce_xpoint_out3", 1) 		# configure xpoint switch to select CDCE u1
fc7.write("cdce_xpoint_out4", 1) 		# configure xpoint switch to select CDCE u1

if clk_sel == 1:
	fc7.write("phase_mon_refclk_sel", 1) 	# select 240Mhz refclk generation inside the FPGA
#R0 fc7.write("phase_mon_lower", 0x8E)		# lower limit (for CDCE u1 default settings: 240MHz 0deg)
#R0	fc7.write("phase_mon_upper", 0x9E)		# upper limit (for CDCE u1 default settings: 240MHz 0deg)
#R1
#R1
else:
	fc7.write("phase_mon_refclk_sel", 0) 	# select 160Mhz refclk generation inside the FPGA
#R0	fc7.write("phase_mon_lower", 0xdc)		# lower limit (for CDCE u1 default settings: 160MHz 0deg)
#R0	fc7.write("phase_mon_upper", 0xfc)		# upper limit (for CDCE u1 default settings: 160MHz 0deg)
	fc7.write("phase_mon_lower", 0x08)		# lower limit (for CDCE u1 default settings: 160MHz 0deg)
	fc7.write("phase_mon_upper", 0x20)		# upper limit (for CDCE u1 default settings: 160MHz 0deg)

fc7.write("phase_mon_strobe", 1)
fc7.write("phase_mon_strobe", 0)

os.system('c:\python27\python fc7_cdce_status.py')
