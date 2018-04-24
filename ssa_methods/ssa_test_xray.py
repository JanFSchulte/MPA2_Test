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

	def __init__(self, ssa, I2C, fc7, cal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;
		self.test = test; self.measure = measure;
		self.res = results()
		self.log = self.res.d


	def initialise(self):
		self.ssa.init(reset_board = True, reset_chip = True)


	def test_routine_digital(self, filename = 'default', runname = '  0Mrad'):
		filename = self.res.get_file_name(filename)

		r1, r2 = self.test.lateral_input_phase_tuning(display=False, file = filename, filemode = 'a', runname = runname)
		self.res.set('Lateral_In_L', r1, '', '',  runname)
		self.res.set('Lateral_In_R', r2, '', '',  runname)

		r1, r2, r3 = self.test.cluster_data_basic(mode = 'digital', shift = 0, shiftL = 0, display=False, file = filename, filemode = 'a', runname = runname)
		self.res.set('Cluster_Data',         r1, '%', '',  runname)
		self.res.set('Lateral_In_Clusters',  r2, '%', '',  runname)
		self.res.set('Lateral_Out_Clusters', r3, '%', '',  runname)

	 	r1, r2, r3 = self.test.cluster_data_basic(mode = 'analog',  shift = 0, shiftL = 0, display=False, file = filename, filemode = 'a', runname = runname)
		self.res.set('Pulse_Injection', r1, '%', '',  runname)

		r1 = self.test.memory(memory = 1, display= 0,  file = filename, filemode = 'a', runname = runname)
		self.res.set('Memory_1', r1, '%', '',  runname)

		r1 = self.test.memory(memory = 2, display= 0,  file = filename, filemode = 'a', runname = runname)
		self.res.set('Memory_2', r1, '%', '',  runname)

		r1, r2 = self.test.l1_data_basic(mode = 'digital', file = filename, filemode = 'a', runname = runname)
		self.res.set('L1_data',    r1, '%', '',  runname)
		self.res.set('HIP_flags',  r2, '%', '',  runname)



	def test_routine_analog(self, filename = 'default', runname = '  0Mrad'):
		filename = self.res.get_file_name(filename)
		noisemean, issues, noise = measure.baseline_noise(mode = 'all', filename = 'X-Ray/Prova', runname = runname)
		self.res.set('noise_baseline', noisemean); self.res.set('noise_baseline_issues', issues);


	def test_routine_parameters(self, filename = 'default', runname = '  0Mrad'):
		filename = self.res.get_file_name(filename)
		self.res.set('power'  , pwr.get_power(display=False))



class results():

	class logpar():
		def __init__(self, name, value, unit = '', descr = '', run = ''):
			self.name  = name
			self.unit  = unit
			self.value = value
			self.descr = descr
			self.run   = run

	def __init__(self):
		self.d = OrderedDict()
		#self.clean()

	def set(self, name, value, unit = '', descr = '', run = 'Run-0'):
		self.d[name] = self.logpar(name, value, unit, descr, run)

	def summary(self, runname = 'Run-0'):
		stro = '%16s ; %24s ; %10s ; %4s ; %24s\n'  % ('RunName', 'Test', 'Results', 'Unit', 'Description' )
		for i in self.d:
			if (isinstance(self.d[i].value, bool)):
				temp = 'True' if self.d[i].value else 'False'
			elif( isinstance(self.d[i].value, int) or isinstance(self.d[i].value, float)):
				temp = '%8.3f' % (self.d[i].value)
			elif( isinstance(self.d[i].value, str)):
				temp = self.d[i].value
			else:
				temp = 'conversion error'
			stro += '%16s ; %24s ; %10s ; %4s ; %24s\n'  % (
				self.d[i].run,   self.d[i].name,   temp,
				self.d[i].unit,  self.d[i].descr)

		#stro  = ''
		#stro += '%16s ; Power consuption DVDD   ; %7.2fmW ;\n'  % (runname, self.d['power'][0])
		#stro += '%16s ; Power consuption AVDD   ; %7.2fmW ;\n'  % (runname, self.d['power'][1])
		#stro += '%16s ; Power consuption PVDD   ; %7.2fmW ;\n'  % (runname, self.d['power'][2])
		#stro += '%16s ; Cluster data            ; %7.2f%%  ;\n' % (runname, self.d['cluster_data'][0])
		#stro += '%16s ; Lateral Input  Check L  ;    %s  ;\n'   % (runname, self.d['lateral_in'][0])
		#stro += '%16s ; Lateral Input  Check R  ;    %s  ;\n'   % (runname, self.d['lateral_in'][1])
		#stro += '%16s ; Lateral Input  Clusters ; %7.2f%%  ;\n' % (runname, self.d['cluster_data'][1])
		#stro += '%16s ; Lateral Output Clusters ; %7.2f%%  ;\n' % (runname, self.d['cluster_data'][2])
		#stro += '%16s ; Memory 1                ; %7.2f%%  ;\n' % (runname, self.d['mem_1'])
		#stro += '%16s ; Memory 2                ; %7.2f%%  ;\n' % (runname, self.d['mem_2'])
		#stro += '%16s ; L1 data                 ; %7.2f%%  ;\n' % (runname, self.d['l1_data'][0])
		#stro += '%16s ; HIP Flag data           ; %7.2f%%  ;\n' % (runname, self.d['l1_data'][1])
		return stro

	def display_summary(self):
		print self.get_results()

	def save_summary(self, filename = 'default'):
		filename = self.res.get_file_name(filename)
		fo = open(filename, 'a')
		fo.write( self.get_results() )
		fo.close()

	def get_file_name(self, filename):
		if(filename == 'default' or not isinstance(filename, str) ):
			fo = "X-Ray/" + utils.date_time() + '_X-Ray_'
		else:
			fo = filename
		return fo
