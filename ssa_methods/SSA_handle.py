
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_i2c_conf import *
import numpy as np
import time
import sys
import inspect
import matplotlib.pyplot as plt

class SSA_handle:

	def __init__(self):
		self.analog_mux_map    = analog_mux_map
		self.ssa_peri_reg_map  = ssa_peri_reg_map
		self.ssa_strip_reg_map = ssa_strip_reg_map
		#self.conf = ssa_i2c_conf()

	def set_output_mux(self, testline = 'highimpedence'):
		ctrl = self.analog_mux_map[testline]
		I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
		I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
		r = ((I2C.peri_read('Bias_TEST_LSB') & 0xff))
		r = ((I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			print "Error. Failed to set the trimming"
			return False
		else:
			return True

