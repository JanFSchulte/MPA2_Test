from fc7_daq_methods import *

# test Temp CBC2 Readout
def ReadoutTester():
	write = 0
	read = 1
	delay_after_fast_reset = 50
	delay_after_test_pulse = 200
	delay_before_next_pulse = 400
	number_of_test_pulses = 1
	Configure_TestPulse(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses)
	
	# for real CBC2
	#CBC_ConfigTXT()
	# for CBC3 emulator
	#SendCommand_I2C(          2,         0,       0, 0,    0, write,        2,   0, 0)
	#SendCommand_I2C(          2,         0,       0, 0,    0, write,        3,   0, 0)
	#SendCommand_I2C(          2,         0,       0, 0,    0, write,        4,   0, 0)


	#SetParameterI2C("select_channel_group", 0)
	sleep(1)	

	for i in range(0,8):
		#SetParameterI2C("select_channel_group", i)
		#sleep(0.5)		
		SendCommand_CTRL("start_trigger")
		sleep(0.1)
	

####################
## Program Running #
####################

##--=======================================--

#**************************************************#
#----> INIT AT STARTUP
#**************************************************#
SendCommand_CTRL("global_reset")
sleep(2)
#fc7.write("readout_reset",1)

#**************************************************#
#----> ACQUISITION SETTINGS
#**************************************************#
"""
data_handshake_enable = 0
packet_nbr = 0 #0: 1 packet
num_chips = 2
stub_delay = 194
trigger_type = 0 #0: from top-level / #1: internal trigger (be_proc)
data_type = 0 #0: from top-level (PHY interface) / #1: internal emulating data (test pattern)
size = (6+num_chips*11)*(packet_nbr+1)

#**************************************************#
#----> DAQ CONFIGURATION
#**************************************************#
fc7.write("data_handshake_enable", data_handshake_enable)
fc7.write("packet_nbr", packet_nbr)
fc7.write("trigger_type", trigger_type)
fc7.write("data_type", data_type)
fc7.write("common_stubdata_delay", stub_delay)
fc7.write("cnfg_phy_phase_sel",18)
sleep(5)
print "Phase sel stat", fc7.read("stat_phy_phase_sel")
print "Phase sel stat2", fc7.read("stat_phy_phase_sel2")
print "Bitslip", fc7.read("stat_phy_stat_bitslip")
print "Delay", fc7.read("stat_phy_stat_delay")
print "Serial", fc7.read("stat_phy_stat_serializer")
print "stat_fast_fsm", fc7.read("stat_fast_fsm")
sleep(0.001)
#fc7.write("cnfg_phy_phase_sel",15)
#sleep(5)
#print "Phase sel stat", fc7.read("stat_phy_phase_sel")
#print "Phase sel stat2", fc7.read("stat_phy_phase_sel2")
#print "Bitslip", fc7.read("stat_phy_stat_bitslip")
#print "Delay", fc7.read("stat_phy_stat_delay")
#print "Serial", fc7.read("stat_phy_stat_serializer")
#print "stat_fast_fsm", fc7.read("stat_fast_fsm")

#**************************************************#
#----> START
#**************************************************#
#fc7.write("readout_reset", 0)
#sleep(0.001)
#DIO5Tester("fmc_l8")
#sleep(0.5)
	
ReadoutTester()
sleep(1)

print "N Events Avalibale: ", fc7.read("evnt_cnt")
nevents = fc7.read("evnt_cnt")

for i in range(0, nevents):
	REC_DATA = fc7.fifoRead("readout_run_fifo",size)
	#print uInt32HexListStr(REC_DATA[0:size])
	print_data(num_chips,packet_nbr+1, REC_DATA)
"""
