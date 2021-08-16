# basic d19c methods include
from d19cScripts.fc7_daq_methods import *

##----- begin methods definition 

##----- begin main

# start from phase tuning
fc7.write("ctrl_phy_phase_tune_again", 1)
while(fc7.read("fc7_daq_ctrl.physical_interface_block.phase_tuning_ctrl_done") == 0):
	sleep(0.5)
	print "Waiting for the phase tuning"

# now send the start for l1a and stub data capturing
SendCommand_CTRL("fc7_daq_ctrl.fast_command_block.control.fast_test_pulse")
SendCommand_CTRL("fast_trigger")
sleep(0.001)

status = fc7.read("stat_slvs_debug_general")
mpa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
mpa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)

print "--> Status: "
print "---> MPA L1 Data Ready: ", ((status & 0x00000001) >> 0)
print "---> MPA Stub Data Ready: ", ((status & 0x00000002) >> 1)
print "---> MPA Counters Ready: ", ((status & 0x00000004) >> 2)
print "---> Lateral Data Counters Ready: ", ((status & 0x00000008) >> 3)

print "\n--> L1 Data: "
for word in mpa_l1_data:
    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

print "\n--> Stub Data: "
for word in mpa_stub_data:
    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

print "\n--> Lateral Data: "
for word in lateral_data:
    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

