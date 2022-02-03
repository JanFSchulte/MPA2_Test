from PyChipsUser import *
from time import sleep
import sys
import os
########################################
# init
########################################
fc7addrtable = AddressTable("./fc7addrtable.dat")
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7addrtable, ipaddr, 50001)
########################################

fc7.write("ctrl", 0xff7fffd8) # restore default settings

debug_str=""
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug_str="debug"

#########################################
if debug_str=="debug": print "[info]: cdce|spi wr"
if debug_str=="debug": sys.stdout.flush()
#########################################
spi_comm = 0x8fa38014;

wrbuffer = [0,1,2,3,4,5,6,7,8,0]
wrbuffer[0] = 0xeb840320 # reg0 (out0=240mhz,lvds, phase shift  0deg)
wrbuffer[1] = 0xeb020321 # reg1 (out1=160mhz,lvds, phase shift  0deg)
#wrbuffer[2] = 0xeb020302 # reg2 (out2=240mhz,lvds  phase shift  0deg)
wrbuffer[2] = 0xeb840302 # reg2 (out2=240mhz,lvds  phase shift  0deg)
wrbuffer[3] = 0xeb840303 # reg3 (out3=240mhz,lvds, phase shift  0deg)
wrbuffer[4] = 0xeb140334 # reg4 (out4= 40mhz,lvds, phase shift  0deg, r4.1=1)
wrbuffer[5] = 0x113c0cf5 # reg5 (3.4ns lockw,lvds in, dc term, prim ref enable, sec ref enable, smartmux off, failsafe off etc.)
wrbuffer[6] = 0x33041be6 # reg6 (vco1, ps=4, fd=12, fb=1, chargepump 50ua, internal filter, r6.20=0, auxout= enable; auxout= out2)
wrbuffer[7] = 0xbd800df7 # reg7 (c2=473.5pf, r2=98.6kr, c1=0pf, c3=0pf, r3=5kr etc, sel_del2=1, sel_del1=1)
#wrbuffer[8] = 0x20009978 # reg8 (various)};

rdbuffer = [0,1,2,3,4,5,6,7,8,0]
rdcombuf = [0xe,0x1e,0x2e,0x3e,0x4e,0x5e,0x6e,0x7e,0x8e] 

#
for i in range(0,8):
	fc7.write("spi_txdata",wrbuffer[i])
	#print " writing",uint32hexstr(wrbuffer[i]), "to register",'%02d' % i
	fc7.write("spi_command", spi_comm)
	fc7.read("spi_rxdata") # dummy read
	fc7.read("spi_rxdata") # dummy read

#########################################
if debug_str=="debug": print "[info]: cdce|spi rd"
if debug_str=="debug": sys.stdout.flush()
#########################################
for i in range(0,9):
	fc7.write("spi_txdata",rdcombuf[i])
	fc7.write("spi_command", spi_comm)
	fc7.write("spi_txdata",0xaaaaaaaa) # dummy write
	fc7.write("spi_command", spi_comm);
	rdbuffer[i] = fc7.read("spi_rxdata")
	#print " register",'%02d' % i,"contents =",uint32hexstr(rdbuffer[i])

#########################################
#print "[test]: cdce|spi"
#########################################
if (rdbuffer[0:8]==wrbuffer[0:8]):
	print "[TEST]: cdce|spi                -> /PASS/"
	sys.stdout.flush()
else:
	print "[TEST]: cdce|spi                -> /FAIL/"
	sys.stdout.flush()

#########################################
if debug_str=="debug": print "[info]: cdce|copy to eeprom"
#########################################
os.system('fc7_cdce_copy_to_eeprom.py >> foo')

#########################################
if debug_str=="debug": print "[info]: cdce|powercycle"
#########################################
os.system('fc7_cdce_powerup_and_sync.py >> foo')

#########################################
if debug_str=="debug": print "[info]: cdce|spi rd"
#########################################
for i in range(0,9):
	fc7.write("spi_txdata",rdcombuf[i])
	fc7.write("spi_command", spi_comm)
	fc7.write("spi_txdata",0xaaaaaaaa) # dummy write
	fc7.write("spi_command", spi_comm);
	rdbuffer[i] = fc7.read("spi_rxdata")
	#print " register",'%02d' % i,"contents =",uint32hexstr(rdbuffer[i])

#########################################
#print \n "[test]: cdce|eeprom"
#########################################
if (rdbuffer[0:8]==wrbuffer[0:8]):
	print "[TEST]: cdce|eeprom             -> /PASS/"
else:
	print "[TEST]: cdce|eeprom             -> /FAIL/"

if debug_str=="debug": print "[info]: cdce|status reg         ->" , uInt32HexStr(rdbuffer[8])
if debug_str=="debug": sys.stdout.flush()
#########################################
os.system((' '.join(['fc7_cdce_phase_scan.py', debug_str])))
#########################################