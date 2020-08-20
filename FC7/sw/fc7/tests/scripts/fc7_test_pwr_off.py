from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
from time import sleep
import sys
import os
import visa
from fc7_lib import *

########################################
def tsx1820p_consumption(debug_str):
########################################
	#if debug_str=="debug": print "[info]: gpib|measure consumption"
	tsx1820p.write('VO?')
	vout = tsx1820p.read()
	if debug_str=="debug": print "[info]: gpib|voltage            ->",vout
	tsx1820p.write('IO?')
	iout = tsx1820p.read()
	if debug_str=="debug": print "[info]: gpib|current            ->",iout
	return 0

########################################
def tsx1820p_powerup(debug_str):
########################################
	if debug_str=="debug": print
	if debug_str=="debug": print "[info]: gpib|powering up ..."
	tsx1820p.write('OP 1')
	sleep(2)
	tsx1820p_consumption(debug_str)

########################################
def tsx1820p_powerdown(debug_str):
########################################
	if debug_str=="debug": print
	if debug_str=="debug": print "[info]: gpib|powering down ..."
	tsx1820p.write('OP 0')
	sleep(2)
	tsx1820p_consumption(debug_str)

########################################
def string_found_in_file(file,string):
########################################
	numline=0
	numfound=0
	for line in open(file,"r"):
		numline=numline+1
		#print line
		if line.find(string)> -1:
			numfound=numfound+1
	if numfound!=0: 
		found= True
	else:	
		found= False
#	print "string", string, "found", numfound,"times"
	return found


#########################
#########################
#########################
#########################
#########################
#########################
#########################
#########################
#########################


#########################
# console arguments
#########################
debug_str=""
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug_str="debug"

	
	
tsx1820p_powerdown(debug_str)

print
print "[TEST]: done"



