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

cdce_clk_source = fc7.read("cdce_refsel")
if cdce_clk_source == 1:
	cdce_clk = "primary"
else:
	cdce_clk = "secondary"
	


phase_mon_refclk_sel  = fc7.read("phase_mon_refclk_sel")
if   (phase_mon_refclk_sel == 1): print "-> phase_mon_clock: 240MHz"
elif (phase_mon_refclk_sel == 0): print "-> phase_mon_clock: 160MHz"

print "-> cdce sync busy :", fc7.read("cdce_sync_busy")
print "-> cdce sync done :", fc7.read("cdce_sync_done")

locked_cnt = 0
for i in range (0, 1000):
	lock = fc7.read("cdce_lock")
	if (lock==1): locked_cnt = locked_cnt + 1

print "-> cdce clk source:", cdce_clk
print "-> cdce locked    :", locked_cnt,"of 1000"
print "-> phase_mon_done :", fc7.read("phase_mon_done")
print "-> phase_mon_upper:", uInt8HexStr(fc7.read("phase_mon_upper"))
print "-> phase_mon_count:", uInt8HexStr(fc7.read("phase_mon_count"))
print "-> phase_mon_lower:", uInt8HexStr(fc7.read("phase_mon_lower"))
print "-> phase_mon_ok   :", fc7.read("phase_mon_ok")
