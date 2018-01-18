from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
#####################
# START HERE
#####################
#SendCommand_CTRL("global_reset")
#sleep(1)

################
#change the phase of the fast_cmd wrt the 320MHz clock going to the chip:
#fc7.write("ctrl_phy_fast_cmd_phase",x)

#change the phase of the fake L1 data going to the MPA wrt the 320MHz clock going to the chip:
#fc7.write("ctrl_phy_ssa_gen_trig_phase",x)

#change the phase of the fake stub data going to the MPA wrt the 320MHz clock going to the chip. All 8 lines are phase shifted with the same amount:
#fc7.write("ctrl_phy_ssa_gen_stub_phase",x)

#register to change the data content of the L1 data send by the SSA data generator. See tables in the manual on what to expect:
#fc7.write("cnfg_phy_SSA_gen_trig_data_format",x)

#register to change the data content of the stub data send by the SSA data generator. See tables in the manual on what to expect:
#fc7.write("cnfg_phy_SSA_gen_stub_data_format",x)

#register to change the delay (expressed in 25ns) imposed on sending the generated SSA L1 data wrt to the trigger signal:
#fc7.write("cnfg_phy_SSA_gen_delay_trig_data",x)

#register to change the delay (expressed in 25ns) imposed on sending the generated SSA stub data wrt to the Cal_strobe signal:
#fc7.write("cnfg_phy_SSA_gen_delay_stub_data",x)

################


def reverse_mask(x):
    x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
    x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
    x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
    x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
    x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
    return x

##----- begin main

def read_regs():
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

def send_trigger():
    SendCommand_CTRL("fast_trigger")

def send_test():
    SendCommand_CTRL("fast_test_pulse")

def reset():
    SendCommand_CTRL("global_reset")

def SetNumberOfDataBytes(slave_id, data_wr_nbytes, data_rd_nbytes):

	#set the numbers
	i2c_slave_map[slave_id].data_wr_nbytes = data_wr_nbytes
	i2c_slave_map[slave_id].data_rd_nbytes = data_rd_nbytes

	# update the map
	fc7.write("cnfg_i2c_settings_map_slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))

# set the default data sizes
def SetDefaultNumberOfDataBytes(slave_id):

	# set default values
	if (i2c_slave_map[slave_id].chip_type == "CBC" or i2c_slave_map[slave_id].chip_type == "MPA"):
		i2c_slave_map[slave_id].data_wr_nbytes = 1
		i2c_slave_map[slave_id].data_rd_nbytes = 1
	else:
		print "Wrong chip type"

	# update the map
	fc7.write("cnfg_i2c_settings_map_slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))

# Combine and Send sequential I2C write Command
def SendCommand_I2C_SeqWrite(command, hybrid_id, chip_id, register_address, data):

  raw_command = fc7AddrTable.getItem("ctrl_command_i2c_command_type").shiftDataToMask(command)
  raw_word0 = fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(0)
  raw_word1 = fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(1)
  raw_hybrid_id = fc7AddrTable.getItem("ctrl_command_i2c_command_hybrid_id").shiftDataToMask(hybrid_id)
  raw_chip_id = fc7AddrTable.getItem("ctrl_command_i2c_command_chip_id").shiftDataToMask(chip_id)
  raw_readback = fc7AddrTable.getItem("ctrl_command_i2c_command_readback").shiftDataToMask(0)
  raw_read = fc7AddrTable.getItem("ctrl_command_i2c_command_read").shiftDataToMask(0)
  raw_register = fc7AddrTable.getItem("ctrl_command_i2c_command_register").shiftDataToMask(register_address)

  cmd0 = raw_command + raw_word0 + raw_hybrid_id + raw_chip_id + raw_readback + raw_read + raw_register;

  description = "Sequential Write Command: type = " + str(command) + ", hybrid = " + str(hybrid_id) + ", chip = " + str(chip_id)

  # first word
  fc7.write("ctrl_command_i2c_command_fifo", cmd0)
  sleep(0.01)

  # nbytes
  nbytes = data.size

  # now iterate
  byte_counter = 0
  word_counter = 1
  while (byte_counter<nbytes):
	raw_word_id = fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(word_counter % 2)
	raw_data = 0
	i = 0
	while(i < 3 and byte_counter < nbytes):
		raw_data = raw_data + (data[byte_counter] << 8*i)
		i = i+1
		byte_counter = byte_counter + 1

	cmd = raw_command + raw_word_id + raw_data
  	fc7.write("ctrl_command_i2c_command_fifo", cmd)
	word_counter = word_counter + 1
	sleep(0.01)

  return description

# read the chip data (nbytes per read transaction)
def ReadChipDataNEW(nbytes = 1):
	numberOfReads = 0
	print "Reading Out Data:"
	print "   =========================================================================================="
	print "   | Hybrid ID             || Chip ID             || Register(LSB)          || DATA         |"
	print "   =========================================================================================="

	while fc7.read("stat_command_i2c_fifo_replies_empty") == 0:
		byte_counter = 0

		reply = fc7.read("ctrl_command_i2c_reply_fifo")
		hybrid_id = DataFromMask(reply, "ctrl_command_i2c_reply_hybrid_id")
		chip_id = DataFromMask(reply, "ctrl_command_i2c_reply_chip_id")
		register = DataFromMask(reply, "ctrl_command_i2c_reply_register")
		data = DataFromMask(reply, "ctrl_command_i2c_reply_data")

		# first byte is always in the first word
		print '   | %s %-12i || %s %-12i || %s %-12s || %-12s |' % ("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4])
		byte_counter = byte_counter + 1
		register = register + 1

		# now iterate next words
		while(byte_counter < nbytes):
			# just in case wait next word
			while(fc7.read("stat_command_i2c_fifo_replies_empty") == 1):
				print "debug: waiting next word, should not happen"
				sleep(1)

			reply = fc7.read("ctrl_command_i2c_reply_fifo")
			data1 = (reply & 0x000000FF) >> 0
			data2 = (reply & 0x0000FF00) >> 8
			data3 = (reply & 0x00FF0000) >> 16

			# this "if" is not necessary - satisfied when entered the while loop - print the first byte of the word
			if (byte_counter < nbytes):
				print '   | %s %-12i || %s %-12i || %s %-12s || %-12s |' % ("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data1)[:4])
				byte_counter = byte_counter + 1
				register = register + 1
			# print the second byte of the word
			if (byte_counter < nbytes):
				print '   | %s %-12i || %s %-12i || %s %-12s || %-12s |' % ("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data2)[:4])
				byte_counter = byte_counter + 1
				register = register + 1
			# print the third byte of the word
			if (byte_counter < nbytes):
				print '   | %s %-12i || %s %-12i || %s %-12s || %-12s |' % ("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data3)[:4])
				byte_counter = byte_counter + 1
				register = register + 1




	print "    -----------------------------------------------------------------------------------------"
	print "   ====================================================   "


def write_I2C (chip, address, data, frequency = 0):
    i2cmux = 0
    MPA = 11
    SSA = 12
    command_type = 0
    read = 1
    write = 0
    readback = 0
    SetSlaveMap()
    Configure_MPA_SSA_I2C_Master(1, frequency)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x04) #enable only MPA-SSA chip I2C
    Configure_MPA_SSA_I2C_Master(0, frequency)
    if (chip == 'MPA'):
        SendCommand_I2C  (command_type, 0, MPA, 0, write, address, data, readback)
    elif (chip == 'SSA'):
        SendCommand_I2C  (command_type, 0, SSA, 0, write, address, data, readback)

def read_I2C (chip, address, data = 0, frequency = 0):
    i2cmux = 0
    MPA = 11
    SSA = 12
    command_type = 0
    read = 1
    write = 0
    readback = 0
    SetSlaveMap()
    Configure_MPA_SSA_I2C_Master(1, frequency)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x04) #enable only MPA-SSA chip I2C
    Configure_MPA_SSA_I2C_Master(0, frequency)
    if (chip == 'MPA'):
        SendCommand_I2C(command_type, 0, MPA, 0, read, address, data, readback)
    elif (chip == 'SSA'):
        SendCommand_I2C(command_type, 0, SSA, 0, read, address, data, readback)
    return ReadChipDataNEW()
