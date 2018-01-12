from fc7_daq_methods import *

def get_bit(byteval,idx):
    return ((byteval&(1<<idx))!=0)

def DecodeZSEvent(event):
	# zs event format v17
	total_size = (event[0] & 0x0000FFFF)
	print "Total Event Size: ", total_size
	header1_size = (event[0] & 0xFF000000) >> 24
	fe_mask = (event[0] & 0x00FF0000) >> 16
	print "L1 Counter: ", (event[2] & 0x00FFFFFF)

	if(total_size > header1_size):
		for fe in range(0,8):		
			if get_bit(fe_mask, fe) != 0:
				print "	FE #", fe
				header2_size = (event[header1_size] & 0x00FF0000) >> 16
				fe_event_size = (event[header1_size] & 0x0000FFFF)
				print "	Event size for this FE: ", fe_event_size
				for word_id in range (header1_size+header2_size, len(event)):
					chip_id = (event[word_id] & 0xE0000000) >> 29
					data_type = (event[word_id] & 0x18000000) >> 27
					#print "		chip id: ", chip_id, ", data type: ", data_type
					if data_type == 0:
						data_mask = (event[word_id] & 0x03000000) >> 24
						if get_bit(data_mask,0) == 1:
							strip_id = (event[word_id] & 0x000007f8) >> 3
							strip_width = ((event[word_id] & 0x00000007) >> 0) + 1
							print "		Chip ID: ", chip_id, ", Cluster Position: ", strip_id, ", Cluster Width: ", strip_width
						if get_bit(data_mask,1) == 1:
							strip_id = (event[word_id] & 0x003fc000) >> 14
							strip_width = ((event[word_id] & 0x00003800) >> 11) + 1
							print "		Chip ID: ", chip_id, ", Cluster Position: ", strip_id, ", Cluster Width: ", strip_width	
					if data_type == 1:						
						stub_address = (event[word_id] & 0x001fe000) >> 13
						stub_bend = (event[word_id] & 0x000003c0) >> 6
						sync = (event[word_id] & 0x00000008) >> 3
						err_flag = (event[word_id] & 0x00000004) >> 2
						or_254 = (event[word_id] & 0x00000002) >> 1
						stub_overflow = (event[word_id] & 0x00000001) >> 0
						print "		Chip ID: ", chip_id, ", Stub Address: ", stub_address, ", Stub Bend: ", stub_bend
					if data_type == 2:				
						cluster_ovf = (event[word_id] & 0x04000000) >> 26		
						pipe_addr = (event[word_id] & 0x00001ff0) >> 4
						l1_counter = (event[word_id] & 0x01ff0000) >> 16
						sync = (event[word_id] & 0x00000008) >> 3
						buf_ovf = (event[word_id] & 0x00000002) >> 1
						lat_err = (event[word_id] & 0x00000001) >> 0
						print "		Chip ID: ", chip_id, ", Cluster Overflow: ", cluster_ovf, ", L1 Counter: ", l1_counter, ", Pipeline Address: ", pipe_addr											

	else:
		print "Empty Event(only header1)"
			
			
	

#####################
# START HERE
#####################
SendCommand_CTRL("global_reset")
sleep(1)

################
## fast config #
################
# trigger_source: 1 - L1, 2 - Stubs Coincidence, 3 - User Frequency, 4 - TLU, 5 - External from DIO5, 6 - triggers from test pulse sending machine
trigger_source = 6
# triggers_to_accept: 0 - continious triggering, otherwise sends neeeded amount and turns off
triggers_to_accept = 1
# trigger_user_frequency: in kHz 1 to 1000.
trigger_user_frequency = 1
# trigger_stubs_mask: can set a stubs coincidence, 5 means that stubs from hybrids id=2 and id=0 are required: 1b'101
trigger_stubs_mask = 5
# stub trigger latency
trigger_stub_latency = 200
################

###############
## daq config
###############
data_handshake_enable = 0
packet_nbr = 0 #0: 1 packet
stub_delay = 193
zero_suppression_enable = 1
zs_max_nclusters = 31
###############

################
CBC_ConfigTXT()
fc7.write("zero_suppression_enable", zero_suppression_enable)
fc7.write("zs_max_nclusters", zs_max_nclusters)
fc7.write("data_handshake_enable", data_handshake_enable)
fc7.write("packet_nbr", packet_nbr)
fc7.write("common_stubdata_delay", stub_delay)
################

## enabling channels
write = 0
#for chip in [0,2,3,4,5,6,7]:
#	for i in range(0,255):
#		SendCommand_I2C(0, 0, chip, 0, 1, write, i, 0xFF, 0)
#for i in range(0,255):
#	SendCommand_I2C(0, 0, 1, 0, 1, write, i, 0x00, 0)
#sleep(1)
## readout reset ##
fc7.write("readout_reset", 1)
sleep(0.001)
fc7.write("readout_reset", 0)
sleep(0.001)
###################

Configure_Fast(triggers_to_accept, trigger_user_frequency, trigger_source, trigger_stubs_mask, trigger_stub_latency)

for i in range (0,8):
	SetParameterI2C("select_channel_group", i)
	sleep(1)

	fc7.write("readout_reset", 1)
	sleep(0.001)
	fc7.write("readout_reset", 0)
	sleep(0.001)

	SendCommand_CTRL("start_trigger")
	

	ReadStatus()

	print "Waiting for triggers:"
	i = 0

	while((triggers_to_accept>0 and i<triggers_to_accept) or (triggers_to_accept==0)):
		header1 = fc7.read("readout_run_fifo")
		event_size = (header1 & 0x0000FFFF)
		if (fc7.read("words_cnt") >= event_size-1):
			REC_DATA = fc7.fifoRead("readout_run_fifo",event_size-1)
			REC_DATA = [header1] + REC_DATA
			#print header1
			if zero_suppression_enable == 0:
				print uInt32HexListStr(REC_DATA[0:event_size])
			else:
				DecodeZSEvent(REC_DATA)
			i=i+1

	print "Number of words left: ", fc7.read("words_cnt")


