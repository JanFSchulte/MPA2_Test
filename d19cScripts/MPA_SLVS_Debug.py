# basic d19c methods include
from fc7_daq_methods import *

##----- begin methods definition

def reverse_mask(x):
    x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
    x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
    x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
    x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
    x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
    return x

##----- begin main
SendCommand_CTRL("fast_test_pulse")
SendCommand_CTRL("fast_trigger")
sleep(0.001)
##-----

status = fc7.read("stat_slvs_debug_general")
mpa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
mpa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)

print "--> Status: "
print "---> MPA L1 Data Ready: ", ((status & 0x00000001) >> 0)
print "---> MPA Stub Data Ready: ", ((status & 0x00000002) >> 1)
print "---> MPA Counters Ready: ", ((status & 0x00000004) >> 2)

print "\n--> L1 Data: "
for word in mpa_l1_data:
    print "--->", '%10s' % bin(to_number(reverse_mask(word),32,24)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),8,0)).lstrip('-0b').zfill(8)

print "\n--> Stub Data: "
for word in mpa_stub_data:
    print "--->", '%10s' % bin(to_number(reverse_mask(word),32,24)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),8,0)).lstrip('-0b').zfill(8)
