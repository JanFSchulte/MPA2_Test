from d19cScripts.fc7_daq_methods import *
from d19cScripts.phase_tuning_control import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt

class mpa_ctrl_base:
	def __init__(self, I2C, FC7, pwr, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map):
		self.mpa_peri_reg_map = mpa_peri_reg_map;
		self.mpa_row_reg_map = mpa_row_reg_map;
		self.mpa_pixel_reg_map = mpa_pixel_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
	def resync(self):
		SendCommand_CTRL("fast_fast_reset");
		print('->  \tSent Re-Sync command')
		time.sleep(0.001)
	def reset(self, display=True):
		rp = self.pwr.reset(display=display)
		self.set_sampling_edge("negative")
		return rp
	def init_slvs(self, curr = 1):
		currSLVS = 0b00111000 | curr
		self.I2C.peri_write("ConfSLVS", currSLVS)
	# Operation mode selection:
	def activate_async(self):
		self.I2C.peri_write("Mask", 0b00000011)
		self.I2C.peri_write("Control", 0b01)
		self.I2C.peri_write("Mask", 0b11111111)
	def activate_sync(self):
		self.I2C.peri_write("Mask", 0b00000011)
		self.I2C.peri_write("Control", 0b00)
		self.I2C.peri_write("Mask", 0b11111111)
	def activate_shift(self):
		self.I2C.peri_write("Mask", 0b00000011)
		self.I2C.peri_write("Control", 0b10)
		self.I2C.peri_write("Mask", 0b11111111)
	def activate_pp(self):
		self.I2C.peri_write("Mask", 0b11111111)
		self.I2C.peri_write('ECM',0b10000001)
		self.I2C.peri_write("Mask", 0b11111111)
	def activate_ss(self):
		self.I2C.peri_write('ECM',0b01000001)
	def activate_ps(self):
		self.I2C.peri_write('ECM',0b00001000)

	def ro_peri(self, duration = 100, verbose = 0):
		self.set_peri_mask()
		self.I2C.peri_write('RingOscillator', duration)
		self.I2C.peri_write("Mask", 0b10000000)
		self.I2C.peri_write('RingOscillator', 0b10000000)
		self.set_peri_mask()
		time.sleep(0.01)
		lsb_1 = self.I2C.peri_read('RO_Inv_LSB')
		msb_1 = self.I2C.peri_read('RO_Inv_MSB')
		lsb_2 = self.I2C.peri_read('RO_Del_LSB')
		msb_2 = self.I2C.peri_read('RO_Del_MSB')
		res_1 = ((msb_1<<8) | lsb_1)
		res_2 = ((msb_2<<8) | lsb_2)
		if verbose:
			print("Ring Oscillator Inverter: " , res_1)
			print("Ring Oscillator Delay: " , res_2)
		return res_1, res_2

	def ro_row(self, row, duration = 100, verbose = 0):
		self.set_row_mask(row)
		self.I2C.row_write('RingOscillator', row, duration)
		self.I2C.row_write("Mask", row, 0b10000000)
		self.I2C.row_write('RingOscillator', row, 0b10000000)
		self.set_peri_mask(row)
		time.sleep(0.01)
		lsb_1 = self.I2C.row_read('RO_Row_Inv_LSB', row)
		msb_1 = self.I2C.row_read('RO_Row_Inv_MSB', row)
		lsb_2 = self.I2C.row_read('RO_Row_Del_LSB', row)
		msb_2 = self.I2C.row_read('RO_Row_Del_MSB', row)
		res_1 = ((msb_1<<8) | lsb_1)
		res_2 = ((msb_2<<8) | lsb_2)
		if verbose:
			print("Ring Oscillator Inverter: " , res_1)
			print("Ring Oscillator Delay: " , res_2)
		return res_1, res_2



	def set_peri_mask(self, bit_mask = 0):
		""""Set/Reset mask register, which enables the given bit position for writing across all i2c registers. Required before register writes.

		Args:
			bit_mask (int, optional): Bit mask, to enable I2C register bits for writing. If left unset, all bits are set to enabled, i.e. value = 0b11111111. Defaults to 0.
		"""
		if bit_mask:
			self.I2C.peri_write("Mask", bit_mask)
		else:
			self.I2C.peri_write("Mask", 0b111111111)

	def set_row_mask(self, r = 0, bit_mask = 0):
		""""Set/Reset mask register, which enables the given bit position for writing across all i2c registers. Required before register writes.

		Args:
			bit_mask (int, optional): Bit mask, to enable I2C register bits for writing. If left unset, all bits are set to enabled, i.e. value = 0b11111111. Defaults to 0.
		"""
		if bit_mask:
			self.I2C.row_write("Mask", r , bit_mask)
		else:
			self.I2C.row_write("Mask", r, 0b111111111)

	# Pixel mode selection
	def enable_pix_counter(self, r, p):
		self.I2C.pixel_write('ENFLAGS', r, p, 0x53)
	def enable_pix_disable_ancal(self, r,p):
		self.I2C.pixel_write('ENFLAGS', r, p, 0x13)
	def enable_pix_sync(self, r,p):
		self.I2C.pixel_write('ENFLAGS', r, p, 0x53)
	# Analog Mux control
	def disable_test(self):
		#activate_I2C_chip()
		self.set_peri_mask()
		self.I2C.peri_write('ADC_TEST_selection',0b00000000)
	def enable_test(self, block, point):
		#activate_I2C_chip()
		self.disable_test()
		test = "TEST" + str(block)
		self.I2C.peri_write('TESTMUX',0b00000001 << block)
		self.I2C.peri_write(test, 0b00000001 << point)
	def set_DAC(self, block, point, value):
		#activate_I2C_chip(verbose = 0)
		test = "TEST" + str(block)
		self.I2C.peri_write('TESTMUX',0b00000001 << block)
		self.I2C.peri_write(test, 0b00000001 << point)
		nameDAC = ["A", "B", "C", "D", "E", "F"]
		DAC = nameDAC[point] + str(block)
		self.I2C.peri_write(DAC, value)
	# Threshold and Calibration control
	def set_calibration(self, cal):
		self.I2C.peri_write('CalDAC0',cal)
		self.I2C.peri_write('CalDAC1',cal)
		self.I2C.peri_write('CalDAC2',cal)
		self.I2C.peri_write('CalDAC3',cal)
		self.I2C.peri_write('CalDAC4',cal)
		self.I2C.peri_write('CalDAC5',cal)
		self.I2C.peri_write('CalDAC6',cal)
	def set_threshold(self, th):
		self.I2C.peri_write('ThDAC0',th)
		self.I2C.peri_write('ThDAC1',th)
		self.I2C.peri_write('ThDAC2',th)
		self.I2C.peri_write('ThDAC3',th)
		self.I2C.peri_write('ThDAC4',th)
		self.I2C.peri_write('ThDAC5',th)
		self.I2C.peri_write('ThDAC6',th)
	# Sampling edge control
	def set_sampling_edge(self, edge):
		if edge == "rising" or edge == "positive":
			self.I2C.peri_write('EdgeSelT1Raw', 0b11)
			self.I2C.peri_write('EdgeSelTrig', 0b11111111)
		elif edge == "falling" or edge == "negative":
			self.I2C.peri_write('EdgeSelT1Raw', 0)
			self.I2C.peri_write('EdgeSelTrig', 0)
		else:
			print("Error! The edge name is wrong")
# Output Pad mapping
	def set_out_mapping(self, map = [1, 2, 3, 4, 5, 0]):
		self.I2C.peri_write('OutSetting_1_0', 0b010001);time.sleep(0.1)
		self.I2C.peri_write('OutSetting_3_2', 0b100011);time.sleep(0.1)
		self.I2C.peri_write('OutSetting_5_4', 0b000101);time.sleep(0.1)

# Output Pad mapping
	def set_out_mapping_probing(self, map = [1, 2, 3, 4, 5, 0]):
		self.I2C.peri_write('OutSetting_1_0', 0b001000);time.sleep(0.1)
		self.I2C.peri_write('OutSetting_3_2', 0b011010);time.sleep(0.1)
		self.I2C.peri_write('OutSetting_5_4', 0b101100);time.sleep(0.1)

# Output alignment procedure
	def align_out(self, verbose = 1):
		self.fc7.write("fc7_daq_ctrl.physical_interface_block.control.cbc3_tune_again", 1)
		timeout_max = 5
		timeout = 0
		while(self.fc7.read("fc7_daq_stat.physical_interface_block.phase_tuning_reply") == 0):
			time.sleep(0.1)
			if (timeout == timeout_max):
				timeout = 0
				if (verbose): print("Waiting for the phase tuning")
				self.fc7.write("fc7_daq_ctrl.physical_interface_block.control.cbc3_tune_again", 1)
			else:
				timeout += 1

	def align_out_all(self, verbose = 1, pattern = 0b10100000):
		self.activate_shift()
		# set pattern
		self.I2C.peri_write("LFSR_data", pattern)
		time.sleep(0.1)
		return TuneMPA(pattern)

	def fuse_write(self, lot, wafer_n, pos, process, adc_ref, status, pulse = 0, confirm = 0 ):
		val = ((adc_ref & 0x1F) << 27) | ((process & 0x1F) << 22) | (status & 0x3) << 20 | ((lot & 0x7F) << 13) | ((wafer_n & 0x1F) << 8) | (pos & 0xFF)
		print(bin(val))
		d0 = (val >>  0) & 0xFF
		d1 = (val >>  8) & 0xFF
		d2 = (val >> 16) & 0xFF
		d3 = (val >> 24) & 0xFF
		print(bin(d3).lstrip('-0b').zfill(8), ' ', bin(d2).lstrip('-0b').zfill(8), ' ', bin(d1).lstrip('-0b').zfill(8), ' ', bin(d0).lstrip('-0b').zfill(8))
		self.I2C.peri_write('EfuseProg0', d0); self.I2C.peri_write('EfuseProg1', d1); self.I2C.peri_write('EfuseProg2', d2); self.I2C.peri_write('EfuseProg3', d3)
		r0 = self.I2C.peri_read('EfuseProg0'); r1 = self.I2C.peri_read('EfuseProg1'); r2 = self.I2C.peri_read('EfuseProg2'); r3 = self.I2C.peri_read('EfuseProg3');
		if (((r3<<24) | (r2<<16) | (r1<<8) | (r0<<0) ) != val):
			print("Error in setting the e-fuses write buffer")
			return False
		if (pulse):
			if confirm:  rp = 'Y'
			else:  rp = input("\n->  Are you sure you want to write the e-fuses? [Y|n] : ")
			if (rp == 'Y'):
				time.sleep(0.1); self.I2C.peri_write('BypassMode', 0b00000001)
				time.sleep(0.1); self.I2C.peri_write('EfuseMode', 0b11110000)
				time.sleep(1)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_7_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_7_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_6_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_6_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_5_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_5_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_4_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_4_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_3_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_3_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_2_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_2_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_1_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_1_1", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_0_0", 0xFFFFFFFF)
				self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_0_1", 0xFFFFFFFF)
				self.fc7.send_test(7)
				time.sleep(5)
				#self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_7_0", 0x00)
				#self.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_7_1", 0x00)
				time.sleep(0.1); self.I2C.peri_write('EfuseMode', 0b00000000)
		else:
			return False
		return val

	def read_fuses(self):
		self.I2C.peri_write('EfuseMode', 0b00000000)
		time.sleep(0.1)
		self.I2C.peri_write('EfuseMode', 0b00001111)
		time.sleep(0.1)
		self.I2C.peri_write('EfuseMode', 0b00000000)
		r0 = self.I2C.peri_read('EfuseValue0'); r1 = self.I2C.peri_read('EfuseValue1'); r2 = self.I2C.peri_read('EfuseValue2'); r3 = self.I2C.peri_read('EfuseValue3');
		print(bin(r3).lstrip('-0b').zfill(8), ' ', bin(r2).lstrip('-0b').zfill(8), ' ', bin(r1).lstrip('-0b').zfill(8), ' ', bin(r0).lstrip('-0b').zfill(8))









#	def save_configuration(self, file = '../MPA_Results/Configuration.csv', display=True):
#		registers = []
#		for reg in self.mpa_peri_reg_map:
#			tmp = [-1, -1, reg, self.I2C.peri_read(reg)]
#			registers.append(tmp)
#		for row in range(1,17):
#			for reg in self.mpa_row_reg_map:
#				tmp = [row, -1, reg, self.I2C.row_read(reg, row)]
#				registers.append(tmp)
#				for pix in range(1,121):
#					for reg_pix in self.mpa_pixel_reg_map:
#						tmp = [row, pix, reg_pix, self.I2C.pix_read(reg_pix, row, pix)]
#						registers.append(tmp)
#		print "->  \tConfiguration Saved on file:   " + str(file)
#		if display:
#			for i in registers:
#				print i
#		CSV.ArrayToCSV(registers, file)
#
#	def load_configuration(self, file = '../MPA_Results/Configuration.csv', display=True):
#		registers = CSV.CsvToArray(file)[:,1:4]
#		for tmp in registers:
#			if(tmp[0] == -1):
#				if display: print 'writing'
#				if (not 'Fuse' in tmp[1]):
#					self.I2C.peri_write(tmp[1], tmp[2])
#					r = self.I2C.peri_read(tmp[1])
#					if(r != tmp[2]):
#						print 'X>  \t Configuration ERROR Periphery  ' + str(tmp[1]) + '  ' + str(tmp[2]) + '  ' + str(r)
#			elif(tmp[0]>=1 and tmp[0]<=16 and (tmp[1]==-1)):
#				if display: print 'writing'
#				if ((not 'ReadCounter' in tmp[1]) and ((not 'Fuse' in tmp[1]))):
#					self.I2C.row_write(tmp[1], tmp[0], tmp[2])
#					r = self.I2C.row_read(tmp[1], tmp[0])
#					if(r != tmp[2]):
#						print 'X>  \t Configuration ERROR Row ' + str(tmp[0])
#			elif(tmp[0]>=1 and tmp[0]<=16 and tmp[1]>=1 and tmp[0]<=121)):
#				if display: print 'writing'
#				if ((not 'ReadCounter' in tmp[1]) and ((not 'Fuse' in tmp[1]))):
#					self.I2C.row_write(tmp[1], tmp[0], tmp[2])
#					r = self.I2C.row_read(tmp[1], tmp[0])
#					if(r != tmp[2]):
#						print 'X>  \t Configuration ERROR Row ' + str(tmp[0])
#
#			if display:
#				print [tmp[0], tmp[1], tmp[2], r]
#		print "->  \tConfiguration Loaded from file"
