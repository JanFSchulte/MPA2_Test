# basic d19c methods include
from fc7_daq_methods import *

##----- begin methods definition 

# define the i2c slave map signle item
class I2C_SlaveMapItem:
	def __init__(self):
        	self.i2c_address = 0
        	self.register_address_nbytes = 0
		self.data_wr_nbytes = 1
		self.data_rd_nbytes = 1
		self.stop_for_rd_en = 0
		self.nack_en = 0
		self.chip_type = "UNKNOWN"
		self.chip_name = "UNKNOWN"
	def SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en, chip_type, chip_name):
		self.i2c_address = i2c_address
        	self.register_address_nbytes = register_address_nbytes
		self.data_wr_nbytes = data_wr_nbytes
		self.data_rd_nbytes = data_rd_nbytes
		self.stop_for_rd_en = stop_for_rd_en
		self.nack_en = nack_en
		self.chip_type = chip_type
		self.chip_name = chip_name

# define the i2c map instance
i2c_slave_map = [I2C_SlaveMapItem() for i in range(31)]

# encode slave map item:
def EncodeSlaveMapItem(slave_item):
	
	# this peace of code just shifts the data, also checks if it fits the field
	shifted_i2c_address = fc7AddrTable.getItem("cnfg_i2c_settings_map_slave_0_config_i2c_address").shiftDataToMask(slave_item.i2c_address)
	shifted_register_address_nbytes = fc7AddrTable.getItem("cnfg_i2c_settings_map_slave_0_config_register_address_nbytes").shiftDataToMask(slave_item.register_address_nbytes)
	shifted_data_wr_nbytes = fc7AddrTable.getItem("cnfg_i2c_settings_map_slave_0_config_data_wr_nbytes").shiftDataToMask(slave_item.data_wr_nbytes)
	shifted_data_rd_nbytes = fc7AddrTable.getItem("cnfg_i2c_settings_map_slave_0_config_data_rd_nbytes").shiftDataToMask(slave_item.data_rd_nbytes)
	shifted_stop_for_rd_en = fc7AddrTable.getItem("cnfg_i2c_settings_map_slave_0_config_stop_for_rd_en").shiftDataToMask(slave_item.stop_for_rd_en)
	shifted_nack_en = fc7AddrTable.getItem("cnfg_i2c_settings_map_slave_0_config_nack_en").shiftDataToMask(slave_item.nack_en)  

	final_command = shifted_i2c_address + shifted_register_address_nbytes + shifted_data_wr_nbytes + shifted_data_rd_nbytes + shifted_stop_for_rd_en + shifted_nack_en

	return final_command

# setting the i2c slave map
def SetSlaveMap():

	# set the values
	# --- SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en) --
	i2c_slave_map[0].SetValues(0b1000001, 1, 1, 1, 1, 1, "CBC", "CBC0")
	i2c_slave_map[1].SetValues(0b1000010, 1, 1, 1, 1, 1, "CBC", "CBC1")

	# updating the slave id table
	print "---> Updating the Slave ID Map"
	for slave_id in range(2):
		fc7.write("cnfg_i2c_settings_map_slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))

# this method overrides the number of the data bytes to be written/read - used for sequential data read/write
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


#####################################################
## -------------- Program Execution -------------- ##
#####################################################

# Reset the board
#print "---> Resetting the d19c board"
#SendCommand_CTRL("global_reset")
#sleep(1)

# loads the slave map (needs to be done after each reset of the d19c)
#SetSlaveMap()

# normal i2c read write transactions
#SendCommand_I2C(command, hybrid_id, chip_id, page, read, register_address, data, ReadBack)
# command - command type, 0 - write to certain chip, hybrid; 1 - write to all chips on hybrid; 2 - write to all chips/hybrids (same for READ)
# define some standart things
#command_type = 0
#read = 1
#write = 0
#readback = 0

## standard i2c read/write section

# standard read
#SendCommand_I2C(command_type, 0, 0, 0, read, 1, 0, readback)
# standard write
#SendCommand_I2C(command_type, 0, 0, 0, write, 1, 20, readback)
# standard read again to check
#SendCommand_I2C(command_type, 0, 0, 0, read, 1, 0, readback)

# read chip data
#sleep(1)
#ReadChipDataNEW()

## sequential i2c read/write section

# set the number of data bytes so sequentialy read/write
#SetNumberOfDataBytes(0, 4, 4)

# first register to read/write
#first_register = 1

# combine words in array, has to match the size of write set by SetNumberOfDataBytes
#words = np.array([0x01,0x02,0x03,0x04])

# seq read
#SendCommand_I2C(command_type, 0, 0, 0, read, first_register, 0, readback)
# seq write (needs to be merged with normal method when checked
#SendCommand_I2C_SeqWrite(command_type, 0, 0, first_register, words)
# seq read again to check
#SendCommand_I2C(command_type, 0, 0, 0, read, first_register, 0, readback)

# read chip data
#sleep(1)
#ReadChipDataNEW(4)

# set the default size of data read/write
#SetDefaultNumberOfDataBytes(0)

#######






