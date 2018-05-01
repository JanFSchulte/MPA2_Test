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

runtest.enable('Lateral_In')
runtest.enable('Cluster_Data')
runtest.enable('Pulse_Injection')
runtest.enable('Memory_1')
runtest.enable('Memory_2')
runtest.enable('L1_data')
runtest.enable('memory_vs_voltage')
runtest.enable('noise_baseline')
runtest.enable('gain_offset_noise')
runtest.enable('threshold_spread')


class SSA_test_XRay():

	def __init__(self, ssa, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure;
		self.summary = results()
		self.config_file = ''
		self.dvdd = 1.0

	def initialise(self, file = False, plot = False):
		self.ssa.init(reset_board = True, reset_chip = True)
		self.biascal.calibrate_to_nominals()
		self.measure.scurve_trim(plot = plot, filename = file + '_Init')
		if (isinstance(file, str)):
			configfile = '../SSA_Results/' + file + '_Configuration_Init.scv'
			self.config_file = configfile
		else:
			configfile = self.config_file
		self.ssa.save_configuration(configfile, display=False)


	def test_routine(self, filename, runname = 'OMrad'):
		time_init = time.time()
		#fo = "../SSA_Results/X-Ray/" + runname + '_' + utils.date_time() + '_X-Ray_'
		if(self.config_file == ''):
			self.config_file = '../SSA_Results/' + filename + '_Configuration_Init.scv'
		fo = filename
		self.pwr.set_dvdd(self.dvdd)
		self.ssa.init(reset_board = True, reset_chip = True)
		self.ssa.load_configuration(self.config_file, display = False)
		self.test_routine_parameters(filename = fo, runname = runname)
		self.test_routine_analog(filename = fo, runname = runname)
		self.test_routine_digital(filename = fo, runname = runname)
		self.summary.display(runname)
		self.summary.save(fo, runname)
		print "->  \tRun time = %7.2f" % (time.time() - time_init)



	def test_routine_parameters(self, filename = 'default', runname = '  0Mrad'):
		filename = self.summary.get_file_name(filename)

		r1, r2, r3 = self.pwr.get_power(display=True)
		self.summary.set('Power_DVDD', r1, 'mW', '',  runname)
		self.summary.set('Power_AVDD', r2, 'mW', '',  runname)
		self.summary.set('Power_PVDD', r3, 'mW', '',  runname)

		r1 = self.biascal.measure_bias(return_data=True)
		for i in r1:
			self.summary.set( i[0], i[1], 'mV', '',  runname)



	def test_routine_digital(self, filename = 'default', runname = '  0Mrad', shift = [0,0,-1,-1,0,0]):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()

		while runtest.is_active('Lateral_In'):
			try:
				r1, r2 = self.test.lateral_input_phase_tuning(display=False, file = filename, filemode = 'a', runname = runname, shift = 0)
				self.summary.set('Lateral_In_L', r1, '', '',  runname)
				self.summary.set('Lateral_In_R', r2, '', '',  runname)
				print "->  \tlateral_input_phase_tuning test Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in lateral_input_phase_tuning test. Reiterating."
		while runtest.is_active('Cluster_Data'):
			try:
				r1, r2, r3 = self.test.cluster_data_basic(mode = 'digital', shift = shift[0], shiftL = shift[1], display=False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('Cluster_Data',         r1, '%', '',  runname)
				self.summary.set('Lateral_In_Clusters',  r2, '%', '',  runname)
				self.summary.set('Lateral_Out_Clusters', r3, '%', '',  runname)
				print "->  \tcluster_data_basic test Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in cluster_data_basic test. Reiterating."
		while runtest.is_active('Pulse_Injection'):
			try:
			 	r1, r2, r3 = self.test.cluster_data_basic(mode = 'analog',  shift = shift[2], shiftL = shift[3], display=False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('Pulse_Injection', r1, '%', '',  runname)
				print "->  \tPulse_Injection test Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in Pulse_Injection test. Reiterating."
		while runtest.is_active('Memory_1'):
			try:
				r1 = self.test.memory(memory = 1, shift = shift[4], display= 0,  file = filename, filemode = 'a', runname = runname)
				self.summary.set('Memory_1', r1, '%', '',  runname)
				print "->  \tMemory_1 test Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in Memory_1 test. Reiterating."
		while runtest.is_active('Memory_2'):
			try:
				r1 = self.test.memory(memory = 2, shift = shift[4], display= 0,  file = filename, filemode = 'a', runname = runname)
				self.summary.set('Memory_2', r1, '%', '',  runname)
				print "->  \tMemory_2 test Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in Memory_2 test. Reiterating."
		while runtest.is_active('L1_data'):
			try:
				r1, r2 = self.test.l1_data_basic(mode = 'digital', shift = shift[5], file = filename, filemode = 'a', runname = runname)
				self.summary.set('L1_data',    r1, '%', '',  runname)
				self.summary.set('HIP_flags',  r2, '%', '',  runname)
				print "->  \tl1_data_basic Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in l1_data_basic test. Reiterating."
		while runtest.is_active('memory_vs_voltage'):
			try:
				self.test.memory_vs_voltage(memory = 1, step = 0.005, start = 1.25, stop = 0.9, latency = 200, shift = 0, file = filename, filemode = 'a', runname = runname)
				print "->  \t memory_vs_voltage Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				self.pwr.set_dvdd(self.dvdd)
				break
			except:
				print "X>  \tError in memory_vs_voltage test. Reiterating."
		#self.summary.display(runname)
		#self.summary.save(filename, runname)


	def test_routine_analog(self, filename = 'default', runname = '  0Mrad'):

		filename = self.summary.get_file_name(filename)
		time_init = time.time()

		while runtest.is_active('noise_baseline'):
			try:
				self.ssa.load_configuration(self.config_file, display = False)
				r1, r2 = self.measure.baseline_noise(ret_average = True, plot = False, mode = 'all', filename = filename, runname = runname, filemode = 'a')
				self.summary.set('noise_baseline' , r1, 'LSB', '',  runname)
				self.summary.set('baseline_issues', r2, '#',   '',  runname)
				print "->  \tl1_data_basic Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in baseline_noise test. Reiterating."
		while runtest.is_active('gain_offset_noise'):
			try:
				self.ssa.load_configuration(self.config_file, display = False)
				r1, r2, r3, r4 = self.measure.gain_offset_noise(calpulse = 50, ret_average = True, plot = False, use_stored_data = False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('gain'          , r1, 'ThDAC/CalDAC', '',  runname)
				self.summary.set('offset'        , r2, 'ThDAC'       , '',  runname)
				self.summary.set('noise_scurve'  , r1, 'ThDAC/CalDAC', '',  runname)
				self.summary.set('scurve_issues' , r1, 'ThDAC/CalDAC', '',  runname)
				print "->  \tgain_offset_noise Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in gain_offset_noise test. Reiterating."
		while runtest.is_active('threshold_spread'):
			try:
				r1 = self.measure.threshold_spread(calpulse = 50, use_stored_data = True, plot = False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('threshold std' , r1, 'ThDAC', '',  runname)
				print "->  \tthreshold_spread Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in threshold_spread test. Reiterating."



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
		self.summary = ["", "", ""]
		#self.clean()

	def set(self, name, value, unit = '', descr = '', run = 'Run-0'):
		self.d[name] = self.logpar(name, value, unit, descr, run)

	def update(self, runname = 'Run-0'):
		self.summary[0] = '\n%16s ; %24s ; %10s ; %16s ; %24s\n'  % ('RunName', 'Test', 'Results', 'Unit', 'Description' )
		self.summary[1] = '\n%24s   %10s %1s %24s\n'  % ('Test', 'Results', 'Unit', '' )
		self.summary[2] = '\n%16s ; ' % (runname)
		for i in self.d:
			if (isinstance(self.d[i].value, bool)):
				temp = 'True' if self.d[i].value else 'False'
			elif( isinstance(self.d[i].value, int) or isinstance(self.d[i].value, float)):
				temp = '%8.3f' % (self.d[i].value)
			elif( isinstance(self.d[i].value, str)):
				temp = self.d[i].value
			elif( isinstance(self.d[i].value, np.ndarray) or isinstance(self.d[i].value, list)):
				temp = str(self.d[i].value)
			else:
				temp = 'conversion error'
			self.summary[0] += '%16s ; %24s ; %10s ; %4s ; %24s\n'  % (self.d[i].run,   self.d[i].name,   temp,  self.d[i].unit,  self.d[i].descr)
			self.summary[1] += '%24s : %10s %4s %24s\n'  % (self.d[i].name,   temp,  self.d[i].unit,  self.d[i].descr)
			self.summary[2] += '%16s ; ' % (temp)

	def display(self, runname = 'Run-0'):
		self.update(runname = runname)
		print self.summary[1]

	def save(self, filename = 'default', runname = 'Run-0'):
		self.update(runname = runname)
		filename1 = '../SSA_Results/' + self.get_file_name(filename) + "_Log.log"
		filename2 = '../SSA_Results/' + self.get_file_name(filename) + "_GlobalLog.csv"
		fo1 = open(filename1, 'a'); fo2 = open(filename2, 'a');
		fo1.write( self.summary[0]); fo2.write( self.summary[2]);
		fo1.close(); fo2.close()

	def get_file_name(self, filename):
		if(filename == 'default' or not isinstance(filename, str) ):
			fo = "../SSA_Results/X-Ray/" + utils.date_time() + '_X-Ray_'
		else:
			fo = filename
		return fo
