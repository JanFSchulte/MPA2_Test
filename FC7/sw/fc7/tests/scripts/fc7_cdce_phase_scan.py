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

debug_str=""
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug_str="debug"

spi_comm = 0x8fa38014;
#############  +0 ######## +1 ##### +2 ####### +3 ######## +4 ###### +5 ######            
reg1_160 = [0xeb020321,0xeb020721,0xeb020b21,0xeb030321,0xeb030721,0xeb030b21]

############# +4 ######## +5 ###### +0 ######  +1 ######## +2 ##### +3 #######            
#reg1_160 = [0xeb030721,0xeb030b21,0xeb020321, 0xeb020721,0xeb020b21,0xeb030321]


cdce_clk_source = fc7.read("cdce_refsel")
if cdce_clk_source == 1:
	cdce_clk = "primary"
else:
	cdce_clk = "secondary"

phase_mon_refclk = fc7.read("phase_mon_refclk_sel")
if phase_mon_refclk == 1:
	phase_mon_clk = "240MHz"
else:
	phase_mon_clk = "160MHz"
	
	
if debug_str=="debug": print "[info]: cdce|input clock source ->", cdce_clk
if debug_str=="debug": print "[info]: cdce|phase scan clock   ->", phase_mon_clk
if debug_str=="debug": sys.stdout.flush()


#########################
# phase scan
#########################

#phase_mon_ok = [0,0,0,0,0,0]
max_loop_nbr = 4
loop_nbr = 0
if debug_str=="debug": print "[info]: cdce|phase scan         -> -----------------"
if debug_str=="debug": print "[info]: cdce|phase scan 60 deg  -> +0 +1 +2 +3 +4 +5"
if debug_str=="debug": print "[info]: cdce|phase scan         -> -----------------"
if debug_str=="debug": sys.stdout.flush()

while (1): 
	if loop_nbr==max_loop_nbr: break
	phase = [0,0,0,0,0,0]
	for j in range(0,6):
		# update value
		fc7.write("spi_txdata",reg1_160[j%6])
		fc7.write("spi_command", spi_comm)
		fc7.read("spi_rxdata") # dummy read
		fc7.read("spi_rxdata") # dummy read
		# copy to eeprom & reboot cdce
		os.system('fc7_cdce_copy_to_eeprom.py >> foo')
		os.system('fc7_cdce_powerup_and_sync.py >> foo')
		# check if locked
		locked_cnt = 0
		for i in range (0, 1000):
			lock = fc7.read("cdce_lock")
			if (lock==1): locked_cnt = locked_cnt + 1
		# run phase mon
		#os.system('fc7_cdce_phase_mon.py >> foo')
		# store results when done
		phase_mon_done=0
		while (phase_mon_done==0): phase_mon_done=fc7.read("phase_mon_done")
		phase[j]=fc7.read("phase_mon_count")
		#phase_mon_ok[j] = fc7.read("phase_mon_ok")
		#
	loop_nbr=loop_nbr+1
	# print for every loop
	if debug_str=="debug": print "[info]: cdce|phase scan values  ->",  \
	uInt8HexStr(phase[0]), uInt8HexStr(phase[1]), uInt8HexStr(phase[2]),\
	uInt8HexStr(phase[3]), uInt8HexStr(phase[4]), uInt8HexStr(phase[5])
#	"   ", phase_mon_ok[0],phase_mon_ok[1],phase_mon_ok[2],phase_mon_ok[3],phase_mon_ok[4],phase_mon_ok[5]
	if debug_str=="debug": sys.stdout.flush()

if debug_str=="debug": print "[info]: cdce|phase scan         -> -----------------"

#########################
# select desired phase
#########################

selected_phase = 0
phase_mon_lo = 0x90
phase_mon_hi = 0xb0

fc7.write("spi_txdata",reg1_160[selected_phase])
if debug_str=="debug": print "[info]: cdce|selected phase     ->", selected_phase*60,"deg"

fc7.write("phase_mon_lower", phase_mon_lo)
if debug_str=="debug": print "[info]: cdce|phase_mon_low      ->", uInt8HexStr(phase_mon_lo)
fc7.write("phase_mon_upper", phase_mon_hi)
if debug_str=="debug": print "[info]: cdce|phase_mon_high     ->", uInt8HexStr(phase_mon_hi)


fc7.write("spi_command", spi_comm)
fc7.read("spi_rxdata") # dummy read
fc7.read("spi_rxdata") # dummy read
os.system('fc7_cdce_copy_to_eeprom.py >> foo')
os.system('fc7_cdce_powerup_and_sync.py >> foo')

#########################
# check if locked
#########################

locked_cnt = 0
for i in range (0, 1000):
	lock = fc7.read("cdce_lock")
	if (lock==1): locked_cnt = locked_cnt + 1

#########################
# verify phase
#########################

cdce_phase_mon_done = 0
while (cdce_phase_mon_done==0): cdce_phase_mon_done=fc7.read("phase_mon_done")
cdce_phase_mon_ok=fc7.read("phase_mon_ok")

if debug_str=="debug": print "[info]: cdce|phase_mon_count    ->", uInt8HexStr(fc7.read("phase_mon_count"))
if debug_str=="debug": print "[info]: cdce|locked             ->", (1000/10.0),'%'

if (locked_cnt==1000 and cdce_phase_mon_done==1 and cdce_phase_mon_ok==1):
	print "[TEST]: cdce|phase monitoring   -> /PASS/"
else:
	if locked_cnt==1000: print "[info]: cdce|phase locked       -> 1"
	print "[TEST]: cdce|phase monitoring   -> /FAIL/"