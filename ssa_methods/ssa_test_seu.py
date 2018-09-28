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
import numpy as np
import matplotlib.pyplot as plt
import ctypes


class SSA_SEU():

	def __init__(self, ssa, seuutil, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.seuutil = seuutil; self.fc7 = fc7; self.cal = cal;
		self.pwr = pwr;   self.test = test; self.biascal = biascal; self.measure = measure;
		self.init_parameters()

	def init_parameters(self):
		self.summary = results()
		self.runtest = RunTest('default')
		self.l1_latency = [101, 351, 501]
		self.run_time = 0.5 #sec


	def set_tun(self):
		self.ion  = input("ION?    ")
		self.tilt = input("LTI?    ")

	def run_info(self):
		return 'prova'

	def main_test(self, filename = 'Try', folder = 'PROVA0'):

		runname = self.run_info()
		logfile = "../SSA_Results/SEU/" + folder + "/" + filename

		striplist = []
		iteration = 0
		stavailable = range(1,121)

		for latency in self.l1_latency:
			for rp in range(5):

				self.ssa.reset(display = False)
				init_time = time.time()
				self.ssa.init(edge = 'negative', display = False)
				#self.test.lateral_input_phase_tuning(shift = 1)

				stavailable = [x for x in stavailable if x not in striplist]
				striplist = random.sample(stavailable, 4)
				striplist = list(np.sort(striplist))
				iteration += 1
				striplist = [15,16,17]
				results = self.seuutil.Run_Test_SEU(
					strip = striplist, hipflags = striplist, delay = 71, run_time = self.run_time,
					cal_pulse_period = 1, l1a_period = 39, latency = latency, display = 0)

				self.seuutil.Stub_ReadFIFOs(
					nevents = 'all',
					filename = "../SSA_Results/SEU/" + folder + '/CL-FIFO/' + filename +'__'+str(runname)+'__'+str(iteration))

				self.seuutil.L1_ReadFIFOs(
					nevents = 'all',
					filename = "../SSA_Results/SEU/" + folder + '/L1-FIFO/' + filename +'__'+str(runname)+'__'+str(iteration))

				conf_p_er, conf_s_er = self.check_configuration(
					filename = "../SSA_Results/SEU/" + folder + '/CONFIG/' + filename +'__'+str(runname)+'__'+str(iteration),
					strip_list = striplist, latency = latency)

				[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er]  = results
				print("->  \tStrip List = " + str(striplist))

				seucounter = self.ssa.ctrl.read_seu_counter()
				seurate = np.float(seucounter)/(time.time() - init_time)
				print("->  \tSEU Counter       ->  Value: " + str(seucounter) + " Rate: " + str(seurate) + " 1/s")

				msg  = runname + ', ' + str(iteration) + ', ' + str(latency) + ', '
				striplist.extend([0]*(8-len(striplist)))
				msg += ', '.join(map(str, striplist )) + ', '
				msg += ', '.join(map(str, results)) + ', '
				msg += str(conf_p_er) + ', ' + str(conf_s_er) + ', ' + str(seucounter) + ', '

				fn = logfile + self.run_info() + '.csv'
				dir = fn[:fn.rindex(os.path.sep)]
				if not os.path.exists(dir): os.makedirs(dir)
				fo = open(fn, 'a')
				fo.write(msg + '\n')
				fo.close()


	def check_configuration(self, filename = 'Try', strip_list = range(1,121), latency = 500):
		#t = time.time()
		conf_new = self.ssa.ctrl.save_configuration(rtarray = True, display=False, strip_list = strip_list, file = (filename+'__configuration.scv'))
		conf_ref = self.ssa.ctrl.load_configuration(rtarray = True, display=False, upload_on_chip = False, file = 'ssa_methods/ssa_base_configuration.csv')
		conf_ref[ np.where(conf_ref[:,1] == 'L1-Latency_LSB')[0][0] , 2] = (latency >> 0) & 0xff
		conf_ref[ np.where(conf_ref[:,1] == 'L1-Latency_MSB')[0][0] , 2] = (latency >> 8) & 0xff
		error = self.ssa.ctrl.compare_configuration(conf_new, conf_ref)
		#print(time.time() - t)
		peri_er = bool(error[0])
		strip_er = not all(v == 0 for v in error[1:])
		if(peri_er):
			print "-X  \tSEU Configuration -> Error in Periphery configuration"
		if(strip_er):
			print "-X  \tSEU Configuration -> Error in Strip configuration"
		return peri_er, strip_er
