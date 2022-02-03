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
#chipsLog.setLevel(logging.DEBUG)    # Verbose logging (see packets being sent and received)

debug=0
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug=1

########################################
########################################
########################################
########################################
########################################
########################################
########################################
########################################
########################################
########################################

brd_char 	= ['w','x','y','z']
brd_char[0] = chr(fc7.read("board_id_char1"))
brd_char[1] = chr(fc7.read("board_id_char2"))
brd_char[2] = chr(fc7.read("board_id_char3"))
brd_char[3] = chr(fc7.read("board_id_char4"))
board_id = ''.join([brd_char[0],brd_char[1],brd_char[2],brd_char[3]])	

rev_char 	= ['w','x','y','z']
rev_char[0] = chr(fc7.read("rev_id_char1"))
rev_char[1] = chr(fc7.read("rev_id_char2"))
rev_char[2] = chr(fc7.read("rev_id_char3"))
rev_char[3] = chr(fc7.read("rev_id_char4"))
rev_id = ''.join([rev_char[0],rev_char[1],rev_char[2],rev_char[3]])	

ver_major = fc7.read("ver_major")
ver_minor = fc7.read("ver_minor")
ver_build = fc7.read("ver_build")
ver = '.'.join([str(ver_major),str(ver_minor),str(ver_build)])	

yyyy = 2000+fc7.read("firmware_yy")
mm        = fc7.read("firmware_mm")
dd        = fc7.read("firmware_dd")
date = '/'.join([str(dd),str(mm),str(yyyy)])	

mac    = ['00','00','00','00','00','00']
mac[5] = uInt8HexStr(fc7.read("mac_b5"))
mac[4] = uInt8HexStr(fc7.read("mac_b4"))
mac[3] = uInt8HexStr(fc7.read("mac_b3"))
mac[2] = uInt8HexStr(fc7.read("mac_b2"))
mac[1] = uInt8HexStr(fc7.read("mac_b1"))
mac[0] = uInt8HexStr(fc7.read("mac_b0"))
mac_addr = ':'.join([mac[5],mac[4],mac[3],mac[2],mac[1],mac[0]])

eui    = ['00','00','00','00','00','00']
eui[5] = uInt8HexStr(fc7.read("eui_b5"))
eui[4] = uInt8HexStr(fc7.read("eui_b4"))
eui[3] = uInt8HexStr(fc7.read("eui_b3"))
eui[2] = uInt8HexStr(fc7.read("eui_b2"))
eui[1] = uInt8HexStr(fc7.read("eui_b1"))
eui[0] = uInt8HexStr(fc7.read("eui_b0"))
eui48 = ' '.join([eui[5],eui[4],eui[3],eui[2],eui[1],eui[0]])

usr_char 	= ['w','x','y','z']
usr_char[0] = chr(fc7.read("usr_id_char1"))
usr_char[1] = chr(fc7.read("usr_id_char2"))
usr_char[2] = chr(fc7.read("usr_id_char3"))
usr_char[3] = chr(fc7.read("usr_id_char4"))
usr_id = ''.join([str(usr_char[0]),str(usr_char[1]),str(usr_char[2]),str(usr_char[3])])	


usr_ver_major = fc7.read("usr_ver_major")
usr_ver_minor = fc7.read("usr_ver_minor")
usr_ver_build = fc7.read("usr_ver_build")

usr_ver = '.'.join([str(usr_ver_major),str(usr_ver_minor),str(usr_ver_build)])	


usr_firmware_yy = fc7.read("usr_firmware_yy")
usr_firmware_mm = fc7.read("usr_firmware_mm")
usr_firmware_dd = fc7.read("usr_firmware_dd")

usr_date = '/'.join([str(usr_firmware_dd),str(usr_firmware_mm),str(usr_firmware_yy+2000)])	

if debug==1: print "[info]: id  |board type         ->" , board_id
if debug==1: print "[info]: id  |board revision     ->" , rev_id   
if debug==1: print "[info]: id  |system fw version  ->" , ver     
if debug==1: print "[info]: id  |system fw date     ->" , date    
if debug==1: print "[info]: id  |user type          ->" , usr_id   
if debug==1: print "[info]: id  |user fw version    ->" , usr_ver     
if debug==1: print "[info]: id  |user fw date       ->" , usr_date    
if debug==1: print "[info]: id  |eui48 (register)   ->" , eui48
    

########################################
########################################
########################################
########################################
########################################
########################################
########################################
########################################
########################################
########################################


#fc7.write("i2c_settings", 0)

########################################
# get unique id
########################################

euiRegBuffer = [0,0,0,0,0,0]
euiRdxBuffer = [0,0,0,0,0,0]

i2c_en    = 1
i2c_sel   = 0
i2c_presc = 1000
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)

i2c_str   = 1
i2c_m16   = 0
i2c_slv   = 0x50

wr = 1
rd = 0
unused = 0x00
addr = 0xfa
eui_eep    = ['00','00','00','00','00','00']

for i in range(0,6):
	#                    (slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
	euiRdxBuffer[i] = i2c(i2c_slv, wr, unused , addr+i, unused, unused, 0    )
	euiRegBuffer[i] = i2c(i2c_slv, rd, unused , unused, unused, unused, 0    )
	eui_eep[5-i] = uInt8HexStr(euiRegBuffer[i])

	eui48_eep = ' '.join([eui_eep[5],eui_eep[4],eui_eep[3],eui_eep[2],eui_eep[1],eui_eep[0]])

	
if debug==1: print "[info]: id  |eui48 (eeprom)     ->",eui48_eep

if euiRegBuffer[0]==0x00 and euiRegBuffer[1]==0x04 and euiRegBuffer[2]==0xa3:
	print "[TEST]: id  |hw identification  -> /PASS/"
elif euiRegBuffer[0]==0x00 and euiRegBuffer[1]==0x1e and euiRegBuffer[2]==0xc0:
	print "[TEST]: id  |hw identification  -> /PASS/"
else:
	print "[TEST]: id  |hw identification  -> /FAIL/"

	
	
i2c_en    = 0
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)

########################################
# get mac from eeprom
########################################
macRegBuffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
macRdxBuffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

i2c_en    = 1
i2c_sel   = 0
i2c_presc = 1000
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)

i2c_str   = 1
i2c_m16   = 0
i2c_slv   = 0x50

wr = 1
rd = 0
unused = 0x00
reg = 0x00

mac_eep    = ['00','00','00','00','00','00']

for i in range(0,16):
	#                 (slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
	macRdxBuffer[i] = i2c(i2c_slv, wr, unused , reg+i , unused, unused, 0    )
	macRegBuffer[i] = i2c(i2c_slv, rd, unused , unused, unused, unused, 0    )

for i in range(1,7):
	mac_eep[6-i] = uInt8HexStr(macRegBuffer[i])

mac_addr_eep = ':'.join([mac_eep[5],mac_eep[4],mac_eep[3],mac_eep[2],mac_eep[1],mac_eep[0]])

i2c_en    = 0
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)

if debug==1: print "[info]: id  |mac (register)     ->" , mac_addr
if debug==1: print "[info]: id  |mac (eeprom)       ->" , mac_addr_eep

if debug==1: print "[info]: id  |eeprom read status ->" , fc7.read("eep_read_done")
if debug==1: print "[info]: id  |dip switch status  ->" , uInt8HexStr(fc7.read("dipsw"))


