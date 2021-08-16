# basic d19c methods include
from fc7_daq_methods import *

##----- begin methods definition 

def StartCountersRead():
    encode_fast_reset = fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_reset").shiftDataToMask(1)
    encode_orbit_reset = fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_orbit_reset").shiftDataToMask(1)
    fc7.write("fc7_daq_ctrl.fast_command_block", encode_fast_reset + encode_orbit_reset)

##----- begin main

##----- begin configuration
# enables raw_mode of the readout (debug)
raw_mode_enable = 0
fc7.write("cnfg_phy_slvs_raw_mode_en", raw_mode_enable)
##----- end configuration

mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")

print "--> Status: "
print "---> MPA Counters Ready(should be zero): ", mpa_counters_ready

print "---> Sending Start and Waiting for Data"

StartCountersRead()

while (mpa_counters_ready == 0):
     sleep(0.5)
     mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
print "---> MPA Counters Ready(should be one): ", mpa_counters_ready

if raw_mode_enable == 1:
	for i in range(0,20000):
		fifo1_word = fc7.read("ctrl_slvs_debug_fifo1_data")
		fifo2_word = fc7.read("ctrl_slvs_debug_fifo2_data")
		line1 = bin(to_number(fifo1_word,8,0)).lstrip('-0b').zfill(8)
		line2 = bin(to_number(fifo1_word,16,8)).lstrip('-0b').zfill(8)
		line3 = bin(to_number(fifo1_word,24,16)).lstrip('-0b').zfill(8)
		line4 = bin(to_number(fifo2_word,8,0)).lstrip('-0b').zfill(8)
		line5 = bin(to_number(fifo2_word,16,8)).lstrip('-0b').zfill(8)
		print "BX#", '%4s' % i, "--->", '%10s' % line1, '%10s' % line2, '%10s' % line3, '%10s' % line4, '%10s' % line5
else:
	counters = fc7.fifoRead("ctrl_slvs_debug_fifo2_data", 2040)
	
	for i in range(2040):
		print "Counter #", i+1, ": ", counters[i]


sleep(0.1)
mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
print "---> MPA Counters Ready(should be zero): ", mpa_counters_ready
