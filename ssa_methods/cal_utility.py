from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from ssa_methods.ssa_i2c_conf import *
import numpy as np
import time
import sys
import inspect

def print_method(name):
	lines = inspect.getsourcelines(name)
	print("".join(lines[0]))

def init_slvs():
	I2C.peri_write('SLVS_pad_current', 0b001)

def do_phase_tuning():
	fc7.write("ctrl_phy_phase_tune_again", 1)
	while(fc7.read("stat_phy_phase_tuning_done") == 0):
        	sleep(0.5)
        	print "Waiting for the phase tuning"	

def set_t1_sampling_edge(edge):
	if edge == "rising" or edge == "positive":
		I2C.peri_write('EdgeSel_T1', 1)
	elif edge == "falling" or edge == "negative":
		I2C.peri_write('EdgeSel_T1', 0)
	else:
		print "Error! The edge name is wrong"

def activate_readout_normal():
	I2C.peri_write('ReadoutMode',0b00)

def activate_readout_async():
	I2C.peri_write('ReadoutMode',0b01)

def activate_readout_shift():
        I2C.peri_write('ReadoutMode',0b10)

def set_shift_pattern_all(pattern):
	set_shift_pattern(pattern,pattern,pattern,pattern,pattern,pattern,pattern,pattern)

def set_shift_pattern(line0, line1, line2, line3, line4, line5, line6, line7):
	I2C.peri_write('OutPattern0',line0)
	I2C.peri_write('OutPattern1',line1)
	I2C.peri_write('OutPattern2',line2)
	I2C.peri_write('OutPattern3',line3)
	I2C.peri_write('OutPattern4',line4)
	I2C.peri_write('OutPattern5',line5)
	I2C.peri_write('OutPattern6',line6)
	I2C.peri_write('OutPattern7/FIFOconfig',line7)

def set_async_delay(value):
	msb = (value & 0xFF00) >> 8
	lsb = (value & 0x00FF) >> 0 
	I2C.peri_write('AsyncRead_StartDel_MSB', msb)
	I2C.peri_write('AsyncRead_StartDel_LSB', lsb)
	
