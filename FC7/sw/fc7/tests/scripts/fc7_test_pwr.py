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

#####################################################################
# set voltages
#####################################################################
os.system('fc7_i2c_voltage_set.py L8 p2v5 >> foo')
os.system('fc7_i2c_voltage_set.py L12 p2v5 >> foo')
os.system('fc7_fmc_pwr_on.py >> foo')



#####################################################################
# i2c expander status
#####################################################################
# enable
i2c_en    = 1
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)

i2c_slv   = 0x20
wr     = 1
rd     = 0
unused = 0x00

os.system('fc7_fmc_pwr_on.py >> foo')
i2c(i2c_slv, wr, unused , 0xff  , 0 , unused, 0    )
expander_status = i2c(i2c_slv, rd, unused , unused, 0,  0, 0)

# disable 
i2c_en    = 0
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)


#####################################################################
# i2c voltage monitoring
#####################################################################
# constants
RegBuffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RdxBuffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
LTC2990 = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

i2c_slv   = 0x4c
i2c_all   = 0x77
wr = 1
rd = 0
unused = 0x00

single = 1
repeat = 0
trig   = 0x01
# variables

acq = single

# enable i2c

i2c_en    = 1
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)
fc7.queueClear()

reg = 0x00
ctrl = (acq<<6)+0x1f # mode V1,V2,V3,V4 voltage measurements
################################################################
# global sync 
################################################################
#(slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
i2c(i2c_all, wr, 0x01   , ctrl  , 1     , unused, 0    )
#print
#print "-> set mode (single acq)"
#(slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
i2c(i2c_all, wr, 0x02   , trig  , 1     , unused, 0    )
#print
#print "-> trigger acquisition"
sleep(0.5)

for j in range (0,4):
	################################################################
	# get voltages
	################################################################
	#print
	for i in range(0,16):
		#                 (slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
		RdxBuffer[i] = i2c(i2c_slv+j, wr, unused , reg+i , unused, unused, 0    )
		RegBuffer[i] = i2c(i2c_slv+j, rd, unused , unused, unused, unused, 0    )
		
	LTC2990[5*j+0]  = ((RegBuffer[0x06] & 0x03f)	<< 8) + RegBuffer[0x07]
	LTC2990[5*j+1]  = ((RegBuffer[0x08] & 0x03f)	<< 8) + RegBuffer[0x09]
	LTC2990[5*j+2]  = ((RegBuffer[0x0a] & 0x03f)	<< 8) + RegBuffer[0x0b]
	LTC2990[5*j+3]  = ((RegBuffer[0x0c] & 0x03f)	<< 8) + RegBuffer[0x0d]
	LTC2990[5*j+4]  = ((RegBuffer[0x0e] & 0x03f)	<< 8) + RegBuffer[0x0f]

################################################################
# calculate (external dividers, Vcc)
################################################################

LTC2990[0] = 0.00030518 * LTC2990[0]*((4.7+4.7)/4.7)
LTC2990[1] = 0.00030518 * LTC2990[1]*((4.7+4.7)/4.7)
LTC2990[2] = 0.00030518 * LTC2990[2]*((4.7+4.7)/4.7)
LTC2990[3] = 0.00030518 * LTC2990[3]*((4.7+4.7)/4.7)
LTC2990[4] = 0.00030518 * LTC2990[4] + 2.5
#LTC2990[3] = 0

LTC2990[5] = 0.00030518 * LTC2990[5]*((4.7+1.18)/1.18)
LTC2990[6] = 0.00030518 * LTC2990[6]*((4.7+1.18)/1.18)
LTC2990[7] = 0.00030518 * LTC2990[7]
LTC2990[8] = 0.00030518 * LTC2990[8]
LTC2990[9] = 0.00030518 * LTC2990[9] + 2.5

LTC2990[10]= 0.00030518 * LTC2990[10]*((4.7+4.7)/4.7)
LTC2990[11]= 0.00030518 * LTC2990[11]*((4.7+4.7)/4.7)
LTC2990[12]= 0.00030518 * LTC2990[12]*((4.7+4.7)/4.7)
LTC2990[13]= 0.00030518 * LTC2990[13]*((4.7+4.7)/4.7)
LTC2990[14]= 0.00030518 * LTC2990[14] + 2.5
           
LTC2990[15]= 0.00030518 * LTC2990[15]*((4.7+1.18)/1.18)
LTC2990[16]= 0.00030518 * LTC2990[16]*((4.7+1.18)/1.18)
LTC2990[17]= 0.00030518 * LTC2990[17]
LTC2990[18]= 0.00030518 * LTC2990[18]
LTC2990[19]= 0.00030518 * LTC2990[19] + 2.5
#
#
i2c_en    = 0
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)



#################
# error checking
#################
err=0
tol = 0.05

if debug==1: print "[info]: pwr |l8_vadj            -> %.2fV" % (LTC2990[1])
if (LTC2990[1]< (2.5*(1-tol))): err=1
if (LTC2990[1]> (2.5*(1+tol))): err=1 

if debug==1: print "[info]: pwr |l8_vadj_sense      -> %.2fV" % (LTC2990[0])
if (LTC2990[0]< (2.5*(1-tol))): err=1
if (LTC2990[0]> (2.5*(1+tol))): err=1 

if debug==1: print "[info]: pwr |3v3                -> %.2fV" % (LTC2990[3])
if (LTC2990[3]< (3.3*(1-tol))): err=1 
if (LTC2990[3]> (3.3*(1+tol))): err=1 

if debug==1: print "[info]: pwr |3v3_sense_l8       -> %.2fV" % (LTC2990[2])
if (LTC2990[2] <(3.3*(1-tol))): err=1
if (LTC2990[2] >(3.3*(1+tol))): err=1 

if debug==1: print "[info]: pwr |12v                -> %.2fV" % (LTC2990[6])
if (LTC2990[6] < (12*(1-tol))): err=1
if (LTC2990[6] > (12*(1+tol))): err=1 

if debug==1: print "[info]: pwr |12v_sense_l8       -> %.2fV" % (LTC2990[5])
if (LTC2990[5] < (12*(1-tol))): err=1
if (LTC2990[5] > (12*(1+tol))): err=1 

if debug==1: print "[info]: pwr |l12_vadj           -> %.2fV" % (LTC2990[11])
if (LTC2990[11]<(2.5*(1-tol))): err=1
if (LTC2990[11]>(2.5*(1+tol))): err=1 

if debug==1: print "[info]: pwr |l12_vadj_sense     -> %.2fV" % (LTC2990[10])
if (LTC2990[10]<(2.5*(1-tol))): err=1
if (LTC2990[10]>(2.5*(1+tol))): err=1 

if debug==1: print "[info]: pwr |3v3                -> %.2fV" % (LTC2990[13])
if (LTC2990[13]<(3.3*(1-tol))): err=1 
if (LTC2990[13]>(3.3*(1+tol))): err=1 

if debug==1: print "[info]: pwr |3v3_sense_l12      -> %.2fV" % (LTC2990[12])
if (LTC2990[12]<(3.3*(1-tol))): err=1 
if (LTC2990[12]>(3.3*(1+tol))): err=1 

if debug==1: print "[info]: pwr |12v                -> %.2fV" % (LTC2990[16])
if (LTC2990[16]<(12*(1-tol))): err=1
if (LTC2990[16]>(12*(1+tol))): err=1 

if debug==1: print "[info]: pwr |12v_sense_l12      -> %.2fV" % (LTC2990[15])
if (LTC2990[15]<(12*(1-tol))): err=1
if (LTC2990[15]>(12*(1+tol))): err=1 


if debug==1: print "[info]: pwr |expander_status    ->", uInt8HexStr(expander_status)
if expander_status!=0xf0: err=1

l12_present = fc7.read("fmc_l12_present")
l12_pg_m2c  = fc7.read("fmc_l12_pg_m2c")
l8_present  = fc7.read("fmc_l8_present")
l8_pg_m2c   = fc7.read("fmc_l8_pg_m2c")

if debug==1: print "[info]: pwr |l8_present         ->",l8_present
if debug==1: print "[info]: pwr |l8_pg_m2c          ->",l8_pg_m2c
if debug==1: print "[info]: pwr |l12_present        ->",l12_present
if debug==1: print "[info]: pwr |l12_pg_m2c         ->",l12_pg_m2c

if (l12_present != 1) or (l12_pg_m2c!=1): err=1 
if (l8_present  != 1) or (l8_pg_m2c !=1): err=1 

###########
# VERDICT
###########
if (err==1):
	print "[TEST]: pwr |voltage monitoring -> /FAIL/"
else:
	print "[TEST]: pwr |voltage monitoring -> /PASS/"	