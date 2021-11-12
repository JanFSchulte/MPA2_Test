import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import copy
import seaborn as sns
from random import randint
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)

from utilities.tbsettings import *
from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
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
	def set_output_mux(self, testline = 'highimpedence', testpad_enable=1):
		if(tbconfig.VERSION['SSA'] >= 2):
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write(    register="ADC_trimming", field='TestPad_Enable',        data=testpad_enable)
			self.I2C.peri_write(    register="ADC_control",  field='ADC_control_input_sel', data=ctrl)
			r = self.I2C.peri_read( register="ADC_control",  field='ADC_control_input_sel')
		else:
			#utils.activate_I2C_chip(self.fc7)
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write('Bias_TEST_LSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_MSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
			self.I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
			r = ((self.I2C.peri_read('Bias_TEST_LSB') & 0xff))
			r = ((self.I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			utils.print_error("Error. Failed to set the MUX")
			return False
		else:
			return True

	#####################################################################
	def adc_measure(self, testline = 'highimpedence', testpad_enable=False, nsamples=1, fast=True, reinit_if_error=True, raw=False):
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
			r1.append( self._adc_measure(testline=testline, fast=fast, reinit_if_error=reinit_if_error) )
		if(raw): return r1
		else:
			if(nsamples>1): r = np.sum(r1) / float(nsamples)
			else: r = r1[0]
		return r

	#####################################################################
	def _adc_measure(self, testline = 'highimpedence', fast=True, reinit_if_error=True):
		#start=time.time()
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
			utils.print_error("Error. Failed to use the ADC")
			return False
		time.sleep(0.001)
		msb = self.I2C.peri_read( register="ADC_out_H", field=False )
		lsb = self.I2C.peri_read( register="ADC_out_L", field=False )
		#print('{:8.3f} ms'.format(1E3*(time.time()-start))); start=time.time()
		if((msb==None) or (lsb==None) or (msb=='Null') or (lsb=='Null') ):
			utils.activate_I2C_chip(self.fc7)
			if(reinit_if_error):
				msb = self.I2C.peri_read( register="ADC_out_H", field=False )
				lsb = self.I2C.peri_read( register="ADC_out_L", field=False )
			else:
				msb = 0
				lsb = 0
		if((msb==None) or (lsb==None) or (msb=='Null') or (lsb=='Null') ):
			return False
		res = ((msb<<8) | lsb)
		return res


	#####################################################################
	def adc_set_trimming(self, value):
		r = self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable',        data=0b1 )
		r = self.I2C.peri_write( register="ADC_trimming", field='ADC_trimming_trim_sel', data=0b1 )
		r = self.I2C.peri_write( register="ADC_trimming", field='ADC_trimming_trim_val', data=value )
		r = self.I2C.peri_read(  register="ADC_trimming", field='ADC_trimming_trim_val' )
		return r

	#####################################################################
	def adc_set_referenence(self, value):
		r = self.I2C.peri_write( register="ADC_VREF", field='ADC_VREF', data=value)
		return r

	#####################################################################
	def adc_get_trimming(self):
		r = self.I2C.peri_read(  register="ADC_trimming", field='ADC_trimming_trim_val' )
		return r

	#####################################################################
	def adc_measure_temperature(self, nsamples=10, raw=False):
		return self.adc_measure(testline='Temperature', nsamples=nsamples, raw=raw)

	#####################################################################
	def adc_measure_THDAC(self, nsamples=10):
		r1 = self.adc_measure('Bias_THDAC', nsamples=nsamples)
		r2 = self.adc_measure('Bias_THDACHIGH', nsamples=nsamples)
		return [r1, r2]

	#####################################################################
	def adc_measure_CALDAC(self, nsamples=10):
		return self.adc_measure('Bias_CALDAC', nsamples=nsamples)

	#####################################################################
	def adc_measure_supply(self, nsamples=1, raw = True, display=True):
		r = np.zeros(6)
		r[0] = self.adc_measure('DVDD', nsamples=nsamples)
		r[1] = self.adc_measure('AVDD', nsamples=nsamples)
		r[2] = self.adc_measure('PVDD', nsamples=nsamples)
		r[3] = self.adc_measure('GND',  nsamples=nsamples)
		r[4] = self.adc_measure('VBG',  nsamples=nsamples)
		r[5] = self.adc_measure('Temperature',  nsamples=nsamples)
		if(not raw):
			r = [r[0]/(2**11), r[1]/(2**11), r[2]/(2**11), r[3], r[4], r[5]]   # 12 bit ADC e partitore 1/2
		if(display):
			utils.print_log('->  ADC measure - DVDD    : {:5d}'.format(int(r[0])))
			utils.print_log('->  ADC measure - AVDD    : {:5d}'.format(int(r[1])))
			utils.print_log('->  ADC measure - PVDD    : {:5d}'.format(int(r[2])))
			utils.print_log('->  ADC measure - GND     : {:5d}'.format(int(r[3])))
			utils.print_log('->  ADC measure - VBG     : {:5d}'.format(int(r[4])))
			utils.print_log('->  ADC measure - Temp    : {:5d}'.format(int(r[5])))
		return r

	#####################################################################
	def adc_measure_ext_pad(self, nsamples=10, reinit_if_error=True):
		#start = time.time()
		rp = self.adc_measure(testline='TESTPAD', testpad_enable=True, nsamples=nsamples, fast=True, reinit_if_error=reinit_if_error )
		#utils.print_log('{:8.3f} ms'.format(1E3*(time.time()-start)))
		return rp


# ssa_peri_reg_map['Fuse_Mode']              = 43
# ssa_peri_reg_map['Fuse_Prog_b0']           = 44
# ssa_peri_reg_map['Fuse_Prog_b1']           = 45
# ssa_peri_reg_map['Fuse_Prog_b2']           = 46
# ssa_peri_reg_map['Fuse_Prog_b3']           = 47
# ssa_peri_reg_map['Fuse_Value_b0']          = 48
# ssa_peri_reg_map['Fuse_Value_b1']          = 49
# ssa_peri_reg_map['Fuse_Value_b2']          = 50
# ssa_peri_reg_map['Fuse_Value_b3']          = 51
