from fc7_daq_methods import *
from send_i2c import *

def getbits(x, b0, bn):
    return (x >> b0) & ((1 << bn) - 1)


# data printing
def GetData():
	print "N Events Avalibale: ", fc7.read("evnt_cnt")
	nevents = fc7.read("evnt_cnt")

	for i in range(0, nevents):
		REC_DATA = fc7.fifoRead("ctrl_readout_run_fifo",size)
		print uInt32HexListStr(REC_DATA[0:size])
		#print "header: " , uInt32HexListStr(REC_DATA[0:6])

		#print "error: " , getbits(REC_DATA[6:7][0], 0, 2)
		#print "L1: " , getbits(REC_DATA[6:7][0], 4, 9)
		#print "NScluster: " , getbits(REC_DATA[6:7][0], 16, 5)
		#print "NPcluster: " , getbits(REC_DATA[6:7][0], 24, 5)
		
		#for i in range(0,12):
		#	bits = REC_DATA[7+i:8+i][0]	
		#	print 2*i , " Scluster address: ", getbits(bits,0,7)
		#	print 2*i ," Scluster MIP: ", getbits(bits,7,1)
		#	print 2*i ," Scluster width: ", getbits(bits,8,3)
		#	print 2*i+1 ," Scluster address: ", getbits(bits,16,7)
		#	print 2*i+1 ," Scluster MIP: " , getbits(bits,23,1)
		#	print 2*i+1 ," Scluster width: ", getbits(bits,24,3)
		#	print "Type: " , " " , getbits(bits,30,2)
		#	
		#for i in range(0,16):
#		#	print "Pcluster: ", i , " " , uInt32HexListStr(REC_DATA[19+i:20+i])
		#        bits = REC_DATA[19+i:20+i][0]
		#	print 2*i , " Pcluster address: ", getbits(bits,0,7)
		#	print 2*i ," Pcluster width: ", getbits(bits,7,3)
		#	print 2*i ," Pcluster zinfo: ", getbits(bits,10,4)
		#	print 2*i+1 ," Pcluster address: ", getbits(bits,16,7)
		#	print 2*i+1 ," Pcluster width: " , getbits(bits,23,3)
		#	print 2*i+1 ," Pcluster zinfo: ", getbits(bits,26,4)
		#	print "Type: " , " " , getbits(bits,30,2)
			

		#print "Stubs: " , uInt32HexListStr(REC_DATA[35:38])
		#print_data(num_chips,packet_nbr+1, REC_DATA)

# test Temp CBC2 Readout
def ReadoutTesterCBC2():
	write = 0
	read = 1
	delay_after_fast_reset = 50
	delay_after_test_pulse = 200
	delay_before_next_pulse = 400
	number_of_test_pulses = 1
	Configure_TestPulse(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses)
	
	# for real CBC2
	CBC_ConfigTXT()
	# for CBC3 emulator
	#SendCommand_I2C(          2,         0,       0, 0,    0, write,        2,   0, 0)
	#SendCommand_I2C(          2,         0,       0, 0,    0, write,        3,   0, 0)
	#SendCommand_I2C(          2,         0,       0, 0,    0, write,        4,   0, 0)


	SetParameterI2C("select_channel_group", 0)
	sleep(1)	

	for i in range(0,8):
		SetParameterI2C("select_channel_group", i)
		sleep(0.5)		
		SendCommand_CTRL("start_trigger")
		sleep(0.1)

# configure test pulse fsm	
def ReadoutTesterMPA():
	## stub trigger
	fc7.write("cnfg_fast_source", 2)
	fc7.write("cnfg_fast_triggers_to_accept", 0)
	sleep(0.01)
  	SendCommand_CTRL("load_trigger_config")
	# it will run continously and be triggered everytime you send the test pulse
	sleep(0.1)
	SendCommand_CTRL("start_trigger")

	stub_data_delay = 201
	for i in range(stub_data_delay,stub_data_delay+1):
	#for i in range(0,1):
		print "Stub Delay Value: ", i
		fc7.write("cnfg_readout_common_stubdata_delay", i)
		sleep(0.1)
		fc7.write("ctrl_readout_reset",1)
		sleep(0.1)
		fc7.write("ctrl_readout_reset",0)
		sleep(0.5)
		#SendCommand_CTRL("start_trigger")
		SendCommand_CTRL("fast_test_pulse")
		sleep(0.1)				
		GetData()

####################
## Program Running #
####################

##--=======================================--

#**************************************************#
#----> INIT AT STARTUP
#**************************************************#
#SendCommand_CTRL("global_reset")
#sleep(2)
#fc7.write("readout_reset",1)

#**************************************************#
#----> ACQUISITION SETTINGS
#**************************************************#
data_handshake_enable = 0
packet_nbr = 0 #0: 1 packet
num_chips = 1
stub_delay = 30
trigger_type = 0 #0: from top-level / #1: internal trigger (be_proc)
data_type = 0 #0: from top-level (PHY interface) / #1: internal emulating data (test pattern)
size = (6+num_chips*32)*(packet_nbr+1)

#**************************************************#
#----> DAQ CONFIGURATION
#**************************************************#
fc7.write("cnfg_readout_data_handshake_enable", data_handshake_enable)
fc7.write("cnfg_readout_packet_nbr", packet_nbr)
fc7.write("cnfg_readout_trigger_type", trigger_type)
fc7.write("cnfg_readout_data_type", data_type)
fc7.write("cnfg_readout_common_stubdata_delay", stub_delay)
sleep(0.001)

#**************************************************#
#----> START
#**************************************************#
#fc7.write("readout_reset", 0)
#sleep(0.001)
#DIO5Tester("fmc_l8")
#sleep(0.5)
	
ReadoutTesterMPA()
