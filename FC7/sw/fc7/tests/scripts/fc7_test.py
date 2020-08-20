from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
import time
from time import sleep
import datetime
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


pwr_ctrl = 0

#########################
# console arguments
#########################
debug_str=""
prog=0
brd_id=""
brd_nbr = 0
brd_nbr_offset = 128 # for fc7_r1

arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug_str="debug"
	if sys.argv[1]=="prog" : prog=1
	if sys.argv[1].isdigit()==True and sys.argv[1].startswith("1") and len(sys.argv[1])==9: 
		brd_id=sys.argv[1]
		brd_nbr=int(sys.argv[1][7:]) +brd_nbr_offset

if (arguments>2):
	if sys.argv[2]=="debug": debug_str="debug"
	if sys.argv[2]=="prog": prog=1
	if sys.argv[2].isdigit()==True and sys.argv[2].startswith("1") and len(sys.argv[2])==9:
		brd_id=sys.argv[2]
		brd_nbr=int(sys.argv[2][7:]) +brd_nbr_offset
	
if (arguments>3):
	if sys.argv[3]=="debug": debug_str="debug"
	if sys.argv[3]=="prog": prog=1
	if sys.argv[3].isdigit()==True and sys.argv[3].startswith("1") and len(sys.argv[3])==9:
		brd_id=sys.argv[3]
		brd_nbr=int(sys.argv[3][7:]) +brd_nbr_offset

		
#########################
# test details
#########################
print ("[TEST]: info|manufacturer id    -> %s" % brd_id)
date_time = datetime.datetime.now()
print ("[TEST]: info|current date/time  -> %s" % date_time)
sys.stdout.flush()

#date_time = datetime.datetime.now()
#if debug_str=="debug": print
#if debug_str=="debug": print ("[info]: date|current date/time  -> %s" % date_time)
#if debug_str=="debug": sys.stdout.flush()
		
#########################
# identify
#########################
tsx1820p = visa.instrument('GPIB0::1::INSTR')
tsx1820p.write('*IDN?')
id = tsx1820p.read()
if debug_str=="debug": print	
if debug_str=="debug": print "[info]: gpib|ps device id       ->",id
if debug_str=="debug": sys.stdout.flush()

if pwr_ctrl==1: 		
	#########################
	# configure
	#########################
	tsx1820p.write('*RST')
	tsx1820p.write('V 12.00; I 3.00; OVP 0.00; DAMPING 0')

	#########################
	# verify settings
	#########################
	tsx1820p.write('V?')
	vset = tsx1820p.read()
	if debug_str=="debug": print "[info]: gpib|voltage set to     ->",vset
	if debug_str=="debug": sys.stdout.flush()
	#
	tsx1820p.write('I?')
	iset = tsx1820p.read()
	if debug_str=="debug": print "[info]: gpib|current set to     -> ",iset
	if debug_str=="debug": sys.stdout.flush()

	#########################
	# power up
	#########################
	tsx1820p_powerup(debug_str)

#########################
# program cpld
#########################
if prog==1:
	#
	cpld_prog_succesful = False
	cable_failure = False
	print
	if debug_str=="debug": print "[info]: prog|cpld programming ..."
	sys.stdout.flush()
	os.system('d:\cpld_prog.bat > d:\cpld_prog.txt 2>&1')
	cpld_prog_succesful = string_found_in_file("d:\cpld_prog.txt","Programming completed successfully")
	cable_failure = string_found_in_file("d:\cpld_prog.txt","Cable connection failed")
	if cpld_prog_succesful==True: 
		print "[TEST]: prog|cpld programming   -> /PASS/"
		sys.stdout.flush()
	else:
		print "[TEST]: prog|cpld programming   -> /FAIL/"
		if cable_failure==True: print "[info]: prog|cpld cable failure"
		sys.stdout.flush()
#		sys.exit()
		
#########################
# program mmc
#########################
if prog==1 and cpld_prog_succesful==True:
	#
	mmc_prog_succesful = False
	if debug_str=="debug": print
	if debug_str=="debug": print "[info]: prog|mmc  programming ..."
	if debug_str=="debug": sys.stdout.flush()
	os.system('d:\mmc_prog.bat > d:\mmc_prog.txt 2>&1')
	mmc_prog_succesful = string_found_in_file("d:\mmc_prog.txt","Programming completed successfully")
	if mmc_prog_succesful==True: 
		print "[TEST]: prog|mmc  programming   -> /PASS/"
		sys.stdout.flush()
	else:
		print "[TEST]: prog|mmc  programming   -> /FAIL/"
		sys.stdout.flush()
#		sys.exit()

	#########################
	# powercycle
	#########################
	if debug_str=="debug": print
	if debug_str=="debug": sys.stdout.flush()
	tsx1820p_consumption(debug_str)
	tsx1820p_powerdown(debug_str)
	tsx1820p_powerup(debug_str)
	
#########################
# FPGA tests
#########################
ethernet_up = False
#
if ((prog==0) or ((prog==1) and (cpld_prog_succesful==True) and (mmc_prog_succesful==True))):
	print
	if debug_str=="debug": print "[info]: fpga|ethernet test ..."
	if debug_str=="debug": sys.stdout.flush()
	sleep(10)
	os.system('ping 192.168.0.80 > d:\ping_results.txt 2>&1')
	ethernet_up = string_found_in_file("d:\ping_results.txt","Reply from 192.168.0.80: bytes=32 time<1ms")

	if ethernet_up==False:
		print "[TEST]: fpga|ethernet test      -> /FAIL/"
		sys.stdout.flush()
	else:
		print "[TEST]: fpga|ethernet test      -> /PASS/"
		print "[TEST]: fpga|sd loading test    -> /PASS/"
		sys.stdout.flush()

#########################
# run tests
#########################
if ((ethernet_up==True) and ((prog==0) or ((prog==1) and (cpld_prog_succesful==True) and (mmc_prog_succesful==True)))):
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()
	os.system((' '.join(['fc7_test_id.py', debug_str])))
	if brd_nbr!=0: 
		if debug_str=="debug": print "[info]: id  |manufacturer id    ->", brd_id
		if debug_str=="debug": sys.stdout.flush()
		os.system((' '.join(['fc7_i2c_mac_ip_eeprom.py wr', str(brd_nbr), debug_str])))
	
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()
	os.system((' '.join(['fc7_test_pwr.py', debug_str])))
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()
	os.system((' '.join(['fc7_test_cdce.py', debug_str])))
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()
	sleep(2)
	os.system((' '.join(['fc7_test_ddr3.py', debug_str])))
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()
	sleep(2)
	os.system((' '.join(['fc7_test_io.py', debug_str])))
	tsx1820p_consumption(debug_str)
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()
	
	#########################
	# increase current for gtx test
	#########################
	tsx1820p.write('V 12.00; I 4.00; OVP 0.00; DAMPING 0')
	tsx1820p.write('V?')
	vset = tsx1820p.read()
	if debug_str=="debug": print "[info]: gpib|voltage set to     ->",vset
	if debug_str=="debug": sys.stdout.flush()
	tsx1820p.write('I?')
	iset = tsx1820p.read()
	if debug_str=="debug": print "[info]: gpib|current set to     -> ",iset
	if debug_str=="debug": sys.stdout.flush()
	#########################


	os.system((' '.join(['fc7_test_gtx_enable.py', debug_str])))
	os.system((' '.join(['fc7_test_gtx_ber.py', debug_str])))
	tsx1820p_consumption(debug_str)
	os.system((' '.join(['fc7_test_gtx_disable.py', debug_str])))
	tsx1820p_consumption(debug_str)
	
	sleep(2)
	os.system((' '.join(['fc7_test_usrclk.py', debug_str])))
	if debug_str=="debug": print	
	if debug_str=="debug": sys.stdout.flush()


if pwr_ctrl==1: 		
	tsx1820p_powerdown(debug_str)

print
print "[TEST]: done"
sys.stdout.flush()
