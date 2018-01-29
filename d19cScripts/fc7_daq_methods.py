from PyChipsUser import *
import sys
import os
from ErrorHandler import *
from time import sleep
import numpy as np
fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
fc7ErrorHandler = ErrorHandler()
########################################
# IP address
########################################
f = open('./d19cScripts/ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
#############
# Combine and Send I2C Command
def SendCommand_I2C(command, hybrid_id, chip_id, page, read, register_address, data, ReadBack):

  raw_command = fc7AddrTable.getItem("ctrl_command_i2c_command_type").shiftDataToMask(command)
  raw_word0 = fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(0)
  raw_word1 = fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(1)
  raw_hybrid_id = fc7AddrTable.getItem("ctrl_command_i2c_command_hybrid_id").shiftDataToMask(hybrid_id)
  raw_chip_id = fc7AddrTable.getItem("ctrl_command_i2c_command_chip_id").shiftDataToMask(chip_id)
  raw_readback = fc7AddrTable.getItem("ctrl_command_i2c_command_readback").shiftDataToMask(ReadBack)
  raw_page = fc7AddrTable.getItem("ctrl_command_i2c_command_page").shiftDataToMask(page)
  raw_read = fc7AddrTable.getItem("ctrl_command_i2c_command_read").shiftDataToMask(read)
  raw_register = fc7AddrTable.getItem("ctrl_command_i2c_command_register").shiftDataToMask(register_address)
  raw_data = fc7AddrTable.getItem("ctrl_command_i2c_command_data").shiftDataToMask(data)

  cmd0 = raw_command + raw_word0 + raw_hybrid_id + raw_chip_id + raw_readback + raw_read + raw_page + raw_register;
  cmd1 = raw_command + raw_word1 + raw_data

  description = "Command: type = " + str(command) + ", hybrid = " + str(hybrid_id) + ", chip = " + str(chip_id)

  #print hex(cmd)
  if(read == 1):
	fc7.write("ctrl_command_i2c_command_fifo", cmd0)
  else:
	fc7.write("ctrl_command_i2c_command_fifo", cmd0)
	sleep(0.01)
	fc7.write("ctrl_command_i2c_command_fifo", cmd1)

  return description

def DataFromMask(data, mask_name):
  return fc7AddrTable.getItem(mask_name).shiftDataFromMask(data)

# Send command ctrl
def SendCommand_CTRL(name = "none"):
	if name == "none":
		print "Sending nothing"
	elif name == "global_reset":
		fc7.write("ctrl_command_global_reset", 1)
		sleep(0.5)
	elif name == "reset_trigger":
		fc7.write("ctrl_fast_reset", 1)
	elif name == "start_trigger":
		fc7.write("ctrl_fast_start", 1)
	elif name == "stop_trigger":
		fc7.write("ctrl_fast_stop", 1)
	elif name == "load_trigger_config":
		fc7.write("ctrl_fast_load_config", 1)
	elif name == "reset_i2c":
		fc7.write("ctrl_command_i2c_reset", 1)
	elif name == "reset_i2c_fifos":
		fc7.write("ctrl_command_i2c_reset_fifos", 1)
	elif name == "fast_orbit_reset":
		fc7.write("ctrl_fast_signal_orbit_reset", 1)
	elif name == "fast_fast_reset":
		fc7.write("ctrl_fast_signal_fast_reset", 1)
	elif name == "fast_trigger":
		fc7.write("ctrl_fast_signal_trigger", 1)
	elif name == "fast_test_pulse":
		fc7.write("ctrl_fast_signal_test_pulse", 1)
	elif name == "fast_i2c_refresh":
		fc7.write("ctrl_fast_signal_i2c_refresh", 1)
	elif name == "load_dio5_config":
		fc7.write("ctrl_dio5_load_config", 1)
	elif name == "load_dio5_config":
		fc7.write("ctrl_dio5_load_config", 1)
	elif name == "clear_counters":
		fc7.queueWrite("ctrl_fast_signal_orbit_reset", 1)
		fc7.queueWrite("ctrl_fast_signal_trigger", 2)
		fc7.queueRun()
	else:
		print "Unknown Command", name

# Data Readout
def to_str(i):
	return "{0:#0{1}x}".format(i,10)
def to_number(i, msb, lsb):
	return int(format(i,'032b')[32-msb:32-lsb],2)

def print_data(num_chips, packet_nbr, data):
	header_size = 6
	package_size = (header_size+(num_chips*11))
	if packet_nbr*package_size != len(data):
		print "Wrong data length"
		return
	for pkg in range(0, packet_nbr):
		print "--==========================--"
		print "-- Header Info:             --"
		print "--==========================--"
		print "\t FE_NBR: ", to_number(data[0+pkg*package_size],23,16), "BLOCK_SIZE: ", to_number(data[0+pkg*package_size],15,0)
		print "\t L1 Counter: ", to_number(data[2+pkg*package_size],23,0)
		print "\t BX Counter: ", to_number(data[3+pkg*package_size],31,0)
		print "\t TLU Trigger ID: ", to_number(data[4+pkg*package_size],23,8)

		print "\t\t", '%8s\t' % "Chip 0", '%8s\t' % "Chip 1", '%8s\t' % "Chip 2", '%8s\t' % "Chip 3", '%8s\t' % "Chip 4", '%8s\t' % "Chip 5", '%8s\t' % "Chip 6", '%8s\t' % "Chip 7"
		for j in range (0, 11):
			if j == 0:
				print "\t --==========================--"
				print "\t -- Trigger Data:            --"
				print "\t --==========================--"
			if j == 9:
				print "\t --==========================--"
				print "\t -- Stub Data:               --"
				print "\t --==========================--"

			if num_chips > 1:
				print "\t\t", to_str(data[header_size+j+pkg*package_size]), "\t",
				for i in range (1,num_chips-1):
					print to_str(data[header_size+i*11+j+pkg*package_size]), "\t",
				print to_str(data[header_size+(num_chips-1)*11+j+pkg*package_size])
			else:
				print "\t\t", to_str(data[header_size+j+pkg*package_size])

# Power initialization for FMC's
def InitFMCPower(fmc_id):
  fc7.write("system_fmc_pg_c2m",1)

  if (fmc_id == "fmc_l12"):
	fc7.write("system_fmc_l12_pwr_en",0)
	os.system("python fc7_i2c_voltage_set.py L12 p2v5");
	sleep(0.5)
	fc7.write("system_fmc_l12_pwr_en",1)

  if (fmc_id == "fmc_l8"):
	fc7.write("system_fmc_l8_pwr_en",0)
	os.system("python fc7_i2c_voltage_set.py L8 p2v5");
	sleep(0.5)
	fc7.write("system_fmc_l8_pwr_en",1)

  os.system("python fc7_i2c_voltage_get_all.py");


# Configure Fast Block
def Configure_Fast(triggers_to_accept, user_frequency, source, stubs_mask, stubs_latency):
  fc7.write("cnfg_fast_triggers_to_accept", triggers_to_accept)
  fc7.write("cnfg_fast_user_frequency", user_frequency)
  ready_source = fc7AddrTable.getItem("cnfg_fast_source").shiftDataToMask(source)
  fc7.write("cnfg_fast_source_full", ready_source)
  fc7.write("cnfg_fast_mask", stubs_mask)
  fc7.write("cnfg_fast_stub_trigger_latency", stubs_latency)
  #sleep(1)
  SendCommand_CTRL("reset_trigger")
  sleep(0.001)
  SendCommand_CTRL("load_trigger_config")
  sleep(0.001)

def Configure_TestPulse(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses):
  fc7.write("cnfg_fast_delay_after_fast_reset", delay_after_fast_reset)
  fc7.write("cnfg_fast_delay_after_test_pulse", delay_after_test_pulse)
  fc7.write("cnfg_fast_delay_before_next_pulse", delay_before_next_pulse)
  fc7.write("cnfg_fast_triggers_to_accept", number_of_test_pulses)
  fc7.write("cnfg_fast_source", 6)

  SendCommand_CTRL("load_trigger_config")
  sleep(1)

# Configure I2C
def Configure_I2C(mask):
  fc7.write("cnfg_command_i2c", fc7AddrTable.getItem("cnfg_command_i2c_mask").shiftDataToMask(mask))
  SendCommand_CTRL("reset_i2c")
  SendCommand_CTRL("reset_i2c_fifos")

###################################################################################################
# CBC Related Methods   									  #
###################################################################################################
# data needs to be shifted if the mask is not from zero
def ShiftDataToMask(mask, data):
	shiftingMask = mask
	bitShiftRequired = 0
	while (shiftingMask & 0x1) == 0:
		shiftingMask >>= 1
		bitShiftRequired += 1
	return (data & 0xff) << bitShiftRequired

# class used for setting the map of different CBC parameters
class Parameter():
	def __init__(self, page_i, reg_address_str, mask_str):
		self.page = page_i-1
		self.reg_address = int(reg_address_str,0)
		self.mask = int(mask_str,16)

# writing parameter to all cbc
def SetParameterI2C(parameter_name, data):
	# 0 - write, 1 - read
	write = 0
	read = 1
	cbc2_map = {}

	# map of needed parameters
	cbc2_map["trigger_latency"] = Parameter(1, "0x01", "FF")
	cbc2_map["hit_detect"] = Parameter(1, "0x02", "60")
	cbc2_map["vcth"] = Parameter(1,"0x0C", "FF")
	cbc2_map["test_pulse_potentiometer"] = Parameter(1,"0x0D", "FF")
	cbc2_map["test_pulse_delay_select"] = Parameter(1,"0x0E", "F8") # LSB00000MSB - minimal, LSB11001MSB - maximal
	cbc2_map["select_channel_group"] = Parameter(1,"0x0E", "07") # LSB 000 MSB
	cbc2_map["test_pulse_control"] = Parameter(1,"0x0F", "C0") # 7 - polarity (1 = positive edge); 6 - enable test pulse
	cbc2_map["mask_channels_8_1"] = Parameter(1,"0x20", "FF")

	write_data = data
	# FIXME no mask anymore
	if cbc2_map[parameter_name].mask != 255:
		fc7.write("cnfg_command_i2c_mask", cbc2_map[parameter_name].mask)
		write_data = ShiftDataToMask(cbc2_map[parameter_name].mask, data)

	SendCommand_I2C(2, 0, 0, cbc2_map[parameter_name].page, write, cbc2_map[parameter_name].reg_address, write_data, 0)
	sleep(0.5)

def CBC_Config():
	SetParameterI2C("trigger_latency", 195)
	SetParameterI2C("hit_detect", 1) # mode = single, enable = on
	SetParameterI2C("vcth", 127) #default
	SetParameterI2C("test_pulse_potentiometer", 0) # default 1.1V
	SetParameterI2C("test_pulse_delay_select", 24) # 11000
	SetParameterI2C("select_channel_group", 0)
	SetParameterI2C("test_pulse_control", 1) # polarity negative, test pulse enabled

	# unmask all channels
	i_start = 32	# 32
	i_finish = 64	# 64
	for i in range(i_start, i_finish):
		SendCommand_I2C(2, 0, 0, 0, 0, 0, i, 255, 0)
	sleep(2)

def CBC_ConfigTXT():
	# 0 - write, 1 - read
	write = 0
	read = 1

	cbc_config = np.genfromtxt('Cbc2_default_hole.txt', skip_header=2, dtype='str')

	for i in range(0, cbc_config.shape[0]): # including offset
	#for i in range(0, 52): # excluding offset
		SendCommand_I2C(2, 0, 0, int(cbc_config[i][1],0), write, int(cbc_config[i][2],0), int(cbc_config[i][4],0), 0)
	sleep(2)

###################################################################################################

# Configure DIO5
def Configure_DIO5(out_en, term_en, thresholds):
  fc7.write("cnfg_dio5_en", 1)
  for i in range (1,6):
	combined_config = fc7AddrTable.getItem("cnfg_dio5_ch1_out_en").shiftDataToMask(out_en[i-1]) + fc7AddrTable.getItem("cnfg_dio5_ch1_term_en").shiftDataToMask(term_en[i-1]) + fc7AddrTable.getItem("cnfg_dio5_ch1_threshold").shiftDataToMask(thresholds[i-1])
	fc7.write(("cnfg_dio5_ch"+str(i)+"_sel"), combined_config)

  sleep(0.5)
  SendCommand_CTRL("load_dio5_config")
  sleep(0.5)


def ReadStatus(name = "Current Status"):
  print "============================"
  print name,":"

  error_counter = fc7.read("stat_error_counter")
  print "   -> Error Counter: ", error_counter
  if error_counter > 0:
	  for i in range (0,error_counter):
		  error_full = fc7.read("stat_error_full")
		  error_block_id = DataFromMask(error_full,"stat_error_block_id");
		  error_code = DataFromMask(error_full,"stat_error_code");
		  print "   -> ",
		  fc7ErrorHandler.getErrorDescription(error_block_id,error_code)
  else:
	print "   -> No Errors"
  temp_source = fc7.read("stat_fast_fsm_source")
  temp_source_name = "Unknown"
  if temp_source == 1:
	temp_source_name = "L1-Trigger"
  elif temp_source == 2:
	temp_source_name = "Stubs"
  elif temp_source == 3:
	temp_source_name = "User Frequency"
  elif temp_source == 4:
	temp_source_name = "TLU"
  elif temp_source == 5:
	temp_source_name = "EXT DIO5"
  elif temp_source == 6:
	temp_source_name = "Test Pulse Trigger"
  elif temp_source == 7:
	temp_source_name = "Antenna Trigger"
  print "   -> trigger source:", temp_source_name
  temp_state = fc7.read("stat_fast_fsm_state")
  temp_state_name = "Unknown"
  if temp_state == 0:
	temp_state_name = "Idle"
  elif temp_state == 1:
	temp_state_name = "Running"
  elif temp_state == 2:
	temp_state_name = "Paused. Waiting for readout"
  print "   -> trigger state:", temp_state_name
  print "   -> trigger configured:", fc7.read("stat_fast_fsm_configured")
  print	"   -> --------------------------------"
  print "   -> i2c commands fifo empty:", fc7.read("stat_command_i2c_fifo_commands_empty")
  print "   -> i2c replies fifo empty:", fc7.read("stat_command_i2c_fifo_replies_empty")
  print "   -> i2c nreplies available:", fc7.read("stat_command_i2c_nreplies_present")
  print "   -> i2c fsm state:", fc7.read("stat_command_i2c_fsm")
  print	"   -> --------------------------------"
  print	"   -> dio5 not ready:", fc7.read("stat_dio5_not_ready")
  print	"   -> dio5 error:", fc7.read("stat_dio5_error")
  print "============================"

def CheckClockFrequencies():
  print "IPBus Clock Rate: ", fc7.read("stat_rate_ipb")/10000.0, "MHz"
  print "40MHz Clock Rate: ", fc7.read("stat_rate_40mhz")/10000.0, "MHz"
  print "Trigger Rate: ", fc7.read("stat_rate_trigger")/10.0, "KHz"
  print "Clock 3 Rate: ", fc7.read("stat_rate_3")/10000.0, "MHz"

def ReadChipData(checking, expected_value):
  numberOfReads = 0
  print "Reading Out Data:"
  print "   =========================================================================================="
  print "   | Hybrid ID             || Chip ID             || Register                || DATA         |"
  print "   =========================================================================================="

  while fc7.read("stat_command_i2c_fifo_replies_empty") == 0:
	  numberOfReads = numberOfReads + 1
	  reply = fc7.read("ctrl_command_i2c_reply_fifo")
	  hybrid_id = DataFromMask(reply, "ctrl_command_i2c_reply_hybrid_id")
	  chip_id = DataFromMask(reply, "ctrl_command_i2c_reply_chip_id")
	  data = DataFromMask(reply, "ctrl_command_i2c_reply_data")
	  register = DataFromMask(reply, "ctrl_command_i2c_reply_register")
	  #print bin(fc7.read("ctrl_i2c_command_fifo"))
	  #print bin(reply)[4:12]
	  print '   | %s %-12i || %s %-12i || %s %-12s || %-12s |' % ("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4])
	  if(checking and data != expected_value and register != 0):
		 print '!!!!!!!!!!!!!!!!!!!!!!! problem on write-read sequence. Expected value is: ' , expected_value
		 sys.exit()
	  print "    -----------------------------------------------------------------------------------------"
  print "   =========================================================================================="
  print "the number of reads is = ", numberOfReads

# tests i2c master
def I2CTester():
	###############
	## i2c config #
	###############
	# command_i2c: 0 - send command to certain hybrid/chip, 1 - send command to all chips on hybrid, 2 - send command to all chips on all hybrids
	#command_i2c = 0
	#hybrid_id = 0
	#chip_id = 0
	#page = 0
	# 0 - write, 1 - read
	write = 0
	read = 1
	#register = 2
	#data = 7
	ReadBack = 0
	################

	ReadStatus("Before I2C Configuration")
	Configure_I2C(255)
	ReadStatus("After I2C Configuration")

	num_i2c_registersPage1 = 35
	num_i2c_registersPage2 = 2
	   #                       i2c_command , hybrid_id ,  chip_id, page , read , register_address , data;

	for i in range(0, num_i2c_registersPage1):
		SendCommand_I2C(          2,         0,       0,    0, read,        1,    10, ReadBack)
	for i in range(0, num_i2c_registersPage2):
		SendCommand_I2C(          2,         0,       0,    1, read,        i,    10, ReadBack)
	for i in range(1, num_i2c_registersPage1):
		SendCommand_I2C(          2,         0,       0,    0, write,       i,    5, ReadBack)
	for i in range(1, num_i2c_registersPage2):
		SendCommand_I2C(          2,         0,       15,    1, write,       i,    7, ReadBack)
	for i in range(0, num_i2c_registersPage1):
		SendCommand_I2C(          2,         0,       0,    0, read,        i,    10, ReadBack)
	for i in range(0, num_i2c_registersPage2):
		SendCommand_I2C(          2,         0,       0,    1, read,        i,    10, ReadBack)

	sleep(1)

	ReadStatus("After Send Command")
	ReadChipData()
	ReadStatus("After Read Reply")

# dio5 testing
def DIO5Tester(fmc_id):
	InitFMCPower(fmc_id)
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

	Configure_DIO5(out_en, term_en, thresholds)
	ReadStatus("After DIO5 Config")
