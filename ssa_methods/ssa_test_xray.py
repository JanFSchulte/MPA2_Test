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
			runtest.enable('Power')
			runtest.enable('Bias')
			runtest.enable('Bias_THDAC')
			runtest.enable('Bias_CALDAC')
			runtest.enable('Configuration')
			self.toptest.configure_tests( runtest )

	def initialise(self, filename):
		self.toptest.initialise(file = filename, plot = True)

	def xray_loop(self, filename, runtime = (60*60*100), rate = (30*60), init_wait = 0 ):
		self.configure_tests()
		self.pwr.set_dvdd(self.toptest.dvdd)
		self.ssa.init(reset_board = True, reset_chip = False, read_current = True)
		utils.activate_I2C_chip()
		time_init = time.time()
		time_base = time_init - (rate - init_wait);
		time_curr = time_init;

		while ((time_curr-time_init) < runtime):
			time_curr = time.time()
			if( float(time_curr-time_base) > float(rate) ):
				time_base = time_curr
				self.toptest.test_routine_main(filename = filename, runname = utils.date_time())
				utils.activate_I2C_chip()
			else:
				time.sleep(0.1);
				self.toptest.idle_routine(filename = filename, runname = utils.date_time())


	def set_start_irradiation_time(self, filename, ):
		print 'ciao'
