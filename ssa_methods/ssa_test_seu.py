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
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
import fnmatch
import re
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns


class SSA_SEU():

	def __init__(self, ssa, seuutil, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.seuutil = seuutil; self.fc7 = fc7; self.cal = cal;
		self.pwr = pwr;   self.test = test; self.biascal = biascal; self.measure = measure;
		self.init_parameters()

	##############################################################
	def main_test(self, run_repeat = 1, run_time = 30):
		self.run_time = run_time
		self.set_info()
		for i in range(run_repeat):
			self.time   = utils.date_time()
			self.filename = "SEU_SSA_" + self.time + "__Ion-" + self.ion + "__Tilt-" + str(self.tilt) + "__Flux-" + str(self.flux) + "__"
			self.seu_test( self.filename, self.folder)

	##############################################################
	def seu_test(self, filename = 'Try', folder = 'PROVA0'):
		runname = self.run_info()
		logfile = "../SSA_Results/SEU/" + folder + "/" + filename
		iteration = 0
		for latency in self.l1_latency:
			striplist = []
			stavailable = range(1,121)
			for rp in range(8):
				self.ssa.reset(display = False)
				init_time = time.time()
				#self.ssa.init(edge = 'negative', display = False)
				#self.test.lateral_input_phase_tuning(shift = 1)
				stavailable = [x for x in stavailable if x not in striplist]
				striplist = random.sample(stavailable, 6)
				striplist = list(np.sort(striplist))
				iteration += 1

				results = self.seuutil.Run_Test_SEU(
					strip = striplist, hipflags = striplist, delay = 73, run_time = self.run_time,
					cal_pulse_period = 1, l1a_period = 39, latency = latency, display = 0)

				seucounter = self.ssa.ctrl.read_seu_counter()

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


	##############################################################
	def plot_logs(self, folder = "../SSA_Results/SEU2"):
		clusterr_mean_00=[]; l1dataer_mean_00=[]; l1header_mean_00=[];
		clusterr_mean_30=[]; l1dataer_mean_30=[]; l1header_mean_30=[];
		seucount_mean_00=[]; seucount_mean_30=[]; LET00=[];  LET30=[];
		dirs = os.listdir(folder)
		dirs.sort()

		for dt in dirs:

			info = CSV.csv_to_array( folder + "/" + dt + "/info.csv" )
			ION  = info[0,1]; LET  = info[3,1];
			FLUX = info[4,1]; TILT = info[5,1];
			summary = []
			for f in os.listdir(folder + '/' + dt):
				if(len(re.findall("\W?SEU_SSA(.+).csv", f))>0):
					#print folder + '/' + dt + '/' + f
					summary = CSV.csv_to_array( folder + '/' + dt + '/' + f )
			seucounter = np.mean(np.where(summary[:,21] < 500))
			clusterr = []
			l1dataer = []
			l1header = []
			for i in summary:
				if('False' in i[19] and 'False' in i[20]):
					clusterr.append(i[15])
					l1dataer.append(i[17])
					l1header.append(i[18])
			if(int(TILT) == 0):
				LET00.append(float(LET))
				seucount_mean_00.append( np.sum(seucounter) )
				clusterr_mean_00.append( np.sum(clusterr) )
				l1dataer_mean_00.append( np.sum(l1dataer) )
				l1header_mean_00.append( np.sum(l1header) )
			else:
				LET30.append(float(LET))
				seucount_mean_30.append( np.sum(seucounter) )
				clusterr_mean_30.append( np.sum(clusterr) )
				l1dataer_mean_30.append( np.sum(l1dataer) )
				l1header_mean_30.append( np.sum(l1header) )
			if(int(TILT) == 0):
				print( "Ion %10s %3s -> %7.3f  %7.3f  %7.3f" % (ION, TILT, np.mean(seucounter), np.mean(clusterr), np.mean(l1dataer)))
		plt.clf()
		return l1dataer_mean_00, l1dataer_mean_30
		LET = range(len(clusterr_mean_00))
		#plt.plot(LET00, clusterr_mean_00)
		plt.plot(LET00, l1dataer_mean_00)
		plt.plot(LET00, seucount_mean_00)
		plt.show()








	##############################################################
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
		if(not peri_er and not strip_er):
			print "->  \tSEU Configuration -> Correct"
		return peri_er, strip_er


	##############################################################
	def run_seu_counter(self, folder, filename, runtime = 60):
		logfile = "../SSA_Results/SEU/" + folder + "/" + filename + "_seucounter.csv"
		tinit = time.time()
		while True:
			seucounter = self.ssa.ctrl.read_seu_counter()
			fo = open(logfile, 'a')
			fo.write(str(time.time()-tinit) + ", " + str(seucounter) + '\n')
			fo.close()
			time.sleep(0.2)
			print str(seucounter)
			if( (time.time()-tinit) > runtime):
				return

	##############################################################
	def init_parameters(self):
		self.summary = results()
		self.runtest = RunTest('default')
		self.l1_latency = [101, 501]
		self.run_time = 0.5 #sec

	def set_info(self):
		self.ion    = raw_input("Ion    : ")
		self.tilt   = raw_input("Angle  : ")
		self.flux   = raw_input("Flux : ")
		self.folder = raw_input("Folder : ")

	def run_info(self):
		return ''

	def I2C_test(self, file):
		for i in range(10000):
			registers = []; rm = []
			peri_reg_map  = self.ssa.ctrl.ssa_peri_reg_map.copy()

			for i in peri_reg_map:
				if('Fuse' in i): rm.append(i)
				if('SEU' in i): rm.append(i)
			for k in rm:
				peri_reg_map.pop(k, None)
			strip_reg_map = self.ssa.ctrl.ssa_strip_reg_map.copy()
			for i in strip_reg_map:
				if('ReadCounter' in i): rm.append(i)
			for k in rm:
				strip_reg_map.pop(k, None)

			for reg in peri_reg_map:
				self.I2C.peri_write(reg, 0x1)
				r = self.I2C.peri_read(reg)
				registers.append([ reg,  r])
				if(r != 0x1):
					print [ reg,  r]

			#for reg in strip_reg_map:
			#	for strip in range(1,120):
			#		self.I2C.strip_write(reg, strip, 0x1)
			#		r = self.I2C.strip_read(reg,  strip)
			#		registers.append([ reg,  r])
			#		#if(r != 0x1):
			#		print [ reg,  r]
			CSV.ArrayToCSV(registers, file+ str(i))






#for reg in ssa.ctrl.ssa_peri_reg_map:
#	I2C.peri_write(reg, 0xff)
#	print ""
#	print reg
#	time.sleep(0.2); print ssa.ctrl.read_seu_counter()
#	time.sleep(0.2); print ssa.ctrl.read_seu_counter()
#	time.sleep(0.2); print ssa.ctrl.read_seu_counter()
#	print pwr.get


#6 10, 30, 45, 60
