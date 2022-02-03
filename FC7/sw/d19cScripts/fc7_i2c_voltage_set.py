########################################
# library calls
########################################
from PyChipsUser import *
from time import sleep
from fc7_lib import *
#
import sys
args = sys.argv
arg_length = len(args)
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

# constants

i2c_slv   = 0x2f
wr = 1
rd = 0
unused = 0x00

sel_fmc_l8  = 0
sel_fmc_l12 = 1

p3v3 = 0xff - 0x09
p2v5 = 0xff - 0x2b
p1v8 = 0xff - 0x67

# variables



if arg_length == 3 	and (args[1]=="L8"   or args[1]=="L12") \
                    and (args[2]=="p3v3" or args[2]=="p2v5" or args[2]=="p1v8") :
		#
		if 	 args[1]=="L8" : rdac_sel = sel_fmc_l8
		elif args[1]=="L12": rdac_sel = sel_fmc_l12
		#
		if 	 args[2]=="p3v3" : voltage = p3v3
		elif args[2]=="p2v5" : voltage = p2v5
		elif args[2]=="p1v8" : voltage = p1v8

		# enable i2c
		i2c_en    = 1
		i2c_sel   = 0
		i2c_presc = 1000
		i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
		fc7.write("i2c_settings", i2c_settings_value)
		
		# set value
		instr = (rdac_sel<<7)+0x08 
		i2c(i2c_slv, wr, instr, voltage , 1 , unused, 0    )
		print "-> set",args[2],"to VADJ of",args[1]

		# disable i2c
		i2c_en    = 0
		i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
		fc7.write("i2c_settings", i2c_settings_value)

else:

	print
	print "-> Error!!! invalid arguments."
	print "-> "
	print "-> Syntax:"
	print "-> "
	print "-> fc7_i2c_set_voltage.py <L8|L12> <p3v3|p2v5|p1v8>"
	print "-> "	
















# import sys
# args = sys.argv
# arg_length = len(args)

# if arg_length == 3: # script name + two parameters	
# else:

	# print
	# print "-> Error!!! arguments are required."
	# print "-> "
	# print "-> Syntax:"
	# print "-> "
	# print "-> fc7_i2c_set_voltage.py <L8|L12> <p3v3|p2v5|p1v8>"
	# print "-> "	