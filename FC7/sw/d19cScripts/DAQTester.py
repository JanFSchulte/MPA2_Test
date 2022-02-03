from fc7_daq_methods import *

#####################
# START HERE
#####################
SendCommand_CTRL("global_reset")
sleep(1)

#####################
# tlu enable: 0,1
# tlu mode: 0 - no handshake, 1 - simple handshake, 2 - data handshake
#####################
tlu_enable = 0
tlu_handshake_mode = 2
fc7.write("cnfg_tlu_handshake_mode", tlu_handshake_mode)
fc7.write("cnfg_tlu_enabled", tlu_enable)

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
trigger_source = 3
# triggers_to_accept: 0 - continious triggering, otherwise sends neeeded amount and turns off
triggers_to_accept = 10
# trigger_user_frequency: in kHz 1 to 1000.
trigger_user_frequency = 1
# trigger_stubs_mask: can set a stubs coincidence, 5 means that stubs from hybrids id=2 and id=0 are required: 1b'101
trigger_stubs_mask = 5
# stub trigger latency
trigger_stub_delay = 195
#so called stub latency
trigger_stub_latency = 40

################
##CHIP config###
################
chip_type = "SSA_emulator"
header_size = 6
n_chips = 2
payload_size = 0 # this depends on the chip type and is calculated from the IPBus package you send.

if(chip_type == "SSA_emulator"):
	#SendCommand_I2C(command type, hybrid_id, chip_id, page, read, register_address, data, ReadBack)
	# command type: 0 - write to certain chip, hybrid; 1 - write to all chips on hybrid; 2 - write to all chips/hybrids (same for READ)
	#write to register 1 0xff as data --> this will put a 1 on the last 8 channels which go out
	SendCommand_I2C(            2,         0,       0,    0,     0,               1,    0xff,       0)
	#write to register 16 0xaa as data --> this will put a 0xaa on the last 8 bits of the HIP data which goes out
	SendCommand_I2C(            2,         0,       0,    0,     0,               16,    0xaa,       0)
	#write to register 33 1 as data --> this will put different data on the SSA centroid lines
	SendCommand_I2C(            2,         0,       0,    0,     0,               33,    1,       0)
	sleep(0.5)
	payload_size = 7
elif(chip_type == "CBC_emulator"):
	print "Doing nothing to configure the CBC emulator"	
	payload_size = 11
elif(chip_type == "CBC_real"):
	CBC_ConfigTXT()
	payload_size = 11

n_words = header_size+n_chips*payload_size
################
##config fast###
################

fc7.write("cnfg_readout_common_stubdata_delay", trigger_stub_delay)
sleep(0.001)

Configure_Fast(triggers_to_accept, trigger_user_frequency, trigger_source, trigger_stubs_mask, trigger_stub_latency)
SendCommand_CTRL("start_trigger") 
ReadStatus()

################
##taking data###
################

print "Waiting for triggers:"
i = 0

while((triggers_to_accept>0 and i<triggers_to_accept) or (triggers_to_accept==0)):
        if (fc7.read("words_cnt") >= n_words):
                REC_DATA = fc7.fifoRead("ctrl_readout_run_fifo",n_words)
#		print uInt32HexListStr(REC_DATA)
                print_data(chip_type,n_words, n_chips, 1, REC_DATA)
                i=i+1

print "Number of words left: ", fc7.read("words_cnt")
