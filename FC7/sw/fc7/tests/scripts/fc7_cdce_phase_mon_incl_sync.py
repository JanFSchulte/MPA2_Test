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

os.system('c:\python27\python fc7_cdce_powerup_and_sync.py')
os.system('c:\python27\python fc7_cdce_phase_mon.py')
