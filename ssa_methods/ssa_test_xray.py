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


class SSA_test_XRay():

	def __init__(self, ssa, I2C, fc7, cal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;
		self.test = test; self.measure = measure;
		self.initialise()

	def initialise(self):
		self.res = {}
		self.res['lateral_in']   = [False, False]
		self.res['cluster_data'] = [0, 0, 0]
		self.res['pulse_inject'] = [0, 0, 0]
		self.res['mem_1']        = 0
		self.res['mem_2']        = 0
		self.res['l1_data']      = [0, 0]


	def test_routine_digital(self, filename = 'default', runname = '  0Mrad'):
		if(filename == 'default'):
			filename = "X-Ray/" + utils.date_time() + '_X-Ray_'
		self.res['lateral_in']   = self.test.lateral_input_phase_tuning(display=False, file = filename, filemode = 'a', runname = runname)
		self.res['cluster_data'] = self.test.cluster_data_basic(mode = 'digital', shift = 0, shiftL = 0, display=False, file = filename, filemode = 'a', runname = runname)
		self.res['pulse_inject'] = self.test.cluster_data_basic(mode = 'analog',  shift = 0, shiftL = 0, display=False, file = filename, filemode = 'a', runname = runname)
		self.res['mem_1']        = self.test.memory(memory = 1, display= 0,  file = filename, filemode = 'a', runname = runname)
		self.res['mem_2']        = self.test.memory(memory = 2, display= 0,  file = filename, filemode = 'a', runname = runname)
		self.res['l1_data']      = self.test.l1_data_basic(mode = 'digital', file = filename, filemode = 'a', runname = runname)
		return self.res

	#def test_routine_analog(self, filename = 'default', runname = '  0Mrad'):



	def print_results(self):
		stro  = ''
		stro += 'Cluster data            ; %7.2f%% ;\n' % (self.res['cluster_data'][0])
		stro += 'Lateral Input  Chack    ;    %s ; %s ;\n' % (self.res['lateral_in'][0], self.res['lateral_in'][1])
		stro += 'Lateral Input  Clusters ; %7.2f%% ;\n' % (self.res['cluster_data'][1])
		stro += 'Lateral Output Clusters ; %7.2f%% ;\n' % (self.res['cluster_data'][2])
		stro += 'Memory 1                ; %7.2f%% ;\n' % (self.res['mem_1'])
		stro += 'Memory 2                ; %7.2f%% ;\n' % (self.res['mem_2'])
		stro += 'L1 data                 ; %7.2f%% ;\n' % (self.res['l1_data'][0])
		stro += 'HIP Flag data           ; %7.2f%% ;\n' % (self.res['l1_data'][1])
		return stro
