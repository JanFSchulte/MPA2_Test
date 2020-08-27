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



class ssa_ctrl_builtin_selftest:

	def __init__(self, i2c, fc7, ctrl, strip, pwr, inject, readout, peri_reg_map, strip_reg_map, analog_mux_map):
		self.i2c = i2c
		self.fc7 = fc7
		self.ctrl = ctrl
		self.strip = strip
		self.pwr = pwr
		self.inject = inject
		self.readout = readout
		self.ssa_peri_reg_map = peri_reg_map
		self.ssa_strip_reg_map = strip_reg_map
		self.analog_mux_map = analog_mux_map

	#######################################################################
	def SRAM(self, memory_select=1, configure=True, display=1):
		bisterr = 0
		bistres = []
		if(memory_select == 1):   ctrl = 0x0f
		elif(memory_select == 2): ctrl = 0xf0
		else: return False
		if(configure):
			#self.reset(display=False)
			self.i2c.peri_write(register = 'mask_strip',  field = False, data=0xff)
			self.i2c.peri_write(register = 'mask_peri_D', field = False, data=0xff)
			self.i2c.peri_write(register = 'mask_peri_A', field = False, data=0xff)
			self.i2c.peri_write(register = 'ClkTree_control', field = False, data=0b01010100)
		self.i2c.peri_write(register = 'bist_memory_sram_mode',  field = False, data= 0x00 )
		self.i2c.peri_write(register = 'bist_memory_sram_start', field = False, data= 0x00 )
		self.i2c.peri_write(register = 'bist_memory_sram_mode',  field = False, data= ctrl )
		self.i2c.peri_write(register = 'bist_memory_sram_start', field = False, data= ctrl )
		time.sleep(0.010); #Time needed byt the BIST
		flag = self.i2c.peri_read( register = "bist_output", field=False)
		status = ((flag>>(1+memory_select))&0b1)
		if( status == 0):
			if(display): utils.print_error("->  BIST memory {:d} test not working. Return status {:2b}: ".format(memory_select, (flag>>2) ))
			bisterr=-1
		else:
			for N in range(0,16):
				if(memory_select==1):
					reg = "bist_memory_sram_output_L_{:X}".format(N)
				else:
					reg = "bist_memory_sram_output_H_{:X}".format(N)
				r = self.i2c.peri_read(register=reg, field=False)
				bistres.append(r)
				if(r != 0):
					bisterr += 1
			if( bisterr > 0 ):
				if(display):
					utils.print_warning("->  BIST memory {:d} test error: ".format(memory_select))
				for N in range(0,16):
					prstr = bin(bistres[N]) if isinstance(bistres[N], int) else str(bistres[N])
					if(display): print('    |- ' + prstr )
			else:
				if(display):
					utils.print_good("->  BIST memory {:d} test OK".format(memory_select))
		return bisterr


	#######################################################################
	def ring_oscilaltor(self, value=64, raw=0):
		if(value>127): value=127
		elif(value<0): value=0
		ringval = {'top-right':[0,0] , 'bottom-right':[0,0], 'bottom-center':[0,0], 'bottom-left':[0,0]}
		self.i2c.peri_write(register='Ring_oscillator_ctrl',  field ='start',  data=0b0)
		self.i2c.peri_write(register='Ring_oscillator_ctrl',  field ='lenght', data=value)
		self.i2c.peri_write(register='Ring_oscillator_ctrl',  field ='start',  data=0b1)
		time.sleep(0.1)
		ringval['bottom-right'][0] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locBR_T1_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locBR_T1_L'))
		ringval['bottom-right'][1] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locBR_T2_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locBR_T2_L'))
		ringval['top-right'][0] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locTR_T1_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locTR_T1_L'))
		ringval['top-right'][1] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locTR_T2_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locTR_T2_L'))
		ringval['bottom-center'][0] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locBC_T1_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locBC_T1_L'))
		ringval['bottom-center'][1] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locBC_T2_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locBC_T2_L'))
		ringval['bottom-left'][0] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locBL_T1_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locBL_T1_L'))
		ringval['bottom-left'][1] = utils.byte2int(
			b1=self.i2c.peri_read(register='Ring_oscillator_out_locBL_T2_H'),
			b0=self.i2c.peri_read(register='Ring_oscillator_out_locBL_T2_L'))
		self.i2c.peri_write(register='Ring_oscillator_ctrl',  field ='start',  data=0b0)
		if(not raw):
			rv = ringval
		else:
			rv = []
			for i in ringval: rv.append(ringval[i][0])
			for i in ringval: rv.append(ringval[i][1])
		return rv
