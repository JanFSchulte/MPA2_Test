import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import copy
from random import randint

from utilities.tbsettings import *
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *


class ssa_ctrl_analog:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map;
		self.analog_mux_map = analog_mux_map;
		self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
		self.dll_chargepump = 0b00;
		self.bias_dl_enable = False
		self.seu_check_time = -1
		self.testpad_is_enable = -1
		self.seu_cntr = { 'A':{'peri':[0]*2, 'strip':[0]*8, 'all':0}, 'S':{'peri':[0]*2, 'strip':[0]*8, 'all':0} }

	#####################################################################
	def set_output_mux(self, testline = 'highimpedence'):
		if(tbconfig.VERSION['SSA'] >= 2):
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write(    register="ADC_trimming", field='TestPad_Enable',        data=0b1)
			self.I2C.peri_write(    register="ADC_control",  field='ADC_control_input_sel', data=ctrl)
			r = self.I2C.peri_read( register="ADC_control",  field='ADC_control_input_sel')
		else:
			#utils.activate_I2C_chip()
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write('Bias_TEST_LSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_MSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
			self.I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
			r = ((self.I2C.peri_read('Bias_TEST_LSB') & 0xff))
			r = ((self.I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			print("Error. Failed to set the MUX")
			return False
		else:
			return True

	#####################################################################
	def _adc_measeure(self, testline = 'highimpedence', fast=True):
		#tinit=time.time()
		input_sel = self.analog_mux_map[testline]
		if(fast):
			r =    self.I2C.peri_write( register="ADC_control", field=False, data=(0b11100000 | (input_sel & 0b00011111)) )
			r = r| self.I2C.peri_write( register="ADC_control", field=False, data=(0b11000000 | (input_sel & 0b00011111)) )
		else:
			r =    self.I2C.peri_write( register="ADC_control", field=False                     , data=0x00)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_reset'       , data=0b1)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_reset'       , data=0b0)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_input_sel'   , data=input_sel)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_enable_start', data=0b11)
		if(not r):
			print("Error. Failed to use the ADC")
			return False
		msb = self.I2C.peri_read( register="ADC_out_H", field=False )
		lsb = self.I2C.peri_read( register="ADC_out_L", field=False )
		if((msb==None) or (lsb==None)):
			res = False
		else:
			res = ((msb<<8) | lsb)
		#print((time.time()-tinit)*1000); tinit=time.time()
		return res

	#####################################################################
	def adc_measeure(self, testline = 'highimpedence', testpad_enable=False, nsamples=1, fast=True):
		r1 = []
		# default: self.testpad_is_enable = -1
		if(testpad_enable or (testline=='TESTPAD')):
			if(self.testpad_is_enable!=1): #to speedup
				self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable', data=0b1 )
				self.testpad_is_enable = 1
		else:
			if(self.testpad_is_enable!=0): #to speedup
				self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable', data=0b0)
				self.testpad_is_enable = 0
		for i in range(nsamples):
			r1.append( self._adc_measeure(testline=testline, fast=fast) )
		if(nsamples>1):
			r = np.sum(r1) / float(nsamples)
		else:
			r = r1[0]
		return r

	#####################################################################
	def adc_set_trimming(self, value):
		r = self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable',        data=0b1 )
		r = self.I2C.peri_write( register="ADC_trimming", field='ADC_trimming_trim_sel', data=0b1 )
		r = self.I2C.peri_write( register="ADC_trimming", field='ADC_trimming_trim_val', data=value )
		r = self.I2C.peri_read(  register="ADC_trimming", field='ADC_trimming_trim_val' )
		return r

	#####################################################################
	def adc_get_trimming(self):
		r = self.I2C.peri_read(  register="ADC_trimming", field='ADC_trimming_trim_val' )
		return r

	#####################################################################
	def adc_measure_temperature(self, nsamples=10):
		return self.adc_measeure('Temperature', nsamples=nsamples)

	#####################################################################
	def adc_measure_THDAC(self, nsamples=10):
		r1 = self.adc_measeure('Bias_THDAC', nsamples=nsamples)
		r2 = self.adc_measeure('Bias_THDACHIGH', nsamples=nsamples)
		return [r1, r2]

	#####################################################################
	def adc_measure_CALDAC(self, nsamples=10):
		return self.adc_measeure('Bias_CALDAC', nsamples=nsamples)

	#####################################################################
	def adc_measure_supply(self, nsamples=1, raw = True):
		r = np.zeros(4)
		r[0] = self.adc_measeure('DVDD', nsamples=nsamples)
		r[1] = self.adc_measeure('AVDD', nsamples=nsamples)
		r[2] = self.adc_measeure('PVDD', nsamples=nsamples)
		r[3] = self.adc_measeure('GND',  nsamples=nsamples)
		if(not raw):
			r = r/(2**11) # 12 bit ADC e partitore 1/2
		return r



# ssa_peri_reg_map['Fuse_Mode']              = 43
# ssa_peri_reg_map['Fuse_Prog_b0']           = 44
# ssa_peri_reg_map['Fuse_Prog_b1']           = 45
# ssa_peri_reg_map['Fuse_Prog_b2']           = 46
# ssa_peri_reg_map['Fuse_Prog_b3']           = 47
# ssa_peri_reg_map['Fuse_Value_b0']          = 48
# ssa_peri_reg_map['Fuse_Value_b1']          = 49
# ssa_peri_reg_map['Fuse_Value_b2']          = 50
# ssa_peri_reg_map['Fuse_Value_b3']          = 51
