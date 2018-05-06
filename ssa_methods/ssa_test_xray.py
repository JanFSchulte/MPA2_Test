from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from collections import OrderedDict
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_test_xray():

	def __init__(self, toptest, ssa, I2C, fc7, cal, biascal, pwr, test, measure):
		self.toptest = toptest
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure;


	def configure_tests(self):
			runtest = RunTest('xray')
			runtest.enable('Lateral_In')
			runtest.enable('Cluster_Data')
			runtest.enable('Pulse_Injection')
			runtest.enable('Cluster_Data2')
			runtest.enable('Memory_1')
			runtest.enable('Memory_2')
			runtest.enable('L1_data')
			runtest.disable('memory_vs_voltage')
			runtest.enable('noise_baseline')
			runtest.enable('gain_offset_noise')
			runtest.enable('threshold_spread')
			runtest.enable('Bias_THDAC')
			runtest.enable('Bias_CALDAC')
			self.toptest.configure_tests( runtest )


	def xray_loop(self, filename, runtime = (60*60*114), rate = (30*60) ):
		time_init = time.time()
		time_base = time_init; time_curr = time_init;
		self.configure_tests()
		iteration = 0
		self.toptest.test_routine_main(filename = filename, runname = utils.date_time())
		while ((time_curr-time_init) < runtime):
			time_curr = time.time()
			if( float(time_curr-time_base) > float(rate) ):
				time_base = time_curr
				iteration += 1
				self.toptest.test_routine_main(filename = filename, runname = utils.date_time())
			else:
				self.idle_routine()


	def set_start_irradiation_time(self, filename, ):
		print 'ciao'


	def idle_routine(self):
		try:
			self.test.cluster_data_basic(mode = 'analog',  shift = -2, shiftL = -2, display=False, file = '../SSA_Results/temp', filemode = 'w', runname = '')
			self.test.l1_data_basic(mode = 'digital', shift = 0, file = '../SSA_Results/temp', filemode = 'w', runname = '')
		except:
			print '========= ERROR ========'
