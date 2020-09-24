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
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure; self.toptest = toptest
		#self.biascal.set_gpib_address(12)


	def configure_tests(self, directory):
			runtest = RunTest('xray')
			runtest.set_enable('Power', 'ON')
			runtest.set_enable('Initialize', 'ON')
			runtest.set_enable('Calibrate', 'ON')
			runtest.set_enable('Bias', 'ON')
			runtest.set_enable('alignment', 'ON')
			runtest.set_enable('Lateral_In', 'ON')
			runtest.set_enable('Cluster_Data', 'ON')
			runtest.set_enable('Pulse_Injection', 'OFF')
			runtest.set_enable('L1_Data', 'ON')
			runtest.set_enable('Memory', 'ON')
			runtest.set_enable('noise_baseline', 'OFF')
			runtest.set_enable('trim_gain_offset_noise', 'ON')
			runtest.set_enable('DACs', 'ON')
			runtest.set_enable('Configuration', 'ON')
			runtest.set_enable('ring_oscillators', 'ON')
			runtest.set_enable('stub_l1_max_speed', 'ON')
			self.toptest.Configure(directory,  runtest )

	def xray_loop(self, runtime = 10E3, rate = 60*5, init_wait = 1, directory = '../SSA_Results/XRAY/' ):
		self.configure_tests(directory)
		time_init = time.time()
		time_base = time_init - (rate - init_wait);
		time_curr = time_init;
		while ((time_curr-time_init) < runtime):
			time_curr = time.time()
			if( float(time_curr-time_base) > float(rate) ):
				time_base = time_curr
				self.toptest.RUN(runname = utils.date_time())
				utils.print_info('->  Total run time: {:7.3f}'.format(time.time()-time_base) )
			else:
				self.toptest.idle_routine(filename = directory+'idle_routine', runname = utils.date_time(), duration=5)


	def set_start_irradiation_time(self, filename, ):
		print('ciao')
