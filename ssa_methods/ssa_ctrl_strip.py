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

class ssa_ctrl_strip:

	def __init__(self, I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.analog_mux_map    = analog_mux_map
		self.ssa_peri_reg_map  = ssa_peri_reg_map
		self.ssa_strip_reg_map = ssa_strip_reg_map
		self.I2C               = I2C
		self.fc7               = FC7
		self.dll_chargepump    = 0b00

	def set_enable(self, strip, enable, polarity = 0, hitcounter = 0, digitalpulse = 0, analogpulse = 0):
		if(strip == 'all'):
			strip = 0
		value =((0b1 & analogpulse  ) << 4 |
			(0b1 & digitalpulse ) << 3 |
			(0b1 & hitcounter   ) << 2 |
			(0b1 & polarity     ) << 1 |
			(0b1 & enable       ) << 0)
		r = self.I2C.strip_write("ENFLAGS", strip, value)

	def set_trimming(self, strip, value):
		value = value & 0b11111
		if(strip == 'all'):
			strip = 0
		self.I2C.strip_write("THTRIMMING", strip, value)

	def get_trimming(self, strip):
		r = self.I2C.strip_read("THTRIMMING", strip)
		return r

	def set_gain_trimming(self, strip, value):
		value = value & 0b11111
		if(strip == 'all'): strip = 0
		self.I2C.strip_write("GAINTRIMMING", strip, value)

	def set_sampling_mode(self, strip, mode):
		if(strip == 'all'): strip = 0
		done = True
		if(mode == 'edge'):
			self.I2C.strip_write("SAMPLINGMODE", strip, 0b00)
		elif(mode == 'level'):
			self.I2C.strip_write("SAMPLINGMODE", strip, 0b01)
		elif (mode == 'or'):
			self.I2C.strip_write("SAMPLINGMODE", strip, 0b10)
		elif (mode == 'xor'):
			self.I2C.strip_write("SAMPLINGMODE", strip, 0b11)
		else:
			done = False
		return done

	def set_cal_strips(self, mode = 'counter', strip = 'all'):
		if  (mode == 'counter'):
			activeval = 0b10101
		elif(mode == 'analog'):
			activeval = 0b10001
		elif(mode == 'digital'):
		 activeval = 0b01001
		else: exit(1)
		if(strip == 'all'):
			self.I2C.strip_write("ENFLAGS", 0, activeval)
		elif(strip == 'none'):
			self.I2C.strip_write("ENFLAGS", 0, 0b00001)
		elif(isinstance(strip, list)):
			self.I2C.strip_write("ENFLAGS", 0, 0b00000)
			for s in strip:
				self.I2C.strip_write("ENFLAGS", s, activeval)
		elif(isinstance(strip, int)):
			self.I2C.strip_write("ENFLAGS", 0, 0b00000)
			self.I2C.strip_write("ENFLAGS", strip, activeval)
		else:
			exit(1)

	def set_polarity(self, pol, strip = 'all'):
		if (strip == 'all'):
			strip = range(1,121)
		elif(isinstance(strip, int)):
			strip = [strip]
		elif(not isinstance(strip, list)):
			return False
		for i in strip:
			r = self.I2C.strip_read("ENFLAGS", i)
			val = (r&0b11101) | (pol<<1)
			self.I2C.strip_write("ENFLAGS", i, val)
		return True

	def set_hipcut(self, value = 'default', strip = 'all'):
		if(value == 'disable'):
			value = 7
		if(value == 'default'):
			value = 1
		elif(not isinstance(value, int)):
			return False
		if(strip == 'all'):
			self.I2C.strip_write("HIPCUT", 0, value)
		elif(isinstance(strip, int)):
			self.I2C.strip_write("HIPCUT", strip, value)
		elif(isinstance(strip, list)):
			for i in strip:
				self.I2C.strip_write("HIPCUT", i, value)
		else:
			return False
		return True
