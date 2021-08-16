from fc7_daq_methods import *

def LoadConfig():
	# set fast commands
	# trigger to accept 0
        fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", 100000)
	# user frequency set to 1000 just in case we want to use
        fc7.write("cnfg_fast_user_frequency", 1000)
	# trigger source
        fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 3)
        # consecutive
        fc7.write("cnfg_fast_delay_between_consecutive_trigeers", 30)
        fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", 39)
	# backpressure enable
	fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 1)
	# initial fast reset
	fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", 1)
	# load config
	sleep(0.01)
	fc7.write("fc7_daq_ctrl.fast_command_block.control.load_config", 1)

	# readout block
	# number of events in package
	fc7.write("cnfg_readout_packet_nbr", 9999)
	# enable data handshake
	fc7.write("cnfg_readout_data_handshake_enable", 0)

	print "--> config is loaded"

def ResetBoard():
	SendCommand_CTRL("global_reset")
	sleep(0.1)
	print "--> d19c was reset"

def ReadCounter():
	return fc7.read("rate_measurement_bx_counter")

def ReadNWords():
	return fc7.read("words_cnt")

def ResetReadout():
        print "--> readout reset done"
        while(not fc7.read("stat_ddr3_initial_calibration_done")):
                sleep(0.01)
        print "--> ddr3 init done"
	fc7.write("fc7_daq_ctrl.readout_block.control.readout_reset",1)
        sleep(0.1)
        fc7.write("fc7_daq_ctrl.readout_block.control.readout_reset",0)
        sleep(0.5)


### Program Run
ResetBoard()
LoadConfig()
ResetReadout()
print "Counter value in the beginning is: ", ReadCounter()
print "Number of words in the beginning is: ", ReadNWords()

SendCommand_CTRL("start_trigger")
print "------"
sleep(3)

counter_value = ReadCounter()
nwords = ReadNWords()
print "Counter value in the end is: ", counter_value
print "Number of words in the end is: ", nwords
time = counter_value/40e6
rate = nwords/time/1000
print "Resulting packing rate: ", rate, "kWords/s (", 32*rate/1e6,  "Gbps )"
# event size 32 for 1x2xCBC3 hybrid, 744 for 32x2xCBC3 hybrids
n_hybrids = 1
total_chip_data_size = 32 # 32 for one MPA, 22 for 2xCBC
event_size = 5 + n_hybrids*(1 + total_chip_data_size)
event_size = (8-event_size%8) + event_size
print "Or: ", rate/event_size, "kEvents/s"
print "Numver of events: ", nwords/event_size
