from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from collections import OrderedDict

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_test_XRay():

	def __init__(self, ssa, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure;
		self.summary = results()
		self.config_file = "X-Ray/SSA_Configuration_Init.scv"

	def initialise(self):
		self.ssa.init(reset_board = True, reset_chip = True)
		self.scurve_trim_spread()
		#self.biascal.calibrate_to_nominals()
		self.ssa.ctrl.save_configuration(self.config_file, display=False)


	def test_routine(self, runname = 'OMrad'):
		time_init = time.time()
		fo = "../SSA_Results/X-Ray/" + runname + '_' + utils.date_time() + '_X-Ray_'
		self.ssa.init(reset_board = True, reset_chip = True)
		self.ssa.load_configuration(self.config_file, display = False)

		#self.test_routine_parameters(filename = fo, runname = runname)
		self.test_routine_digital(filename = fo, runname = runname)
		#self.test_routine_analog(filename = fo, runname = runname)
		self.summary.display(runname)
		self.summary.save(fo, runname)


	def test_routine_digital(self, filename = 'default', runname = '  0Mrad'):
		filename = self.summary.get_file_name(filename)

		r1, r2 = self.test.lateral_input_phase_tuning(display=False, file = filename, filemode = 'a', runname = runname)
		self.summary.set('Lateral_In_L', r1, '', '',  runname)
		self.summary.set('Lateral_In_R', r2, '', '',  runname)

		r1, r2, r3 = self.test.cluster_data_basic(mode = 'digital', shift = 0, shiftL = 0, display=False, file = filename, filemode = 'a', runname = runname)
		self.summary.set('Cluster_Data',         r1, '%', '',  runname)
		self.summary.set('Lateral_In_Clusters',  r2, '%', '',  runname)
		self.summary.set('Lateral_Out_Clusters', r3, '%', '',  runname)

	 	r1, r2, r3 = self.test.cluster_data_basic(mode = 'analog',  shift = 0, shiftL = 0, display=False, file = filename, filemode = 'a', runname = runname)
		self.summary.set('Pulse_Injection', r1, '%', '',  runname)

		r1 = self.test.memory(memory = 1, display= 0,  file = filename, filemode = 'a', runname = runname)
		self.summary.set('Memory_1', r1, '%', '',  runname)

		r1 = self.test.memory(memory = 2, display= 0,  file = filename, filemode = 'a', runname = runname)
		self.summary.set('Memory_2', r1, '%', '',  runname)

		r1, r2 = self.test.l1_data_basic(mode = 'digital', file = filename, filemode = 'a', runname = runname)
		self.summary.set('L1_data',    r1, '%', '',  runname)
		self.summary.set('HIP_flags',  r2, '%', '',  runname)



	def test_routine_analog(self, filename = 'default', runname = '  0Mrad'):
		filename = self.summary.get_file_name(filename)

		#r1, r2 = self.measure.baseline_noise(ret_average = True, plot = False, mode = 'all', filename = filename, runname = runname)
		#self.summary.set('noise_baseline' , r1, 'LSB', '',  runname)
		#self.summary.set('baseline_issues', r2, '#',   '',  runname)

		r1, r2, r3, r4 = self.measure.gain_offset_noise( ret_average = True, plot = False, use_stored_data = False, file = filename, filemode = 'a', runname = runname)
		self.summary.set('gain'          , r1, 'ThDAC/CalDAC', '',  runname)
		self.summary.set('offset'        , r2, 'ThDAC'       , '',  runname)
		self.summary.set('noise_scurve'  , r1, 'ThDAC/CalDAC', '',  runname)
		self.summary.set('scurve_issues' , r1, 'ThDAC/CalDAC', '',  runname)



	def test_routine_parameters(self, filename = 'default', runname = '  0Mrad'):
		filename = self.summary.get_file_name(filename)

		r1, r2, r3 = self.pwr.get_power(display=True)
		self.summary.set('Power_DVDD', r1, 'mW', '',  runname)
		self.summary.set('Power_AVDD', r2, 'mW', '',  runname)
		self.summary.set('Power_PVDD', r3, 'mW', '',  runname)

		r1 = self.biascal.measure_bias(return_data=True)
		for i in r1:
			self.summary.set( i[0], i[1], 'mV', '',  runname)





class results():

	class logpar():
		def __init__(self, name, value, unit = '', descr = '', run = ''):
			self.name = name
			self.unit = unit
			self.value = value
			self.descr = descr
			self.run = run

	def __init__(self):
		self.d = OrderedDict()
		self.summary = ["", ""]
		#self.clean()

	def set(self, name, value, unit = '', descr = '', run = 'Run-0'):
		self.d[name] = self.logpar(name, value, unit, descr, run)

	def update(self, runname = 'Run-0'):
		self.summary[0] = '\n%16s ; %24s ; %10s ; %16s ; %24s\n'  % ('RunName', 'Test', 'Results', 'Unit', 'Description' )
		self.summary[1] = '\n%24s   %10s %1s %24s\n'  % ('Test', 'Results', 'Unit', '' )
		for i in self.d:
			if (isinstance(self.d[i].value, bool)):
				temp = 'True' if self.d[i].value else 'False'
			elif( isinstance(self.d[i].value, int) or isinstance(self.d[i].value, float)):
				temp = '%8.3f' % (self.d[i].value)
			elif( isinstance(self.d[i].value, str)):
				temp = self.d[i].value
			else:
				temp = 'conversion error'
			self.summary[0] += '%16s ; %24s ; %10s ; %4s ; %24s\n'  % (self.d[i].run,   self.d[i].name,   temp,  self.d[i].unit,  self.d[i].descr)
			self.summary[1] += '%24s : %10s %4s %24s\n'  % (self.d[i].name,   temp,  self.d[i].unit,  self.d[i].descr)


	def display(self, runname = 'Run-0'):
		self.update(runname = runname)
		print self.summary[1]

	def save(self, filename = 'default', runname = 'Run-0'):
		self.update(runname = runname)
		filename = self.get_file_name(filename) + "Log.log"
		fo = open(filename, 'a')
		fo.write( self.summary[0] )
		fo.close()

	def get_file_name(self, filename):
		if(filename == 'default' or not isinstance(filename, str) ):
			fo = "../SSA_Results/X-Ray/" + utils.date_time() + '_X-Ray_'
		else:
			fo = filename
		return fo
