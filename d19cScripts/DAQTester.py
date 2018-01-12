from fc7_daq_methods import *

#####################
# START HERE
#####################
SendCommand_CTRL("global_reset")
sleep(1)

#####################
# tlu mode: 0 - no handshake, 1 - simple handshake, 2 - data hanshake
#####################
handshake_mode = 2
#fc7 = getIPFromFile()
fc7.write("cnfg_tlu_handshake_mode", handshake_mode)

################
## dio5 config #
################
# enabled outputs
out_en = [1,0,1,0,0]
# 50ohm termination
term_en = [0, 1, 0, 1, 1]
# thresholds
thresholds = [0,50,0,50,50]
################
#InitFMCPower("fmc_l8")
#Configure_DIO5(out_en, term_en, thresholds)

################
## fast config #
################
# trigger_source: 1 - L1, 2 - Stubs Coincidence, 3 - User Frequency, 4 - TLU, 5 - External from DIO5, 6 - triggers from test pulse sending machine
trigger_source = 6
# triggers_to_accept: 0 - continious triggering, otherwise sends neeeded amount and turns off
triggers_to_accept = 10
# trigger_user_frequency: in kHz 1 to 1000.
trigger_user_frequency = 33
# trigger_stubs_mask: can set a stubs coincidence, 5 means that stubs from hybrids id=2 and id=0 are required: 1b'101
trigger_stubs_mask = 5
# stub trigger latency
trigger_stub_latency = 195
################

CBC_type = "CBC3_emulator"

################
if(CBC_type == "CBC3_emulator"):
	print "doing nothing for configuration of the CBC3 emulator"
	
elif(CBC_type == "CBC2_real"):
	CBC_ConfigTXT()
################

fc7.write("common_stubdata_delay", trigger_stub_latency)
sleep(0.001)

Configure_Fast(triggers_to_accept, trigger_user_frequency, trigger_source, trigger_stubs_mask, trigger_stub_latency)
SendCommand_CTRL("start_trigger")

#changing the i2c registers before taking data.
#LSBs of VCTH
#SendCommand_I2C(2,            0,                  0,        0,    0,      0,                 33,    6, 1)
#MSBs of VCTH
#SendCommand_I2C(2,            0,                  0,        0,    0,      0,                 34,    0, 1)
#channel data
#SendCommand_I2C(2,            0,                  0,        0,    0,      0,                 2,   0 , 1)
#SendCommand_I2C(2,            0,                  0,        0,    0,      0,                 32,   0 , 1)
#SendCommand_I2C(2,            0,                  0,        0,    0,      0,                 12,   0 , 1)
#sleep(2)
"""
print "Waiting for triggers:"
i = 0
while((triggers_to_accept>0 and i<triggers_to_accept) or (triggers_to_accept==0)):
	if (fc7.read("words_cnt") >= 28):
		REC_DATA = fc7.fifoRead("readout_run_fifo",28)
		#print uInt32HexListStr(REC_DATA[0:size])
		print_data(2, 1, REC_DATA)
		i=i+1



nTriggerBatches = 0
while(nTriggerBatches < 1):
	print "Waiting for triggers:"
	SendCommand_CTRL("start_trigger")
	sleep(0.01)
	i = 0
	while((triggers_to_accept>0 and i<triggers_to_accept) or (triggers_to_accept==0)):
		if (fc7.read("words_cnt") >= 28):
			REC_DATA = fc7.fifoRead("readout_run_fifo",28)
			#print uInt32HexListStr(REC_DATA[0:size])
			print_data(2, 1, REC_DATA)
			i=i+1
ReadChipData(False, 0)
"""
fc7.write("common_stubdata_delay", trigger_stub_latency)
sleep(0.001)

Configure_Fast(triggers_to_accept, trigger_user_frequency, trigger_source, trigger_stubs_mask, trigger_stub_latency)
SendCommand_CTRL("start_trigger")

ReadStatus()

print "Waiting for triggers:"
i = 0
while((triggers_to_accept>0 and i<triggers_to_accept) or (triggers_to_accept==0)):
        if (fc7.read("words_cnt") >= 28):
                REC_DATA = fc7.fifoRead("readout_run_fifo",28)
                #print uInt32HexListStr(REC_DATA[0:size])
                print_data(2, 1, REC_DATA)
                i=i+1

print "Number of words left: ", fc7.read("words_cnt")
	print "Number of words left: ", fc7.read("words_cnt")
	nTriggerBatches = nTriggerBatches +1
	print "number of trigger batches: ", nTriggerBatches
