import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt

from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.tbsettings import *


class ssa_ctrl_strip:

	def __init__(self, I2C, FC7):
		self.I2C               = I2C
		self.fc7               = FC7
		self.dll_chargepump    = 0b00

	def set_enable(self, strip, enable, polarity = 0, hitcounter = 0, digitalpulse = 0, analogpulse = 0):
		value =((0b1 & analogpulse  ) << 4 |
			(0b1 & digitalpulse ) << 3 |
			(0b1 & hitcounter   ) << 2 |
			(0b1 & polarity     ) << 1 |
			(0b1 & enable       ) << 0)
		if(tbconfig.VERSION['SSA'] >= 2):
			r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=strip, data=value)
		else:
			r = self.I2C.strip_write("ENFLAGS", strip, value)

	def set_trimming(self, strip, value):
		value = value & 0b11111
		if(tbconfig.VERSION['SSA'] >= 2):
			r = self.I2C.strip_write(register="ThresholdTrimming", field=False, strip=strip, data=value)
		else:
			if(strip == 'all'): strip = 0
			r = self.I2C.strip_write("THTRIMMING", strip, value)
		return r

	def get_trimming(self, strip):
		if(tbconfig.VERSION['SSA'] >= 2):
			r = self.I2C.strip_read(register="ThresholdTrimming", field=False, strip=strip)
		else:
			r = self.I2C.strip_read("THTRIMMING", strip)
		return r

	def set_gain_trimming(self, strip, value):
		value = value & 0b11111
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write( register="StripControl2", field='GainTrimming', strip=strip, data=value)
		else:
			if(strip == 'all'): strip = 0
			self.I2C.strip_write("GAINTRIMMING", strip, value)

	def set_sampling_mode(self, strip, mode):
		if(tbconfig.VERSION['SSA'] >= 2):
			if(mode == 'edge'):
				r = self.I2C.strip_write(register="StripControl1", field='Sampling_Mode', strip=strip, data=0b00)
			elif(mode == 'level'):
				r = self.I2C.strip_write(register="StripControl1", field='Sampling_Mode', strip=strip, data=0b01)
			elif (mode == 'or'):
				r = self.I2C.strip_write(register="StripControl1", field='Sampling_Mode', strip=strip, data=0b10)
			elif (mode == 'xor'):
				r = self.I2C.strip_write(register="StripControl1", field='Sampling_Mode', strip=strip, data=0b11)
			else:
				r = False
		else:
			r = True
			if(strip == 'all'):
				strip = 0
			if(mode == 'edge'):
				self.I2C.strip_write("SAMPLINGMODE", strip, 0b00)
			elif(mode == 'level'):
				self.I2C.strip_write("SAMPLINGMODE", strip, 0b01)
			elif (mode == 'or'):
				self.I2C.strip_write("SAMPLINGMODE", strip, 0b10)
			elif (mode == 'xor'):
				self.I2C.strip_write("SAMPLINGMODE", strip, 0b11)
			else:
				r = False
		return r

	def set_cal_strips(self, mode = 'counter', strip = 'all'):
		if  (mode == 'counter'):
			activeval = 0b10101
		elif(mode == 'analog'):
			activeval = 0b10001
		elif(mode == 'digital'):
			activeval = 0b01001
		else: exit(1)
		if(tbconfig.VERSION['SSA'] >= 2):
			if(strip == 'all'):
				r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=activeval)
			elif(strip == 'none'):
				r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b00001)
			elif(isinstance(strip, list)):
				r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b00000)
				for s in strip:
					r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=s, data=activeval)
			elif(isinstance(strip, int)):
				self.I2C.strip_write("ENFLAGS", 0, 0b00000)
				r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b00000)
				r = self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=strip, data=activeval)
			else:
				print("X>  \tSet_cal_strips error. Wrong strip format specified")
				return False
			return r
		else:
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
				print("X>  \tSet_cal_strips error. Wrong strip format specified")
				return False
			return True

	def set_polarity(self, pol, strip = 'all'):
		if (strip == 'all'):
			strip = range(1,121)
		elif(isinstance(strip, int)):
			strip = [strip]
		elif(not isinstance(strip, list)):
			return False
		for i in strip:
			if(tbconfig.VERSION['SSA'] >= 2):
				r = self.I2C.strip_read(register="StripControl1", field='ENFLAGS', strip=i)
			else:
				r = self.I2C.strip_read("ENFLAGS", i)
			val = (r&0b11101) | (pol<<1)
			if(tbconfig.VERSION['SSA'] >= 2):
				self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=i, data=val)
			else:
				self.I2C.strip_write("ENFLAGS", i, val)
		return True

	def set_hipcut(self, value = 'default', strip = 'all'):
		if(value == 'disable'):
			value = 7
		if(value == 'default'):
			value = 1
		elif(not isinstance(value, int)):
			return False
		if(tbconfig.VERSION['SSA'] >= 2):
			if(strip == 'all'):
				self.I2C.strip_write(register="StripControl2", field='HIP_Cut', strip='all', data=value)
			elif(isinstance(strip, int)):
				self.I2C.strip_write(register="StripControl2", field='HIP_Cut', strip=strip, data=value)
			elif(isinstance(strip, list)):
				for i in strip:
					self.I2C.strip_write(register="StripControl2", field='HIP_Cut', strip=i, data=value)
			else:
				return False
		else:
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
