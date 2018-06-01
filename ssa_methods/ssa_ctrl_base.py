from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt

class ssa_ctrl_base:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map;
		self.analog_mux_map = analog_mux_map;
		self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
		self.dll_chargepump = 0b00;
		self.bias_dl_enable = False


	def resync(self):
		SendCommand_CTRL("fast_fast_reset");
		print '->  \tSent Re-Sync command'
		sleep(0.001)


	def reset(self, display=True):
		rp = self.pwr.reset(display=display)
		self.set_t1_sampling_edge("negative")
		return rp

	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		registers = []
		for reg in self.ssa_peri_reg_map:
			tmp = [-1, reg, self.I2C.peri_read(reg)]
			registers.append(tmp)
		for strip in range(1,121):
			for reg in self.ssa_strip_reg_map:
				tmp = [strip, reg, self.I2C.strip_read(reg, strip)]
				registers.append(tmp)
		print "->  \tConfiguration Saved on file:   " + str(file)
		if display:
			for i in registers:
				print i
		CSV.ArrayToCSV(registers, file)

	def load_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		registers = CSV.CsvToArray(file)[:,1:4]
		for tmp in registers:
			if(tmp[0] == -1):
				if display: print 'writing'
				if (not 'Fuse' in tmp[1]):
					self.I2C.peri_write(tmp[1], tmp[2])
					r = self.I2C.peri_read(tmp[1])
					if(r != tmp[2]):
						print 'X>  \t Configuration ERROR Periphery  ' + str(tmp[1]) + '  ' + str(tmp[2]) + '  ' + str(r)
			elif(tmp[0]>=1 and tmp[0]<=120):
				if display: print 'writing'
				if ((not 'ReadCounter' in tmp[1]) and ((not 'Fuse' in tmp[1]))):
					self.I2C.strip_write(tmp[1], tmp[0], tmp[2])
					r = self.I2C.strip_read(tmp[1], tmp[0])
					if(r != tmp[2]):
						print 'X>  \t Configuration ERROR Strip ' + str(tmp[0])
			if display:
				print [tmp[0], tmp[1], tmp[2], r]
		print "->  \tConfiguration Loaded from file"


	def set_output_mux(self, testline = 'highimpedence'):
		ctrl = self.analog_mux_map[testline]
		self.I2C.peri_write('Bias_TEST_LSB', 0) # to avoid short
		self.I2C.peri_write('Bias_TEST_MSB', 0) # to avoid short
		self.I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
		self.I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
		r = ((self.I2C.peri_read('Bias_TEST_LSB') & 0xff))
		r = ((self.I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			print "Error. Failed to set the MUX"
			return False
		else:
			return True


	def init_slvs(self, current = 0b100):
		self.I2C.peri_write('SLVS_pad_current', current)
		r = self.I2C.peri_read('SLVS_pad_current')
		if (self.I2C.peri_read("SLVS_pad_current") != (current & 0b111) ):
			print "Error! I2C did not work properly"
			exit(1)


	def set_lateral_lines_alignament(self):
		self.I2C.strip_write("ENFLAGS", 0, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0)
		self.I2C.strip_write("DigCalibPattern_H", 0, 0)
		self.I2C.peri_write( "CalPulse_duration", 15)
		self.I2C.strip_write("ENFLAGS",   7, 0b01001)
		self.I2C.strip_write("ENFLAGS", 120, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L",   7, 0xff)
		self.I2C.strip_write("DigCalibPattern_L", 120, 0xff)


	def reset_pattern_injection(self):
		self.I2C.strip_write("ENFLAGS", 0, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0)
		self.I2C.strip_write("DigCalibPattern_H", 0, 0)


	def __do_phase_tuning(self):
		#print self.fc7.read("stat_phy_phase_tuning_done")
		self.fc7.write("ctrl_phy_phase_tune_again", 1)
		#print self.fc7.read("stat_phy_phase_tuning_done")
		send_test(15)
		#print self.fc7.read("stat_phy_phase_tuning_done")
		while(self.fc7.read("stat_phy_phase_tuning_done") == 0):
			sleep(0.5)
			print "Waiting for the phase tuning"


	def phase_tuning(self):
		self.activate_readout_shift()
		self.set_shift_pattern_all(128)
		time.sleep(0.01)
		self.set_lateral_lines_alignament()
		time.sleep(0.01)
		self.__do_phase_tuning()
		self.I2C.peri_write('OutPattern7/FIFOconfig', 7)
		self.reset_pattern_injection()
		self.activate_readout_normal()


	def set_t1_sampling_edge(self, edge):
		if edge == "rising" or edge == "positive":
			self.I2C.peri_write('EdgeSel_T1', 1)
		elif edge == "falling" or edge == "negative":
			self.I2C.peri_write('EdgeSel_T1', 0)
		else:
			print "Error! The edge name is wrong"


	def activate_readout_normal(self, mipadapterdisable = 0):
		val = 0b100 if (mipadapterdisable) else 0b000
		self.I2C.peri_write('ReadoutMode',val)
		if (self.I2C.peri_read("ReadoutMode") != val):
			print "Error! I2C did not work properly"
			exit(1)


	def activate_readout_async(self, ssa_first_counter_delay = 8, correction = 0):
		self.I2C.peri_write('ReadoutMode',0b01)
		# write to the I2C
		self.I2C.peri_write("AsyncRead_StartDel_MSB", ((ssa_first_counter_delay >> 8) & 0x01))
		self.I2C.peri_write("AsyncRead_StartDel_LSB", (ssa_first_counter_delay & 0xff))
		# check the value
		if (self.I2C.peri_read("AsyncRead_StartDel_LSB") != ssa_first_counter_delay & 0xff):
			print "Error! I2C did not work properly"
			error(1)
		# ssa set delay of the counters
		fwdel = ssa_first_counter_delay + 24 + correction
		if(fwdel >= 255):
			print '->  \tThe counters delay value selected is not supposrted by the firmware [> 255]'
		self.fc7.write("cnfg_phy_slvs_ssa_first_counter_del", fwdel & 0xff)


	def activate_readout_shift(self):
		self.I2C.peri_write('ReadoutMode',0b10)


	def set_shift_pattern_all(self, pattern):
		self.set_shift_pattern(pattern,pattern,pattern,pattern,pattern,pattern,pattern,pattern)


	def set_shift_pattern(self, line0, line1, line2, line3, line4, line5, line6, line7):
		self.I2C.peri_write('OutPattern0',line0)
		self.I2C.peri_write('OutPattern1',line1)
		self.I2C.peri_write('OutPattern2',line2)
		self.I2C.peri_write('OutPattern3',line3)
		self.I2C.peri_write('OutPattern4',line4)
		self.I2C.peri_write('OutPattern5',line5)
		self.I2C.peri_write('OutPattern6',line6)
		self.I2C.peri_write('OutPattern7/FIFOconfig',line7)


	def set_async_delay(self, value):
		msb = (value & 0xFF00) >> 8
		lsb = (value & 0x00FF) >> 0
		self.I2C.peri_write('AsyncRead_StartDel_MSB', msb)
		self.I2C.peri_write('AsyncRead_StartDel_LSB', lsb)


	def set_threshold(self, value):
		self.I2C.peri_write("Bias_THDAC", value)
		sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDAC")
		if(test_read != value):
			print "Was writing: ", value, ", got: ", test_read
			print "Error. Failed to set the threshold"
			error(1)


	def set_threshold_H(self, value):
		self.I2C.peri_write("Bias_THDACHIGH", value)
		sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDACHIGH")
		if(test_read != value):
			print "Was writing: ", value, ", got: ", test_read
			print "Error. Failed to set the threshold"
			error(1)


	def init_default_thresholds(self):
		# init thersholds
		self.I2C.peri_write("Bias_THDAC", 35)
		self.I2C.peri_write("Bias_THDACHIGH", 120)


	def init_trimming(self, th_trimming = 15, gain_trimming = 15):
		self.I2C.strip_write('THTRIMMING', 0, th_trimming)
		self.I2C.strip_write('GAINTRIMMING', 0, gain_trimming)
		repT = [0xff]*120
		repG = [0xff]*120
		error = False
		for i in range(1,121):
			repT[i-1] = self.I2C.strip_read('THTRIMMING', i)
			repG[i-1] = self.I2C.strip_read('GAINTRIMMING', i)
		for i in repT:
			if (i != th_trimming): error = True
		for i in repG:
			if (i != gain_trimming): error = True
		if error:
			print "Error. Failed to set the trimming"


	def set_cal_pulse(self, amplitude = 255, duration = 5, delay = 'keep'):
		self.I2C.peri_write("Bias_CALDAC", amplitude) # init cal pulse itself
		self.I2C.peri_write("CalPulse_duration", duration) # set cal pulse duration
		self.set_cal_pulse_delay(delay) # init the cal pulse digital delay line


	def set_cal_pulse_delay(self, delay):
		if(isinstance(delay, str)):
			if(delay == 'disable' or delay == 'off'):
				self.I2C.peri_write("Bias_DL_en", 0)
				self.bias_dl_enable = False
			elif(delay == 'enable'or delay == 'on'):
				self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			elif(delay == 'keep'): pass
			else: exit(1)
		elif(isinstance(delay, int)):
			if (not self.bias_dl_enable):
				self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			self.I2C.peri_write("Bias_DL_ctrl", delay)
		return True


	def set_sampling_deskewing_coarse(self, value):
		word = value & 0b111
		self.I2C.peri_write("PhaseShiftClock", word)
		r = self.I2C.peri_read("PhaseShiftClock")
		if(r != word): return False
		else: return True


	def set_sampling_deskewing_fine(self, value, enable = True, bypass = False):
		word = (
			((value & 0b1111) << 0) |
			((self.dll_chargepump & 0b11) << 4) |
			((bypass & 0b1) << 6) |
			((enable & 0b1) << 7)
		)
		self.I2C.peri_write("ClockDeskewing", word)
		r = self.I2C.peri_read("ClockDeskewing")
		if(r != word): return False
		else: return True


	def set_sampling_deskewing_chargepump(self, val):
		self.dll_chargepump = val & 0b11
		r = self.I2C.peri_read("ClockDeskewing")
		word = (r & 0b11001111) | (self.dll_chargepump << 4)
		self.I2C.peri_write("ClockDeskewing", word)
		r = self.I2C.peri_read("ClockDeskewing")
		if(r != word): return False
		else: return True


	def set_lateral_data_phase(self, left, right):
		self.fc7.write("ctrl_phy_ssa_gen_lateral_phase_1", right)
		self.fc7.write("ctrl_phy_ssa_gen_lateral_phase_2", left)


	def set_lateral_data(self, left, right):
		self.fc7.write("cnfg_phy_SSA_gen_right_lateral_data_format", right)
		self.fc7.write("cnfg_phy_SSA_gen_left_lateral_data_format", left)
