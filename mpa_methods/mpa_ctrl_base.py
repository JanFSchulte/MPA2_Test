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
## Operation mode selection:
	def activate_async(self):
		self.I2C.peri_write('ReadoutMode',0b01)
	def activate_sync(self):
		self.I2C.peri_write('ReadoutMode',0b00)
	def activate_shift(self):
		self.I2C.peri_write('ReadoutMode',0b10)
	def activate_pp(self):
		self.I2C.peri_write('ECM',0b10000001)
	def activate_ss(self):
		self.I2C.peri_write('ECM',0b01000001)
	def activate_ps(self):
		self.I2C.peri_write('ECM',0b00001000)
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
		self.I2C.peri_write('TESTMUX',0b00000000)
		self.I2C.peri_write('TEST0',0b00000000)
		self.I2C.peri_write('TEST1',0b00000000)
		self.I2C.peri_write('TEST2',0b00000000)
		self.I2C.peri_write('TEST3',0b00000000)
		self.I2C.peri_write('TEST4',0b00000000)
		self.I2C.peri_write('TEST5',0b00000000)
		self.I2C.peri_write('TEST6',0b00000000)
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
		self.I2C.peri_write('OutSetting_0',map[0])
		self.I2C.peri_write('OutSetting_1',map[1])
		self.I2C.peri_write('OutSetting_2',map[2])
		self.I2C.peri_write('OutSetting_3',map[3])
		self.I2C.peri_write('OutSetting_4',map[4])
		self.I2C.peri_write('OutSetting_5',map[5])
# Output alignment procedure
	def align_out(self, verbose = 1):
		self.fc7.write("ctrl_phy_phase_tune_again", 1)
		timeout_max = 5
		timeout = 0
		while(self.fc7.read("stat_phy_phase_tuning_done") == 0):
			time.sleep(0.1)
			if (timeout == timeout_max):
				timeout = 0
				if (verbose): print("Waiting for the phase tuning")
				self.fc7.write("ctrl_phy_phase_tune_again", 1)
			else:
				timeout += 1
	def align_out_all(self, verbose = 1):
		self.I2C.peri_write("ReadoutMode", 2)
		self.I2C.peri_write("LFSR_data", 0b10100000)
		time.sleep(0.1)
		return TuneMPA()
		#self.I2C.peri_write("ReadoutMode", 0)


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
