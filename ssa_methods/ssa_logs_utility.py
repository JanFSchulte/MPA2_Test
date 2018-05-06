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




class RunTest():

	def __init__(self, configname = 'default'):
		self.test = {}
		self.configname = configname
		if(configname != 'default'):
			print '->  \tTest Configuration object [' + str(self.configname) + '] created.'

	def enable(self, name):
		 self.test[name] = True

	def disable(self, name):
		self.test[name] = False

	def is_active(self, name):
		if(not name in self.test):
			return False
		else:
			r = self.test[name]
			if(r):
				print "------- Running test: " + str(name)
			return r

	def __del__(self):
		print '->  \tTest Configuration object [' + str(self.configname) + '] replaced.'
