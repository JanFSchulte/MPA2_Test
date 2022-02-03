########################################
# imports
########################################
from PyChipsUser import *
from time import sleep
########################################
# fc7 configuration
########################################
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
########################################



#######################################
# main
#######################################

# constants

on  = 1
off = 0

# variables

state = off 

# process

fc7.write("fmc_pg_c2m"    , state) 
fc7.write("fmc_l12_pwr_en", state)
fc7.write("fmc_l8_pwr_en" , state)
print
print "-> fmc_pg_c2m     ->", state
print "-> fmc_L12_pwr_en ->", state
print "-> fmc_L8_pwr_en  ->", state
print
