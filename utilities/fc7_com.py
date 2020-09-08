import numpy as np
import time
import sys
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm
from scipy.interpolate import BSpline as interpspline
from multiprocessing import Process
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from datetime import datetime

class I2C_MainSlaveMapItem:
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

class fc7_com():
	def __init__(self, fc7_if, fc7AddrTable):
		self.fc7 = fc7_if
		self.fc7AddrTable = fc7AddrTable
		self.set_invert(False)
		self.chip_adr = [0,0]
		self.enable = [1,1]
		self.update_active_readout_chip()

	def compose_fast_command(self, duration = 0, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 0):
		encode_resync = self.fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(resync_en)
		encode_l1a = self.fc7AddrTable.getItem("ctrl_fast_signal_trigger").shiftDataToMask(l1a_en)
		encode_cal_pulse = self.fc7AddrTable.getItem("ctrl_fast_signal_test_pulse").shiftDataToMask(cal_pulse_en)
		encode_bc0 = self.fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(bc0_en)
		encode_duration = self.fc7AddrTable.getItem("ctrl_fast_signal_duration").shiftDataToMask(duration)
		self.write("ctrl_fast", encode_resync + encode_l1a + encode_cal_pulse + encode_bc0 + encode_duration)

	def update_active_readout_chip(self):
		self.active_chip = self.read("cnfg_phy_slvs_chip_switch")
		return self.active_chip

	def get_active_readout_chip(self):
		return self.active_chip

	def set_active_readout_chip(self, ID):
		if(ID != self.active_chip):
			self.write("cnfg_phy_slvs_chip_switch", ID)
			self.update_active_readout_chip()
			print("->\tReadout switched to SSA-{:d}".format(ID))
		return self.active_chip

	def set_invert(self, mode=False):
		self.invert = mode

	def start_counters_read(self, duration = 0):
		self.compose_fast_command(duration, resync_en = 1, l1a_en = 0, cal_pulse_en = 0, bc0_en = 1)

	def send_resync(self):
		self.SendCommand_CTRL("fast_fast_reset")

	def send_trigger(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 0)

	def open_shutter(self,duration = 0, repeat=1):
		for i in range(repeat):
			self.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 0)

	def send_test(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 0, cal_pulse_en = 1, bc0_en = 0)

	def orbit_reset(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 1)

	def close_shutter(self,duration = 0, repeat=1):
		for i in range(repeat):
			self.compose_fast_command(duration, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 1)

	def reset(self):
		self.SendCommand_CTRL("global_reset")

	def clear_counters(self,duration = 0, repeat = 1):
		for i in range(repeat):
			self.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 1)

	def set_chip_id(self, index = 0, address = 0):
		self.chip_adr[index] = int('{:03b}'.format(address & 0b111)[::-1], 2)
		self._write_id_enable()
		#print("->\tChip 0 address set to: {:2d}".format(self.chip_adr[0] & 0b111))
		#print("->\tChip 1 address set to: {:2d}".format(self.chip_adr[1] & 0b111))

	def disable_chip(self, index = 0):
		self.enable[index] = 0
		self._write_id_enable()

	def enable_chip(self, index = 0):
		self.enable[index] = 1
		self._write_id_enable()

	def reset_chip(self, index = 0):
		self.disable_chip()
		time.sleep(0.5)
		self.enable_chip()

	def _write_id_enable(self):
		val = ((self.chip_adr[1] & 0b111) << 5) | ((self.chip_adr[0] & 0b111) << 1)
		val = val | ((self.enable[1] & 0b1) << 4)  | ((self.enable[0] & 0b1) << 0)
		time.sleep(0.01); self.Configure_MPA_SSA_I2C_Master(1, 2, verbose=0);
		time.sleep(0.01); self.Send_MPA_SSA_I2C_Command(0, 0, 0, 0, 0x02, verbose=0); # route to 2nd PCF8574
		time.sleep(0.01); self.Send_MPA_SSA_I2C_Command(1, 0, 0, 0, val, verbose=0);  # set reset bit
		time.sleep(0.01);
		#print(bin(val))
		self.activate_I2C_chip(verbose=0)

	def activate_I2C_chip(frequency = 0, verbose = 1):
		i2cmux = 0
		write = 0
		self.SetSlaveMap(verbose = verbose)
		self.Configure_MPA_SSA_I2C_Master(1, frequency, verbose = verbose)
		self.Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x04, verbose = verbose) #enable only MPA-SSA chip I2C
		self.Configure_MPA_SSA_I2C_Master(0, frequency, verbose = verbose)
		self.SetMainSlaveMap(verbose = verbose)

	def write(self, p1, p2, p3 = 0):
		cnt = 0; ex = '';
		while cnt < 4:
			try:
				return self.fc7.write(p1, p2, p3)
			except:
				print('=>  FC7 Communication error - fc7_write')
				ex = sys.exc_info()
				time.sleep(0.1)
				cnt += 1
		print(ex)

	def read(self, p1, p2 = 0):
		cnt = 0; ex = '';
		while cnt < 4:
			try:
				return self.fc7.read(p1, p2)
			except:
				ex = sys.exc_info()
				print('=>  \tFC7 Communication error - fc7_read')
				time.sleep(0.1)
				cnt += 1
		print(ex)

	def blockRead(self, p1, p2, p3 = 0):
		cnt = 0; ex = '';
		rt = False; ar = [];
		while cnt < 4:
			try:
				rt = self.fc7.blockRead(p1, p2, p3)
				break
			except:
				ex = sys.exc_info()
				print('=>  \tFC7 Communication error - fc7_read_block')
				time.sleep(0.1)
				cnt += 1
		if(cnt>=4):
			print(ex)
			return
		else:
			if(self.invert and rt):
				for word in rt:
					ar.append( ~np.uint32(word) )
			else:
				ar = rt
			return ar



	def fifoRead(self, p1, p2, p3 = 0):
		cnt = 0; ex = '';
		while cnt < 4:
			try:
				return self.fc7.fifoRead(p1, p2, p3)
			except:
				ex = sys.exc_info()
				print('=>  \tFC7 Communication error - fc7_read_fifo')
				time.sleep(0.1)
				cnt += 1
		print(ex)

	def SendCommand_CTRL(self, p1):
		cnt = 0; ex = '';
		while cnt < 4:
			try:
				return SendCommand_CTRL(p1)
			except:
				ex = sys.exc_info()
				print('=>  \tFC7 Communication error - SendCommand_CTRL')
				time.sleep(0.1)
				cnt += 1
		print(ex)

	def Configure_MPA_SSA_I2C_Master(self, enabled, frequency=4, verbose = 1):
		## ------ if enabled=1, enables the mpa ssa i2c master and disables the main one
		## ------ frequency: 0 - 0.1MHz, 1 - 0.2MHz, 2 - 0.4MHz, 3 - 0.8MHz, 4 - 1MHz, 5 - 2 MHz, 6 - 4MHz, 7 - 5MHz, 8 - 8MHz, 9 - 10MHz
		if enabled > 0:
			if verbose: print("---> Enabling the MPA SSA Board I2C master")
		else:
			if verbose: print("---> Disabling the MPA SSA Board I2C master")
		# sets the main CBC, MPA, SSA i2c master
		self.fc7.write("cnfg_phy_i2c_master_en", int(not enabled))
		# sets the MPA SSA board I2C master
		self.fc7.write("cnfg_mpa_ssa_board_i2c_master_en", enabled)
		# sets the frequency
		self.fc7.write("cnfg_mpa_ssa_board_i2c_freq", frequency)
		# wait a bit
		time.sleep(0.1)
		# now reset all the I2C related stuff
		self.fc7.write("ctrl_command_i2c_reset", 1)
		self.fc7.write("ctrl_command_i2c_reset_fifos", 1)
		self.fc7.write("ctrl_mpa_ssa_board_reset", 1)
		time.sleep(0.1)


	def Send_MPA_SSA_I2C_Command(self, slave_id, board_id, read, register_address, data, verbose = 1):
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
		#print(bin(shifted_command_type))
		#print(bin(shifted_word_id_0))
		#print(bin(shifted_slave_id))
		if verbose:
			print("ctrl_command_i2c_command_fifo")
			print(hex(word_0))
			print(hex(word_1))
		# writing the command
		self.fc7.write("ctrl_command_i2c_command_fifo", word_0)
		self.fc7.write("ctrl_command_i2c_command_fifo", word_1)
		# wait for the reply to come back
		while self.fc7.read("stat_command_i2c_fifo_replies_empty") > 0:
			if verbose:
				self.ReadStatus()
				time.sleep(0.1)
		# get the reply
		reply = self.fc7.read("ctrl_command_i2c_reply_fifo")
		reply_slave_id = DataFromMask(reply, "mpa_ssa_i2c_reply_slave_id")
		reply_board_id = DataFromMask(reply, "mpa_ssa_i2c_reply_board_id")
		reply_err = DataFromMask(reply, "mpa_ssa_i2c_reply_err")
		reply_data = DataFromMask(reply, "mpa_ssa_i2c_reply_data")
		# print(full word)
		#print("Full Reply Word: ", hex(reply))
		# check the data
		if reply_err == 1:
			print("ERROR! Error flag is set to 1. The data is treated as the error code.")
			print("Error code: " + hex(reply_data))
		elif reply_slave_id != slave_id:
			print("ERROR! Slave ID doesn't correspond to the one sent")
		elif reply_board_id != board_id:
			print("ERROR! Board ID doesn't correspond to the one sent")
		else:
			if read == 1:
				if verbose: print("Data that was read is: " + hex(reply_data))
				return reply_data
			else:
				if verbose: print("Successful write transaction")

	def activate_I2C_chip(self, frequency = 0, verbose = 1):
		i2cmux = 0
		write = 0
		self.SetSlaveMap(verbose = verbose)
		self.Configure_MPA_SSA_I2C_Master(1, frequency, verbose = verbose)
		self.Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x04, verbose = verbose) #enable only MPA-SSA chip I2C
		self.Configure_MPA_SSA_I2C_Master(0, frequency, verbose = verbose)
		self.SetMainSlaveMap(verbose = verbose)

	def SetMainSlaveMap(self, verbose = 1):
		self.i2c_slave_map = [I2C_MainSlaveMapItem() for i in range(31)]
		# define the map itself
		#i2c_slave_map = [I2C_MainSlaveMapItem() for i in range(31)]
		# set the values
		# --- SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en) --
		i2c_slave_map[0].SetValues(0b1000000, 2, 1, 1, 1, 0, "MPA",  "MPA0")
		i2c_slave_map[1].SetValues(0b0100001, 2, 1, 1, 1, 0, "SSA",  "SSA0")
		i2c_slave_map[2].SetValues(0b0100111, 2, 1, 1, 1, 0, "SSA1", "SSA1")
		# updating the slave id table
		if verbose:
			print("---> Updating the Slave ID Map")
		for slave_id in range(3):
			self.fc7.write("cnfg_i2c_settings_map_slave_" + str(slave_id) + "_config", EncodeMainSlaveMapItem(i2c_slave_map[slave_id]))
			if verbose:
				print("Writing","cnfg_i2c_settings_map_slave_" + str(slave_id) + "_config", hex(EncodeMainSlaveMapItem(i2c_slave_map[slave_id])))

	def SetSlaveMap(self, verbose = 1):
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
		if verbose: print("---> Updating the Slave ID Map")
		for slave_id in range(16):
			self.fc7.write("cnfg_mpa_ssa_board_slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))
			if verbose:
				print("Writing","cnfg_mpa_ssa_board_slave_" + str(slave_id) + "_config", hex(EncodeSlaveMapItem(i2c_slave_map[slave_id])))


	def ReadStatus(self, name = "Current Status"):
		print("============================")
		print(name + ":")
		error_counter = fc7.read("stat_error_counter")
		print("   -> Error Counter: " + str(error_counter))
		if error_counter > 0:
			for i in range (0,error_counter):
				error_full = fc7.read("stat_error_full")
				error_block_id = DataFromMask(error_full,"stat_error_block_id");
				error_code = DataFromMask(error_full,"stat_error_code");
				print("   -> ")
				fc7ErrorHandler.getErrorDescription(error_block_id,error_code)
		else:
			print("   -> No Errors")
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
		print("   -> trigger source:" + str(temp_source_name))
		temp_state = fc7.read("stat_fast_fsm_state")
		temp_state_name = "Unknown"
		if temp_state == 0:
			temp_state_name = "Idle"
		elif temp_state == 1:
			temp_state_name = "Running"
		elif temp_state == 2:
			temp_state_name = "Paused. Waiting for readout"
		print("   -> trigger state:" + str(temp_state_name))
		print("   -> trigger configured:"  + str(fc7.read("stat_fast_fsm_configured")))
		print(   "   -> --------------------------------")
		print("   -> i2c commands fifo empty:" + str( fc7.read("stat_command_i2c_fifo_commands_empty")))
		print("   -> i2c replies fifo empty:" + str( fc7.read("stat_command_i2c_fifo_replies_empty")))
		print("   -> i2c nreplies available:" + str( fc7.read("stat_command_i2c_nreplies_present")))
		print("   -> i2c fsm state:" + str( fc7.read("stat_command_i2c_fsm") ))
		print(   "   -> --------------------------------")
		print(   "   -> dio5 not ready:" + str(fc7.read("stat_dio5_not_ready")))
		print(   "   -> dio5 error:" + str( fc7.read("stat_dio5_error")))
		print("============================")
