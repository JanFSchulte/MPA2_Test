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
from myScripts.Utilities import *
from utilities.tbsettings import *

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
		#self.update_active_readout_chip()
		self.active_chip = 0

	def compose_fast_command(self, duration = 0, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 0):
		encode_resync = self.fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_reset").shiftDataToMask(resync_en)
		encode_l1a = self.fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_trigger").shiftDataToMask(l1a_en)
		encode_cal_pulse = self.fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_test_pulse").shiftDataToMask(cal_pulse_en)
		encode_bc0 = self.fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_orbit_reset").shiftDataToMask(bc0_en)
		encode_duration = self.fc7AddrTable.getItem("fc7_daq_ctrl.fast_command_block.control.fast_duration").shiftDataToMask(duration)
		self.write("fc7_daq_ctrl.fast_command_block", encode_resync + encode_l1a + encode_cal_pulse + encode_bc0 + encode_duration)

	def DataFromMask(self, data, mask_name):
		return self.fc7AddrTable.getItem(mask_name).shiftDataFromMask(data)

	def update_active_readout_chip(self):
		self.active_chip = self.read("cnfg_phy_slvs_chip_switch")
		return self.active_chip

	def get_active_readout_chip(self):
		return self.active_chip

	def set_active_readout_chip(self, ID, display=True):
		if(ID != self.active_chip):
			self.write("cnfg_phy_slvs_chip_switch", ID)
			self.update_active_readout_chip()
			if(display): print("->  Readout switched to SSA-{:d}".format(ID))
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
		try:
			self._write_id_enable()
		except:
			pass
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
		time.sleep(0.2)
		self.enable_chip()
		self.activate_I2C_chip(verbose=0)

	def _write_id_enable(self):
		val = ((self.chip_adr[1] & 0b111) << 5) | ((self.chip_adr[0] & 0b111) << 1)
		val = val | ((self.enable[1] & 0b1) << 4)  | ((self.enable[0] & 0b1) << 0)
		time.sleep(0.01); self.Configure_MPA_SSA_I2C_Master(1, 2, verbose=0);
		time.sleep(0.01); self.Send_MPA_SSA_I2C_Command(0, 0, 0, 0, 0x02, verbose=0, note='route to 2nd PCF8574'); # route to 2nd PCF8574
		time.sleep(0.01); self.Send_MPA_SSA_I2C_Command(1, 0, 0, 0, val, verbose=0, note='set reset bit');  # set reset bit
		time.sleep(0.01); self.Send_MPA_SSA_I2C_Command(1, 0, 0, 0, val, verbose=0, note='set reset bit');  # set reset bit
		time.sleep(0.01);
		#print(bin(val))
		#self.activate_I2C_chip(verbose=0)

	def activate_I2C_chip(self, frequency = 0, verbose = 1):
		i2cmux = 0
		write = 0
		#print('activate_I2C_chip')
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

	def blockWrite(self, p1, p2, p3 = 0):
		cnt = 0; ex = '';
		rt = False; ar = [];
		while cnt < 4:
			try:
				rt = self.fc7.blockWrite(p1, p2, p3)
				break
			except:
				ex = sys.exc_info()
				print('=>  \tFC7 Communication error - fc7_write_block')
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
		self.fc7.write("fc7_daq_cnfg.physical_interface_block.i2c.master_en", int(not enabled))
		# sets the MPA SSA board I2C master
		self.fc7.write("fc7_daq_cnfg.mpa_ssa_board_block.i2c_master_en", enabled)
		# sets the frequency
		self.fc7.write("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq", frequency)
		# wait a bit
		time.sleep(0.1)
		# now reset all the I2C related stuff
		self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.control.reset", 1)
		self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.control.reset_fifos", 1)
		self.fc7.write("fc7_daq_ctrl.mpa_ssa_board_block.reset", 1)
		time.sleep(0.1)


	def Send_MPA_SSA_I2C_Command(self, slave_id, board_id, read, register_address, data, verbose = 1, note = ''):
		# this peace of code just shifts the data, also checks if it fits the field
		# general
		"""new addresstable
		shifted_command_type = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.command_type").shiftDataToMask(8)
		shifted_word_id_0 = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word_id").shiftDataToMask(0)
		shifted_word_id_1 = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word_id").shiftDataToMask(1)
		# command specific
		shifted_slave_id = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_slave_id").shiftDataToMask(slave_id)
		shifted_board_id = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_board_id").shiftDataToMask(board_id)
		shifted_read = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_read").shiftDataToMask(read)
		shifted_register_address = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_register").shiftDataToMask(register_address)
		shifted_data = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word1_data").shiftDataToMask(data)
		"""
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
			print("fc7_daq_ctrl.command_processor_block.i2c.command_fifo")
			print(hex(word_0))
			print(hex(word_1))
		# writing the command
		time.sleep(0.001);
		self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", word_0); time.sleep(0.001);
		self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", word_1); time.sleep(0.001);
		# wait for the reply to come back
		rr = 1
		while(rr > 0):
			time.sleep(0.001)
			rr = self.fc7.read("fc7_daq_stat.command_processor_block.i2c.reply_fifo.empty")
			if verbose:
				time.sleep(0.001);
				self.ReadStatus()
				time.sleep(0.1)
		# get the reply
		time.sleep(0.001);
		reply = self.fc7.read("fc7_daq_ctrl.command_processor_block.i2c.reply_fifo")
		time.sleep(0.001);

		reply_slave_id = self.DataFromMask(reply, "mpa_ssa_i2c_reply_slave_id")
		reply_board_id = self.DataFromMask(reply, "mpa_ssa_i2c_reply_board_id")
		reply_err = self.DataFromMask(reply, "mpa_ssa_i2c_reply_err")
		reply_data = self.DataFromMask(reply, "mpa_ssa_i2c_reply_data")

		'''new addresstable
		reply_slave_id = self.DataFromMask(reply, "fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_reply.slave_id")
		reply_board_id = self.DataFromMask(reply, "fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_reply.board_id")
		reply_err = self.DataFromMask(reply, "fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_reply.err")
		reply_data = self.DataFromMask(reply, "fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_reply.data")
		'''
		# print(full word)
		#print("Full Reply Word: ", hex(reply))
		# check the data
		if reply_err == 1:
			utils.print_warning("ERROR! Error flag is set to 1. The data is treated as the error code. ")
			utils.print_warning("Send_MPA_SSA_I2C_Command slave_id [{:s}] board_id={:d}, read={:d}, register_address={:d}, data={:d}".format(note, board_id, read, register_address, data))
			utils.print_warning("Error code: " + hex(reply_data))
		elif reply_slave_id != slave_id:
			utils.print_warning("ERROR! Slave ID doesn't correspond to the one sent")
		elif reply_board_id != board_id:
			utils.print_warning("ERROR! Board ID doesn't correspond to the one sent")
		else:
			if read == 1:
				if verbose: print("Data that was read is: " + hex(reply_data))
				return reply_data
			else:
				if verbose: print("Successful write transaction")

	def SetMainSlaveMap(self, verbose = 1):
		self.i2c_slave_map = [I2C_MainSlaveMapItem() for i in range(31)]
		# define the map itself
		#i2c_slave_map = [I2C_MainSlaveMapItem() for i in range(31)]
		# set the values
		# --- SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en) --
		i2c_slave_map[0].SetValues(tbconfig.MPA_ADR[0], 2, 1, 1, 1, 0, "MPA",  "MPA0")
		i2c_slave_map[1].SetValues(tbconfig.SSA_ADR[0], 2, 1, 1, 1, 0, "SSA",  "SSA0")
		i2c_slave_map[2].SetValues(tbconfig.SSA_ADR[1], 2, 1, 1, 1, 0, "SSA1", "SSA1")
		#print(bin(tbconfig.MPA_ADR[0]))
		#print(bin(tbconfig.SSA_ADR[0]))
		#print(bin(tbconfig.SSA_ADR[1]))
		# updating the slave id table
		if verbose:
			print("---> Updating the Slave ID Map")
		for slave_id in range(3):
			self.fc7.write("fc7_daq_cnfg.command_processor_block.i2c_address_table.slave_" + str(slave_id) + "_config", EncodeMainSlaveMapItem(i2c_slave_map[slave_id]))
			if verbose:
				print("Writing","fc7_daq_cnfg.command_processor_block.i2c_address_table.slave_" + str(slave_id) + "_config", hex(EncodeMainSlaveMapItem(i2c_slave_map[slave_id])))

	def SetSlaveMap(self, verbose = 1):
		# define the map itself
		i2c_slave_map = [I2C_SlaveMapItem() for i in range(31)]
		# set the values
		# --- SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en) --
		#print('SET SLAVE MAP2')
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
		i2c_slave_map[12].SetValues(0b0100001, 2, 1, 1, 1, 0, "SSA")
		i2c_slave_map[11].SetValues(tbconfig.MPA_ADR[0], 2, 1, 1, 1, 0, "MPA")
		i2c_slave_map[12].SetValues(tbconfig.SSA_ADR[0], 2, 1, 1, 1, 0, "SSA0")
		i2c_slave_map[13].SetValues(tbconfig.SSA_ADR[1], 2, 1, 1, 1, 0, "SSA1")
		i2c_slave_map[15].SetValues(0b1011111, 1, 1, 1, 1, 0, "CBC3")
		# updating the slave id table
		if verbose: print("---> Updating the Slave ID Map")
		for slave_id in range(16):
			self.fc7.write("fc7_daq_cnfg.mpa_ssa_board_block.slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))
			if verbose:
				print("Writing","fc7_daq_cnfg.mpa_ssa_board_block.slave_" + str(slave_id) + "_config", hex(EncodeSlaveMapItem(i2c_slave_map[slave_id])))


	def ReadStatus(self, name = "Current Status"):
		print("============================")
		print(name + ":")
		error_counter = self.fc7.read("fc7_daq_stat.general.global_error.counter")
		print("   -> Error Counter: " + str(error_counter))
		if error_counter > 0:
			for i in range (0,error_counter):
				error_full = self.fc7.read("fc7_daq_stat.general.global_error.full_error")
				error_block_id = self.DataFromMask(error_full,"stat_error_block_id");
				error_code = self.DataFromMask(error_full,"stat_error_code");
				print("   -> ")
				fc7ErrorHandler.getErrorDescription(error_block_id,error_code)
		else:
			print("   -> No Errors")
		temp_source = self.fc7.read("fc7_daq_stat.fast_command_block.general.source")
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
		temp_state = self.fc7.read("fc7_daq_stat.fast_command_block.general.fsm_state")
		temp_state_name = "Unknown"
		if temp_state == 0:
			temp_state_name = "Idle"
		elif temp_state == 1:
			temp_state_name = "Running"
		elif temp_state == 2:
			temp_state_name = "Paused. Waiting for readout"
		print("   -> trigger state:" + str(temp_state_name))
		print("   -> trigger configured:"  + str(self.fc7.read("fc7_daq_stat.fast_command_block.general.configured")))
		print(   "   -> --------------------------------")
		print("   -> i2c commands fifo empty:" + str( self.fc7.read("fc7_daq_stat.command_processor_block.i2c.command_fifo.empty")))
		print("   -> i2c replies fifo empty:" + str( self.fc7.read("fc7_daq_stat.command_processor_block.i2c.reply_fifo.empty")))
		print("   -> i2c nreplies available:" + str( self.fc7.read("fc7_daq_stat.command_processor_block.i2c.nreplies")))
		print("   -> i2c fsm state:" + str( self.fc7.read("fc7_daq_stat.command_processor_block.i2c.master_status_fsm") ))
		print(   "   -> --------------------------------")
		print(   "   -> dio5 not ready:" + str(self.fc7.read("fc7_daq_stat.dio5_block.status.not_ready")))
		print(   "   -> dio5 error:" + str( self.fc7.read("fc7_daq_stat.dio5_block.status.error")))
		print("============================")

	def SendPhaseTuningCommand(self, value):
		self.fc7.write("fc7_daq_ctrl.physical_interface_block.phase_tuning_ctrl", value)

	def get_lines_alignment_status(self, display=False):
		status = []
		for i in range(0,9):
			status.append( self.CheckLineDone(0,0,i, display, True) )
		status = np.array(status)
		return status

	def CheckLineDone(self, hybrid_id, chip_id, line_id, display=False, return_full_status=False):
		# shifting
		hybrid_raw = (hybrid_id & 0xF) << 28
		chip_raw = (chip_id & 0xF) << 24
		line_raw = (line_id & 0xF) << 20
		# command 1
		command_type = 1
		command_raw = (command_type & 0xF) << 16
		# final command 1
		command_final = hybrid_raw + chip_raw + line_raw + command_raw
		self.SendPhaseTuningCommand(command_final)
		time.sleep(0.01)
		line_status = self.GetPhaseTuningStatus(printStatus = display, return_full_status=return_full_status)
		if(return_full_status): line_done = line_status[1]
		else: line_done = line_status
		if line_done >= 0:pass
		else: print("Tuning Failed or Wrong Status")
		if(return_full_status): return line_status
		else: return line_done


	def GetPhaseTuningStatus(self, printStatus = True, return_full_status=False):
		# get data word
		data = self.fc7.read("fc7_daq_ctrl.physical_interface_block.phase_tuning_ctrl")
		# parse commands
		line_id = (data & 0xF0000000) >> 28
		output_type = (data & 0x0F000000) >> 24
		# line configuration
		if(output_type == 0):
			mode = (data & 0x00003000) >> 12
			master_line_id = (data & 0x00000F00) >> 8
			delay = (data & 0x000000F8) >> 3
			bitslip = (data & 0x00000007) >> 0
			if printStatus:
				print("Line Configuration: ")
				print("\tLine ID: "+ str(line_id) +",\tMode: "+ str(mode)+ ",\tMaster line ID: "+ str(master_line_id)+ ",\tIdelay: "+ str(delay)+ ",\tBitslip: "+ str(bitslip))
			if(not return_full_status):
				return -1
			else:
				return [-1, line_id, mode, master_line_id, delay, bitslip]
		# tuning status
		elif(output_type == 1):
			delay = (data & 0x00F80000) >> 19
			bitslip = (data & 0x00070000) >> 16
			done = (data & 0x00008000) >> 15
			wa_fsm_state = (data & 0x00000F00) >> 8
			pa_fsm_state = (data & 0x0000000F) >> 0
			if printStatus:
				print("Line Status: ")
				print("\tTuning done/applied: "+ str(done))
				print("\tLine ID: "+str(line_id)+ ",\tIdelay: " +str(delay)+ ",\tBitslip: " +str(bitslip)+ ",\tWA FSM State: " +str(wa_fsm_state)+ ",\tPA FSM State: "+str( pa_fsm_state))
			if(not return_full_status):
				return done
			else:
				return [line_id, done, delay, bitslip, wa_fsm_state, pa_fsm_state]
		# tuning status
		elif output_type == 6:
			default_fsm_state = (data & 0x000000FF) >> 0
			if printStatus:
				print("Default tuning FSM state: "+ hex(default_fsm_state))
			return -1
		# unknown
		else:
			print("Error! Unknown status message!")
			return -2


	def TuneLine(self, line_id, pattern, pattern_period, changePattern = True, printStatus = False):
		# in that case all set specified pattern (same for all lines)
		if changePattern:
			self.SetLineMode(0,0,line_id,mode = 0)
			self.SetLinePattern(0,0,line_id,pattern, pattern_period)
			time.sleep(0.01)
		# do phase alignment
		self.SendControl(0,0,line_id,"do_phase")
		time.sleep(0.01)
		# do word alignment
		self.SendControl(0,0,line_id,"do_word")
		time.sleep(0.01)
		if printStatus:
			self.GetLineStatus(0,0,line_id)
			print( "\n")
		return self.CheckLineDone(0,0,line_id)

	def TuneLine_phase(self, line_id, pattern, pattern_period, changePattern = True):
		# in that case all set specified pattern (same for all lines)
		if changePattern:
			self.SetLineMode(0,0,line_id,mode = 0)
			self.SetLinePattern(0,0,line_id,pattern, pattern_period)
			time.sleep(0.01)
		# do phase alignment
		self.SendControl(0,0,line_id,"do_phase")
		time.sleep(0.01)


	def TuneLine_line(self, line_id, pattern, pattern_period, changePattern = True):
		# in that case all set specified pattern (same for all lines)
		if changePattern:
			self.SetLineMode(0,0,line_id,mode = 0)
			self.SetLinePattern(0,0,line_id,pattern, pattern_period)
			time.sleep(0.01)
		# do word alignment
		self.SendControl(0,0,line_id,"do_word")
		time.sleep(0.01)
		return self.CheckLineDone(0,0,line_id)

	def SetLinePattern(self, hybrid_id, chip_id, line_id, pattern, pattern_period):
		# shifting
		hybrid_raw = (hybrid_id & 0xF) << 28
		chip_raw = (chip_id & 0xF) << 24
		line_raw = (line_id & 0xF) << 20
		# setting the size of the pattern
		command_type = 3
		command_raw = (command_type & 0xF) << 16
		len_raw = (0xFF & pattern_period) << 0
		command_final = hybrid_raw + chip_raw + line_raw + command_raw + len_raw
		self.SendPhaseTuningCommand(command_final)
		# setting the pattern itself
		command_type = 4
		command_raw = (command_type & 0xF) << 16
		byte_id_raw = (0xFF & 0) << 8
		pattern_raw = (0xFF & pattern) << 0
		command_final = hybrid_raw + chip_raw + line_raw + command_raw + byte_id_raw + pattern_raw
		self.SendPhaseTuningCommand(command_final)


	def SetLineMode(self, hybrid_id, chip_id, line_id, mode, delay = 0, bitslip = 0, l1_en = 0, master_line_id = 0):
		# shifting
		hybrid_raw = (hybrid_id & 0xF) << 28
		chip_raw = (chip_id & 0xF) << 24
		line_raw = (line_id & 0xF) << 20
		# command
		command_type = 2
		command_raw = (command_type & 0xF) << 16
		# shift payload
		mode_raw = (mode & 0x3) << 12
		# defautls
		l1a_en_raw = 0
		master_line_id_raw = 0
		delay_raw = 0
		bitslip_raw = 0
		# now assign proper values
		if mode == 0:
			l1a_en_raw = (l1_en & 0x1) << 11
		elif mode == 1:
			master_line_id_raw = (master_line_id & 0xF) << 8
		elif mode == 2:
			delay_raw = (delay & 0x1F) << 3
			bitslip_raw = (bitslip & 0x7) << 0
		# now combine the command itself
		command_final = hybrid_raw + chip_raw + line_raw + command_raw + mode_raw + l1a_en_raw + master_line_id_raw + delay_raw + bitslip_raw
		self.SendPhaseTuningCommand(command_final)


	def SendControl(self, hybrid_id, chip_id, line_id, command):
		# shifting
		hybrid_raw = (hybrid_id & 0xF) << 28
		chip_raw = (chip_id & 0xF) << 24
		line_raw = (line_id & 0xF) << 20
		# command
		command_type = 5
		command_raw = (command_type & 0xF) << 16
		# final
		command_final = hybrid_raw + chip_raw + line_raw + command_raw
		if command == "do_apply":
			command_final += 4
		elif command == "do_word":
			command_final += 2
		elif command == "do_phase":
			command_final += 1
		# send
		self.SendPhaseTuningCommand(command_final)

	def GetLineStatus(self, hybrid_id, chip_id, line_id):
		# shifting
		hybrid_raw = (hybrid_id & 0xF) << 28
		chip_raw = (chip_id & 0xF) << 24
		line_raw = (line_id & 0xF) << 20
		# command 0
		command_type = 0
		command_raw = (command_type & 0xF) << 16
		# final command 0
		command_final = hybrid_raw + chip_raw + line_raw + command_raw
		self.SendPhaseTuningCommand(command_final)
		time.sleep(0.01)
		# self.GetPhaseTuningStatus()
		# command 1
		command_type = 1
		command_raw = (command_type & 0xF) << 16
		# final command 1
		command_final = hybrid_raw + chip_raw + line_raw + command_raw
		self.SendPhaseTuningCommand(command_final)
		time.sleep(0.01)
		done = self.GetPhaseTuningStatus()
		return done


	# read the chip data (nbytes per read transaction)
	def ReadChipDataNEW(self, nbytes = 1, verbose = 0):
		numberOfReads = 0
		data = None
		if verbose:
			print("Reading Out Data:")
			print("   ==========================================================================================")
			print("   | Hybrid ID             || Chip ID             || Register(LSB)          || DATA         |")
			print("   ==========================================================================================")

		while self.fc7.read("fc7_daq_stat.command_processor_block.i2c.reply_fifo.empty") == 0:
			byte_counter = 0
			reply = self.fc7.read("fc7_daq_ctrl.command_processor_block.i2c.reply_fifo")
			hybrid_id = self.DataFromMask(reply, "ctrl_command_i2c_reply_hybrid_id")
			chip_id = self.DataFromMask(reply, "ctrl_command_i2c_reply_chip_id")
			register = self.DataFromMask(reply, "ctrl_command_i2c_reply_register") #didnt find
			data = self.DataFromMask(reply, "ctrl_command_i2c_reply_data")

			# first byte is always in the first word
			if verbose:
				print('   | {:s} {:-12i} || {:s} {:-12i} || {:s} {:-12i} || {:-12i} |'.format("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4]))
			byte_counter = byte_counter + 1
			register = register + 1
			while(byte_counter < nbytes):
				# just in case wait next word
				while(self.fc7.read("fc7_daq_stat.command_processor_block.i2c.reply_fifo.empty") == 1):
					print("debug: waiting next word, should not happen")
					time.sleep(1)
				reply = self.fc7.read("fc7_daq_ctrl.command_processor_block.i2c.reply_fifo")
				data1 = (reply & 0x000000FF) >> 0
				data2 = (reply & 0x0000FF00) >> 8
				data3 = (reply & 0x00FF0000) >> 16
				# this "if" is not necessary - satisfied when entered the while loop - print the first byte of the word
				if (byte_counter < nbytes):
					if verbose:
						print('   | {:s} {:-12i} || {:s} {:-12i} || {:s} {:-12i} || {:-12i} |'.format("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4]))
					byte_counter = byte_counter + 1
					register = register + 1
				# print(the second byte of the word)
				if (byte_counter < nbytes):
					if verbose:
						print('   | {:s} {:-12i} || {:s} {:-12i} || {:s} {:-12i} || {:-12i} |'.format("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4]))
					byte_counter = byte_counter + 1
					register = register + 1
				# print(the third byte of the word)
				if (byte_counter < nbytes):
					if verbose:
						print('   | {:s} {:-12i} || {:s} {:-12i} || {:s} {:-12i} || {:-12i} |'.format( "Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4]))
					byte_counter = byte_counter + 1
					register = register + 1
		if verbose:
			print("	-----------------------------------------------------------------------------------------")
			print("   ====================================================   ")
		return data
