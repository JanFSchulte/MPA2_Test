from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_inject():

	def __init__(self, I2C, FC7, ssactrl, ssastrip):
		self.I2C = I2C; self.fc7 = FC7;
		self.ctrl = ssactrl; self.strip = ssastrip;
		self.__initialise()

	def digital_pulse(self, hit_list = [], hip_list = [], times = 1, sequence = 0xff, initialise = True):
		leftdata  = 0; rightdata = 0;

		if(initialise == True):
			self.ctrl.activate_readout_normal()
			self.I2C.peri_write("CalPulse_duration", times)
			#self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			#fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", 4)

		if(sequence != self.DigCalibPattern): #to speedup
			self.I2C.strip_write("DigCalibPattern_L", 0, sequence)

		if(hit_list != self.hit_list):#to speedup
			self.hit_list = hit_list
			self.I2C.strip_write("ENFLAGS", 0, 0b0)
			for cl in hit_list:
				if (cl < 1):
					rightdata = rightdata | (0b1 << (7+cl))
				elif (cl > 120):
					leftdata = leftdata | (0b1 << (cl-121))
				else:
					#time.sleep(0.001)
					self.I2C.strip_write("ENFLAGS", cl, 0b01001)

		if(self.data_l != leftdata or self.data_r != rightdata):#to speedup
			self.ctrl.set_lateral_data(left = leftdata, right = rightdata)
			self.data_l = leftdata;
			self.data_r = rightdata;

		if(hip_list != self.hip_list):#to speedup
			self.hip_list = hip_list
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)
			for cl in hip_list:
				self.I2C.strip_write("DigCalibPattern_H", cl, sequence)
		sleep(0.001)
		utils.generic_parameters['ssa_inject_utility_mode'] = 'digital'


	def analog_pulse(self, hit_list = [], mode = 'edge', threshold = [50, 100], cal_pulse_amplitude = 255, initialise = True, trigger = False):
		if(initialise == True):
			self.ctrl.activate_readout_normal()
			self.ctrl.set_cal_pulse(amplitude = cal_pulse_amplitude, duration = 15, delay = 'keep')
			self.ctrl.set_threshold(threshold[0])
			self.ctrl.set_threshold_H(threshold[1])
			self.I2C.strip_write("DigCalibPattern_L", 0, 0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)
			#Configure_TestPulse_MPA_SSA(200, 1)
		if(mode != self.hitmode): # to speed up
			self.hitmode = mode
			self.strip.set_sampling_mode('all', mode)
		#enable pulse injection in selected clusters
		self.I2C.strip_write("ENFLAGS", 0, 0b00000)
		for cl in hit_list:
			if(cl > 0 and cl < 121):
				self.I2C.strip_write("ENFLAGS", cl, 0b10001)
				sleep(0.001)
		if(trigger == True):
			self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
			self.fc7.SendCommand_CTRL("start_trigger")
			sleep(0.01)
		sleep(0.001)
		utils.generic_parameters['ssa_inject_utility_mode'] = 'analog'


	def __initialise(self):
		self.hitmode = 'none'
		self.data_l = False
		self.data_r = False
		self.hit_list = []
		self.hip_list = []
		self.DigCalibPattern = 0
