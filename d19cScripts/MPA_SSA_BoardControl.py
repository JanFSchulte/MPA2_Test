# basic d19c methods include
from d19cScripts.fc7_daq_methods import *

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
		self.chip_name = "UNKNOWN"
	def SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en, chip_name):
		self.i2c_address = i2c_address
        	self.register_address_nbytes = register_address_nbytes
		self.data_wr_nbytes = data_wr_nbytes
		self.data_rd_nbytes = data_rd_nbytes
		self.stop_for_rd_en = stop_for_rd_en
		self.nack_en = nack_en
		self.chip_name = chip_name

# encode slave map item:
def EncodeSlaveMapItem(slave_item):

	# this peace of code just shifts the data, also checks if it fits the field
	shifted_i2c_address = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_i2c_address").shiftDataToMask(slave_item.i2c_address)
	shifted_register_address_nbytes = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_register_address_nbytes").shiftDataToMask(slave_item.register_address_nbytes)
	shifted_data_wr_nbytes = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_data_wr_nbytes").shiftDataToMask(slave_item.data_wr_nbytes)
	shifted_data_rd_nbytes = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_data_rd_nbytes").shiftDataToMask(slave_item.data_rd_nbytes)
	shifted_stop_for_rd_en = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_stop_for_rd_en").shiftDataToMask(slave_item.stop_for_rd_en)
	shifted_nack_en = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_nack_en").shiftDataToMask(slave_item.nack_en)

	final_command = shifted_i2c_address + shifted_register_address_nbytes + shifted_data_wr_nbytes + shifted_data_rd_nbytes + shifted_stop_for_rd_en + shifted_nack_en

	return final_command

# setting the i2c slave map
def SetSlaveMap(verbose = 1):
	# define the map itself
	i2c_slave_map = [I2C_SlaveMapItem() for i in range(16)]

	# set the values
	# --- SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en) --
	i2c_slave_map[0].SetValues(0b1110000, 0, 1, 1, 0, 1, "PCA9646")
	i2c_slave_map[1].SetValues(0b0100000, 0, 1, 1, 0, 1, "PCF8574")
	i2c_slave_map[2].SetValues(0b0100100, 0, 1, 1, 0, 1, "PCF8574")
	i2c_slave_map[3].SetValues(0b0010100, 0, 2, 3, 0, 1, "LTC2487") # ADC
	i2c_slave_map[4].SetValues(0b1001000, 1, 2, 2, 0, 0, "DAC7678")
	i2c_slave_map[5].SetValues(0b1000000, 1, 2, 2, 0, 1, "INA226")
	i2c_slave_map[6].SetValues(0b1000001, 1, 2, 2, 0, 1, "INA226")
	i2c_slave_map[7].SetValues(0b1000010, 1, 2, 2, 0, 1, "INA226")
	i2c_slave_map[8].SetValues(0b1000100, 1, 2, 2, 0, 1, "INA226")
	i2c_slave_map[9].SetValues(0b1000101, 1, 2, 2, 0, 1, "INA226")
	i2c_slave_map[10].SetValues(0b1000110, 1, 2, 2, 0, 1, "INA226")
	i2c_slave_map[11].SetValues(0b1000000, 2, 1, 1, 1, 0, "MPA")
	i2c_slave_map[12].SetValues(0b0100000, 2, 1, 1, 1, 0, "SSA")
	i2c_slave_map[15].SetValues(0b1011111, 1, 1, 1, 1, 0, "CBC3")


	# updating the slave id table
	if verbose: print "---> Updating the Slave ID Map"
	for slave_id in range(16):
		fc7.write("cnfg_mpa_ssa_board_slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))
		if verbose: print "Writing","cnfg_mpa_ssa_board_slave_" + str(slave_id) + "_config", hex(EncodeSlaveMapItem(i2c_slave_map[slave_id]))

# i2c masters configuration
def Configure_MPA_SSA_I2C_Master(enabled, frequency=4, verbose = 1):
	## ------ if enabled=1, enables the mpa ssa i2c master and disables the main one
	## ------ frequency: 0 - 0.1MHz, 1 - 0.2MHz, 2 - 0.4MHz, 3 - 0.8MHz, 4 - 1MHz, 5 - 2 MHz, 6 - 4MHz, 7 - 5MHz, 8 - 8MHz, 9 - 10MHz

	if enabled > 0:
		if verbose: print "---> Enabling the MPA SSA Board I2C master"
	else:
		if verbose: print "---> Disabling the MPA SSA Board I2C master"

	# sets the main CBC, MPA, SSA i2c master
	fc7.write("cnfg_phy_i2c_master_en", int(not enabled))
	# sets the MPA SSA board I2C master
	fc7.write("cnfg_mpa_ssa_board_i2c_master_en", enabled)

	# sets the frequency
	fc7.write("cnfg_mpa_ssa_board_i2c_freq", frequency)

	# wait a bit
	sleep(0.1)

	# now reset all the I2C related stuff
	fc7.write("ctrl_command_i2c_reset", 1)
	fc7.write("ctrl_command_i2c_reset_fifos", 1)
	fc7.write("ctrl_mpa_ssa_board_reset", 1)
	sleep(0.1)

def Send_MPA_SSA_I2C_Command(slave_id, board_id, read, register_address, data, verbose = 1):

	# this peace of code just shifts the data, also checks if it fits the field
	# general
	shifted_command_type = fc7AddrTable.getItem("mpa_ssa_i2c_request_command_type").shiftDataToMask(8)
	shifted_word_id_0 = fc7AddrTable.getItem("mpa_ssa_i2c_request_word_id").shiftDataToMask(0)
	shifted_word_id_1 = fc7AddrTable.getItem("mpa_ssa_i2c_request_word_id").shiftDataToMask(1)
	# command specific
	shifted_slave_id = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_slave_id").shiftDataToMask(slave_id)
	shifted_board_id = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_board_id").shiftDataToMask(board_id)
	shifted_read = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_read").shiftDataToMask(read)
	shifted_register_address = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_register").shiftDataToMask(register_address)
	shifted_data = fc7AddrTable.getItem("mpa_ssa_i2c_request_word1_data").shiftDataToMask(data)

	# composing the word
	word_0 = shifted_command_type + shifted_word_id_0 + shifted_slave_id + shifted_board_id + shifted_read + shifted_register_address
	word_1 = shifted_command_type + shifted_word_id_1 + shifted_data
	#print bin(shifted_command_type)
	#print bin(shifted_word_id_0)
	#print bin(shifted_slave_id)
	if verbose:
		print "ctrl_command_i2c_command_fifo"
		print hex(word_0)
		print hex(word_1)

	# writing the command
	fc7.write("ctrl_command_i2c_command_fifo", word_0)
	fc7.write("ctrl_command_i2c_command_fifo", word_1)

	# wait for the reply to come back
	while fc7.read("stat_command_i2c_fifo_replies_empty") > 0:
		if verbose:
			ReadStatus()
			sleep(0.1)

	# get the reply
	reply = fc7.read("ctrl_command_i2c_reply_fifo")

	reply_slave_id = DataFromMask(reply, "mpa_ssa_i2c_reply_slave_id")
	reply_board_id = DataFromMask(reply, "mpa_ssa_i2c_reply_board_id")
	reply_err = DataFromMask(reply, "mpa_ssa_i2c_reply_err")
	reply_data = DataFromMask(reply, "mpa_ssa_i2c_reply_data")

	# print full word
	#print "Full Reply Word: ", hex(reply)

	# check the data
	if reply_err == 1:
		print "ERROR! Error flag is set to 1. The data is treated as the error code."
		print "Error code: ", hex(reply_data)
	elif reply_slave_id != slave_id:
		print "ERROR! Slave ID doesn't correspond to the one sent"
	elif reply_board_id != board_id:
		print "ERROR! Board ID doesn't correspond to the one sent"

	else:
		if read == 1:
			if verbose: print "Data that was read is: ", hex(reply_data)
			return reply_data
		else:
			if verbose: print "Successful write transaction"

##----- end methods definition

##----- begin constants
#read = 1
#write = 0
#cbc3 = 15
##----- end constants

#####################################################
## -------------- Program Execution -------------- ##
#####################################################

# Reset the board
#print "---> Resetting the d19c board"
#SendCommand_CTRL("global_reset")
#sleep(1)

# loads the slave map (needs to be done after each reset of the d19c)
#SetSlaveMap()
# sets the mpa/ssa i2c master config
#Configure_MPA_SSA_I2C_Master(1)

#######

# send test read command
#Send_MPA_SSA_I2C_Command(cbc3, 0, read, 1, 0)

# send write command to change the value of the register
#Send_MPA_SSA_I2C_Command(cbc3, 0, write, 1, 0xc8)

# send read again
#Send_MPA_SSA_I2C_Command(cbc3, 0, read, 1, 0)

#######

# disables the mpa/ssa i2c master
#Configure_MPA_SSA_I2C_Master(0)
