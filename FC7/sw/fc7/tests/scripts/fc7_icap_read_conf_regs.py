##===================================================================================================##
##==================================== Script Information ===========================================##
##===================================================================================================##
##																								 
## Company:  				CERN (PH-ESE-BE)													 
## Engineer: 				Manoel Barros Marin (manoel.barros.marin@cern.ch) (m.barros@ieee.org)
## 																						 					
## Create Date:				05/04/2013													 
## Script Name:				fc7_icap_bootsts_status_reg_rd											 
## Python Version:			2.7.3																			
##																											
## Revision:				1.0 																				
##																													
## Additional Comments: 																							
## * Note!!! The bit 26 of the status register is different when read by JTAG than by ICAP because
##           the JTAG interface is 16 bit (status[26] = 0) while the ICAP interface is set to 32 bit
##           (status[26] = 1)(See Xilinx AR# 34909).
##																		
##===================================================================================================##
##===================================================================================================##

## Python modules:
import sys
from time import sleep

## Import the PyChips code - PYTHONPATH must be set to the PyChips installation src folder!
from PyChipsUser import *

##===================================================================================================##
##======================================== Script Body ==============================================## 
##===================================================================================================##

#######################################################################################################
## PYCHIPS
#######################################################################################################

##################################################################################################
### Uncomment one of the following two lines to turn on verbose or very-verbose debug modes.   ###
### These debug modes allow you to see the packets being sent and received.                    ###
##################################################################################################
#chipsLog.setLevel(logging.DEBUG)    # Verbose logging (see packets being sent and received)

# Read in an address table by creating an AddressTable object (Note the forward slashes, not backslashes!)
fc7AddrTable = AddressTable("./fc7AddrTable.dat")

f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
print
print "--=======================================--"
print "  Opening fc7 with IP", ipaddr
print "--=======================================--"

#######################################################################################################
## Main
#######################################################################################################

#####################################################################

###################
## ICAP commands ##
###################

idcode_command_pre = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xAA995566, 0x20000000, 0x20000000, 0x20000000, 0x28018001, 0x20000000, 0x20000000]

bootsts_command_pre = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xAA995566, 0x20000000, 0x20000000, 0x20000000, 0x2802C001, 0x20000000, 0x20000000]

status_command_pre = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xAA995566, 0x20000000, 0x20000000, 0x20000000, 0x2800E001, 0x20000000, 0x20000000]

command_post = [0x30008001, 0x0000000d,0x20000000]


#####################################################################

#####################################################################

## bootsts register:	
print
fc7.fifoWrite("icap", idcode_command_pre, 0)
idcode_reg = fc7.read("icap")
fc7.fifoWrite("icap", command_post, 0)
print "-> Reading IDCODE ...", uInt32HexStr(idcode_reg)
print "->"

####################
## Read registers ##
####################

bootsts_len = 16
status_len  = 32

## Register bit masks:
regMask = []
for i in range(32):
	regMask.append(0x00000000 + (2**i))
	
## bootsts register:	
print
fc7.fifoWrite("icap", bootsts_command_pre, 0)
bootsts_reg = fc7.read("icap")
fc7.fifoWrite("icap", command_post, 0)
print "-> Reading bootsts register content...",uInt32HexStr(bootsts_reg)
print "->"

bootsts_bit = []
for i in range(bootsts_len):
	bootsts_bit.append(0)
	bootsts_bit[i] = (bootsts_reg & regMask[i]) >> i

print "-> BOOTSTS register content details"
print "-> [0]  VALID_0 - ERROR OR END OF STARTUP (EOS) DETECTED...............:", bootsts_bit[0]
print "-> [1]  FALLBACK_0 - FALLBACK TRIGGERED RECONFIGURATION................:", bootsts_bit[1]
print "-> [2]  IPROG_0 - INTERNAL WARMBOOT (IPROG) TRIGGERED RECONFIGURATION..:", bootsts_bit[2]
print "-> [3]  WTO_ERROR_0 - WATCHDOG TIME OUT ERROR..........................:", bootsts_bit[3]
print "-> [4]  ID_ERROR_0 - FPGA DEVICE IDCODE ERROR..........................:", bootsts_bit[4]
print "-> [5]  CRC_ERROR_0 - CYCLIC REDUNDANCY CHECK (CRC) ERROR..............:", bootsts_bit[5]
print "-> [6]  WRAP_ERROR_0 - BPI FLASH ADDRESS COUNTER WRAP AROUND ERROR.....:", bootsts_bit[6]
print "-> [7]  HMAC_ERROR_0 - HMAC ERROR......................................:", bootsts_bit[7]
print "-> [8]  VALID_1 - ERROR OR END OF STARTUP (EOS) DETECTED...............:", bootsts_bit[8]
print "-> [9]  FALLBACK_1 - FALLBACK TRIGGERED RECONFIGURATION................:", bootsts_bit[9]
print "-> [10] IPROG_1 - INTERNAL WARMBOOT (IPROG) TRIGGERED RECONFIGURATION..:", bootsts_bit[10]
print "-> [11] WTO_ERROR_1 - WATCHDOG TIME OUT ERROR..........................:", bootsts_bit[11]
print "-> [12] ID_ERROR_1 - FPGA DEVICE IDCODE ERROR..........................:", bootsts_bit[12]
print "-> [13] CRC_ERROR_1 - CYCLIC REDUNDANCY CHECK (CRC) ERROR..............:", bootsts_bit[13]
print "-> [14] WRAP_ERROR_1 - BPI FLASH ADDRESS COUNTER WRAP AROUND ERROR.....:", bootsts_bit[14]
#print "-> [15] RESERVED.......................................................:", bootsts_bit[15]

## status register:
print 
fc7.fifoWrite("icap", status_command_pre, 0)
status_reg = fc7.read("icap")
fc7.fifoWrite("icap", command_post, 0)
print "-> Reading status register content...",uInt32HexStr(status_reg)
print "->"




status_bit = []
for i in range(status_len):
	status_bit.append(0)
	status_bit[i] = (status_reg & regMask[i]) >> i

print "-> STATUS register content details"
print "-> [0]  CRC_ERROR......................................................:", status_bit[0]
print "-> [1]  PART_SECURED...................................................:", status_bit[1]
print "-> [2]  MMCM_LOCK......................................................:", status_bit[2]
print "-> [3]  DCI_MATCH......................................................:", status_bit[3]
print "-> [4]  EOS............................................................:", status_bit[4]
print "-> [5]  GTS_CFG_B......................................................:", status_bit[5]
print "-> [6]  GWE............................................................:", status_bit[6]
print "-> [7]  GHIGH_B........................................................:", status_bit[7]
print "-> [8]  MODE[0]........................................................:", status_bit[8]
print "-> [9]  MODE[1]........................................................:", status_bit[9]
print "-> [10] MODE[2]........................................................:", status_bit[10]
print "-> [11] INIT_COMPLETE..................................................:", status_bit[11]
print "-> [12] INIT_B.........................................................:", status_bit[12]
print "-> [13] RELEASE_DONE...................................................:", status_bit[13]
print "-> [14] DONE...........................................................:", status_bit[14]
print "-> [15] ID_ERROR.......................................................:", status_bit[15]
print "-> [16] DEC_ERROR......................................................:", status_bit[16]
print "-> [17] XADC_OVER_TEMP.................................................:", status_bit[17]
print "-> [18] STARTUP_STATE[0]...............................................:", status_bit[18]
print "-> [19] STARTUP_STATE[1]...............................................:", status_bit[19]
print "-> [20] STARTUP_STATE[2]...............................................:", status_bit[20]
#print "-> [21] RESERVED.......................................................:", status_bit[21]
#print "-> [22] RESERVED.......................................................:", status_bit[22]
#print "-> [23] RESERVED.......................................................:", status_bit[23]
#print "-> [24] RESERVED.......................................................:", status_bit[24]
print "-> [25] BUS_WIDTH[0]...................................................:", status_bit[25]
print "-> [26] BUS_WIDTH[1]...................................................:", status_bit[26]
#print "-> [27] RESERVED.......................................................:", status_bit[27]
#print "-> [28] RESERVED.......................................................:", status_bit[28]
#print "-> [29] RESERVED.......................................................:", status_bit[29]
#print "-> [30] RESERVED.......................................................:", status_bit[30]
#print "-> [31] RESERVED.......................................................:", status_bit[31]

print "->"
print "-> done"

##===================================================================================================##
##===================================================================================================##	