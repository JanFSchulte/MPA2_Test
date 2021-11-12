import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.tbsettings import *

class SSA_inject():

	def __init__(self, I2C, FC7, ssactrl, ssastrip):
		self.I2C = I2C; self.fc7 = FC7;
		self.ctrl = ssactrl; self.strip = ssastrip;
		self.__initialise()

	def digital_pulse(self, hit_list = [], hip_list = [], times = 1, sequence = 0x01, initialise = True, profile=False):
		leftdata  = 0; rightdata = 0;

		if(initialise == True):
			self.ctrl.activate_readout_normal()
			self.ctrl.set_cal_pulse_duration(times)
			#self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			#fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", 4)
		if(profile): pr_start=time.time()
		if(sequence != self.DigCalibPattern): #to speedup
			if(tbconfig.VERSION['SSA'] >= 2):
				self.I2C.strip_write( register="DigCalibPattern_L", field=False, strip='all', data=sequence)
			else:
				self.I2C.strip_write("DigCalibPattern_L", 0, sequence)

		if( (hit_list != self.hit_list) or (self.data_l != leftdata) or (self.data_r != rightdata)):#to speedup
			self.hit_list = hit_list
			if(tbconfig.VERSION['SSA'] >= 2):
				self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b00000)
			else:
				self.I2C.strip_write("ENFLAGS", 0, 0b0)
			for cl in hit_list:
				if (cl < 1):
					rightdata = rightdata | (0b1 << (7+cl))
					#print(bin(rightdata))
				elif (cl > 120):
					leftdata = leftdata | (0b1 << (cl-121))
					#print(bin(leftdata))
				else:
					#time.sleep(0.001)
					if(tbconfig.VERSION['SSA'] >= 2):
						self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=(cl), data=0b01001)
					else:
						self.I2C.strip_write("ENFLAGS", cl, 0b01001)

		if(self.data_l != leftdata or self.data_r != rightdata):#to speedup
			#print(bin(rightdata))
			#print(bin(leftdata))
			self.ctrl.set_lateral_data(left = leftdata, right = rightdata)
			self.data_l = leftdata;
			self.data_r = rightdata;

		if(hip_list != self.hip_list):#to speedup
			self.hip_list = hip_list
			self.I2C.strip_write(register="DigCalibPattern_H", strip='all', data=0x0)
			for cl in hip_list:
				if(tbconfig.VERSION['SSA'] >= 2):
					self.I2C.strip_write("DigCalibPattern_H", (cl), sequence)
				else:
					self.I2C.strip_write("DigCalibPattern_H", cl, sequence)
		time.sleep(0.001)
		utils.generic_parameters['ssa_inject_utility_mode'] = 'digital'
		if(profile): utils.print_log('->  digital_pulse time = {:0.3f}ms'.format(1000*(time.time()-pr_start)))


	def analog_pulse(self, hit_list = [], mode = 'edge', threshold = [50, 100], cal_pulse_amplitude = 150, initialise = True, trigger = False):
		if(initialise == True):
			self.ctrl.activate_readout_normal()
			self.ctrl.set_cal_pulse(amplitude = cal_pulse_amplitude, duration = 15, delay = 'keep')
			self.ctrl.set_threshold(threshold[0])
			self.ctrl.set_threshold_H(threshold[1])
			if(tbconfig.VERSION['SSA'] >= 2):
				self.I2C.strip_write( register="DigCalibPattern_L", field=False, strip='all', data=0)
				self.I2C.strip_write( register="DigCalibPattern_H", field=False, strip='all', data=0)
			else:
				self.I2C.strip_write("DigCalibPattern_L", 0, 0)
				self.I2C.strip_write("DigCalibPattern_H", 0, 0)
			#Configure_TestPulse_MPA_SSA(200, 1)
		if(mode != self.hitmode): # to speed up
			self.hitmode = mode
			self.strip.set_sampling_mode('all', mode)
		#enable pulse injection in selected clusters
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b00000)
		else:
			self.I2C.strip_write("ENFLAGS", 0, 0b00000)
		for cl in hit_list:
			if(cl > 0 and cl < 121):
				if(tbconfig.VERSION['SSA'] >= 2):
					self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=(cl), data=0b10001)
				else:
					self.I2C.strip_write("ENFLAGS", cl, 0b10001)
				time.sleep(0.001)
		if(trigger == True):
			self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a", 1)
			self.fc7.SendCommand_CTRL("start_trigger")
			time.sleep(0.01)
		time.sleep(0.001)
		utils.generic_parameters['ssa_inject_utility_mode'] = 'analog'


	def __initialise(self):
		self.hitmode = 'none'
		self.data_l = False
		self.data_r = False
		self.hit_list = [0xffff]
		self.hip_list = [0xffff]
		self.DigCalibPattern = 0xffff
