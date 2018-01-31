# basic d19c methods include
from d19cScripts.fc7_daq_methods import *

##----- begin methods definition

def reverse_mask(x):
#    x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
#    x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
#    x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
#    x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
#    x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
    return x

def StartCountersRead():
    encode_fast_reset = fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(1)
    encode_orbit_reset = fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(1)
    fc7.write("ctrl_fast", encode_fast_reset + encode_orbit_reset)

##----- begin main

# Reset the board
print "---> Resetting the d19c board"
SendCommand_CTRL("global_reset")
sleep(1)

mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")

print "--> Status: "
print "---> MPA Counters Ready(should be zero): ", mpa_counters_ready

print "---> Sending Start and Waiting for Data"

StartCountersRead()

while (mpa_counters_ready == 0):
     sleep(0.5)
     mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
print "---> MPA Counters Ready(should be one): ", mpa_counters_ready

for i in range(0,20000):
	fifo1_word = fc7.read("ctrl_slvs_debug_fifo1_data")
	fifo2_word = fc7.read("ctrl_slvs_debug_fifo2_data")
	line1 = bin(to_number(reverse_mask(fifo1_word),8,0)).lstrip('-0b').zfill(8)
	line2 = bin(to_number(reverse_mask(fifo1_word),16,8)).lstrip('-0b').zfill(8)
	line3 = bin(to_number(reverse_mask(fifo1_word),24,16)).lstrip('-0b').zfill(8)
	line4 = bin(to_number(reverse_mask(fifo2_word),8,0)).lstrip('-0b').zfill(8)
	line5 = bin(to_number(reverse_mask(fifo2_word),16,8)).lstrip('-0b').zfill(8)
	print "BX#", '%4s' % i, "--->", '%10s' % line1, '%10s' % line2, '%10s' % line3, '%10s' % line4, '%10s' % line5

sleep(0.1)
mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
print "---> MPA Counters Ready(should be zero): ", mpa_counters_ready
