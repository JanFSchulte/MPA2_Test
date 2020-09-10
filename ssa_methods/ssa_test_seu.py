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

from collections import OrderedDict
from functools import reduce
from pandas.core.common import flatten as pandas_flatten
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from utilities.tbsettings import *

class SSA_SEU():

	def __init__(self, ssa, seuutil, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.seuutil = seuutil; self.fc7 = fc7; self.cal = cal;
		self.pwr = pwr;   self.test = test; self.biascal = biascal; self.measure = measure;
		self.init_parameters()

	##############################################################
	def init_parameters(self):
		self.summary = results()
		self.runtest = RunTest('default')
		self.l1_latency = [101, 501]
		self.run_time = 5 #sec

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
		logfile = "../SSA_Results/SEU_Results/" + folder + "/" + filename
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

				self.ssa.ctrl.read_seu_counter(display=False, return_rate=True) #only to initialize timer for rate calculation

				#results = self.seuutil.Run_Test_SEU(
				#	check_stub=True, check_l1=True, check_lateral=True,
				#	strip = striplist, hipflags = striplist, delay = 74, run_time = self.run_time,
				#	cal_pulse_period = 1, l1a_period = 39, latency = latency, display = 1, stop_if_fifo_full = 0)

				#[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration]  = results

				seucounter = self.ssa.ctrl.read_seu_counter(display=True)

				self.seuutil.Stub_ReadFIFOs(
					nevents = 'all',
					filename = "../SSA_Results/SEU/" + folder + '/CL-FIFO/' + filename +'__'+str(runname)+'__'+str(iteration))

				self.seuutil.L1_ReadFIFOs(
					nevents = 'all',
					filename = "../SSA_Results/SEU/" + folder + '/L1-FIFO/' + filename +'__'+str(runname)+'__'+str(iteration))

				conf_p_er, conf_s_er = self.check_configuration(
					filename = "../SSA_Results/SEU/" + folder + '/CONFIG/' + filename +'__'+str(runname)+'__'+str(iteration),
					strip_list = striplist, latency = latency)

				print("->  Strip List = " + str(striplist))

				striplist.extend([0]*(8-len(striplist)))
				logdata = list(pandas_flatten([
					runname, str(iteration), str(latency), striplist,
					CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, conf_p_er,  conf_s_er,
					self.ssa.ctrl.seu_cntr['S']['peri'], self.ssa.ctrl.seu_cntr['S']['strip'],
					self.ssa.ctrl.seu_cntr['A']['peri'], self.ssa.ctrl.seu_cntr['A']['strip'],
					test_duration, seucounter['time_since_last_check'],
					]))
				msg = ','.join(map(str, logdata))
				fn = logfile + self.run_info() + '.csv'
				dir = fn[:fn.rindex(os.path.sep)]
				if not os.path.exists(dir): os.makedirs(dir)
				with open(fn, 'a') as fo:
					fo.write(msg + '\n')

	def analyse_stub_error_buffer(self, folder = "../SSA_Results/SEU_Results_anl"):
		labels = []
		datalog = []
		self.dirs = os.listdir(folder)
		self.dirs = [s for s in self.dirs  if "Test_" in s]
		self.dirs.sort()

	##############################################################
	def compile_logs(self, folder = "../SSA_Results/SEU_Results", cl_cut = 100, l1_cut = 100):
		labels = []
		datalog = []
		self.dirs = os.listdir(folder)
		self.dirs = [s for s in self.dirs  if "Test_" in s]
		self.dirs.sort()
		datalog.append( ["LET", "TILT", "LATENCY", "FLUX", "Run Time", "Average SEU Counter in 30sec", "Average Cluster Errors in 30sec", "Average L1 Errors in 30sec", "Average Cluster Errors / (30sec*Flux)", "Average L1 Errors in 30sec / (30sec*Flux)", "Duration Cluster test [s]", "Cluster data errors", "Duration L1 test [s]", "L1 data errors"])
		for dt in self.dirs:
			summary = []
			l1er_lowlatency  = []
			l1er_highlatency = []
			info = CSV.csv_to_array( folder + "/" + dt + "/info.csv" )
			ION  = info[0,1]
			LET  = float(info[3,1])
			FLUX = float(info[4,1])
			TILT = float(info[5,1])
			for f in os.listdir(folder + '/' + dt):
				if(len(re.findall("\W?SEU_SSA(.+).csv", f))>0):
					#print(folder + '/' + dt + '/' + f)
					summary = CSV.csv_to_array( folder + '/' + dt + '/' + f )
			self.summary = summary

			tmp = summary[np.where(summary[:,21] < 100)][:,21]
			seucnt = np.mean(tmp)

			tmp = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]<250) )][:,15]
			cor = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]<250) )][:,24]
			clusterr_l_sum = np.sum(tmp + cor)
			clusterr_l_len = len(tmp + cor)
			clusterr_l = np.float(np.mean(tmp + cor))

			tmp = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]>250) )][:,15]
			cor = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]>250) )][:,24]
			clusterr_h = np.mean(tmp + cor)
			clusterr_h_sum = np.sum(tmp + cor)
			clusterr_h_len = len(tmp + cor)
			clusterr_h = np.float(np.mean(tmp + cor))

			tmp = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]<250)  )][:,17]
			cor = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]<250)  )][:,25]
			l1dataer_l_sum = np.sum(tmp + cor)
			l1dataer_l_len = len(tmp + cor)
			l1dataer_l = np.float(np.mean(tmp + cor))

			tmp = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]>250)  )][:,17]
			cor = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]>250)  )][:,25]
			l1dataer_h_sum = np.sum(tmp + cor)
			l1dataer_h_len = len(tmp + cor)
			l1dataer_h = np.float(np.mean(tmp + cor))

			print( "->  {:2s}   {:%7.3f}   {:7.3f}  {:7.3f}  {:7.3f} ".format(ION, LET,  clusterr_l+clusterr_h, l1dataer_l, l1dataer_h)  )

			datalog.append( [LET, TILT, 100 , FLUX, 30, seucnt, clusterr_l, l1dataer_l, clusterr_l/(float(FLUX)*30), l1dataer_l/(float(FLUX)*30), clusterr_l_len*30,  clusterr_l_sum, l1dataer_l_len*30,  l1dataer_l_sum ])
			#print(datalog[-1])
			datalog.append( [LET, TILT, 500 , FLUX, 30, seucnt, clusterr_h, l1dataer_h, clusterr_h/(float(FLUX)*30), l1dataer_h/(float(FLUX)*30), clusterr_h_len*30,  clusterr_h_sum, l1dataer_h_len*30,  l1dataer_h_sum ])
			#print(datalog[-1])
			#time.sleep(2)
		CSV.array_to_csv( datalog , folder + "/cmplog.csv" )
		print("->  Compiled log saved in: " + str( folder + "/cmplog.csv") )


	##############################################################
	def plot_logs(self, folder = "../SSA_Results/SEU_Results", compile_data = True, cl_cut = 70, l1_cut = 70):
		if(compile_data):
			self.compile_logs(folder = folder, cl_cut = cl_cut, l1_cut = l1_cut)
		datalog = CSV.csv_to_array(folder + "/cmplog.csv" )
		xvalues = np.unique(datalog[1: , 1])
		er_clus_100_t00 = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='100') )][:,[1, 9]] , dtype=float)
		er_clus_500_t00 = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='500') )][:,[1, 9]] , dtype=float)
		er_l100_t00     = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='100') )][:,[1,10]] , dtype=float)
		er_l500_t00     = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='500') )][:,[1,10]] , dtype=float)
		er_clus_100_t30 = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='100') )][:,[1, 9]] , dtype=float)
		er_clus_500_t30 = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='500') )][:,[1, 9]] , dtype=float)
		er_l100_t30     = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='100') )][:,[1,10]] , dtype=float)
		er_l500_t30     = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='500') )][:,[1,10]] , dtype=float)
		l1_data100      = np.array( datalog[ np.where( (datalog[:,3]=='100') )][:,[1,10]] , dtype=float)
		l1_data500      = np.array( datalog[ np.where( (datalog[:,3]=='500') )][:,[1,10]] , dtype=float)
		clust_data100   = np.array( datalog[ np.where( (datalog[:,3]=='100') )][:,[1, 9]] , dtype=float)
		clust_data500   = np.array( datalog[ np.where( (datalog[:,3]=='500') )][:,[1, 9]] , dtype=float)
		clust_data      = np.array( datalog[1: ,[1,9]] , dtype=float)
		er_clus = []; er_l100 = []; er_l500 = [];
		for i in np.unique(clust_data[:,0]):
			tmp = np.array(  clust_data[ np.where((clust_data[:,0] == i)) ] )[:,1]
			tmp = np.mean( np.array(tmp) )
			er_clus.append( [i , tmp] )
			tmp = np.array(  l1_data100[ np.where((l1_data100[:,0] == i)) ] )[:,1]
			tmp = np.mean( np.array(tmp) )
			er_l100.append( [i , tmp] )
			tmp = np.array(  l1_data500[ np.where((l1_data500[:,0] == i)) ] )[:,1]
			tmp = np.mean( np.array(tmp) )
			er_l500.append( [i , tmp] )
		er_clus = np.array(er_clus)
		er_l100 = np.array(er_l100)
		er_l500 = np.array(er_l500)

		#plt.clf()
		fig = plt.figure(figsize=(16,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("Errors per particle", fontsize=32)
		plt.xlabel('LET', fontsize=16)
		color=iter(sns.color_palette('deep'))
		#plt.ylim(bottom = 1E-9)
		c = next(color)
		plt.semilogy(er_clus[:,0], er_clus[:,1], '--o', color = c, markersize = 10, markeredgewidth = 0)
		c = next(color)
		plt.semilogy(er_l100[:,0], er_l100[:,1], '--o', color = c, markersize = 10, markeredgewidth = 0)
		c = next(color)
		plt.semilogy(er_l500[:,0], er_l500[:,1], '--o', color = c, markersize = 10, markeredgewidth = 0)

	##############################################################
	def seucounter_try(self, iterations = 1000):
		curtime = time.time()
		for i in range(iterations):
			cnt = self.ssa.ctrl.read_seu_counter()
			print("->  %10.6f -> %3d" % ( (time.time()-curtime), cnt))

	##############################################################
	def check_configuration(self, filename = '../SSA_Results/SEU/test', strip_list = range(1,121), latency = 500):
		#t = time.time()
		utils.print_info("->  Saving configuration to " + str(filename))
		conf_new = self.ssa.ctrl.save_configuration(
			rtarray = True, display=False, strip_list = 'all',
			file = (filename+'__configuration.scv'))

		utils.print_info("->  Reading default configuration ")
		conf_ref = self.ssa.ctrl.load_configuration(
			rtarray = True, display=False, upload_on_chip = False,
			file = 'ssa_methods/Configuration/ssa_configuration_base_v{:d}.csv'.format(tbconfig.VERSION['SSA']))

		#conf_ref[ np.where(conf_ref[:,1] == 'L1_Latency_lsb')[0][0] , 2] = (latency >> 0) & 0xff
		#conf_ref[ np.where(conf_ref[:,1] == 'L1_Latency_msb')[0][0] , 2] = (latency >> 8) & 0xff
		utils.print_info("->  Comparing configuration")
		error = self.ssa.ctrl.compare_configuration(conf_new, conf_ref)
		#print(time.time() - t)
		peri_er = bool(error[0])
		strip_er = not all(v == 0 for v in error[1:])
		if(peri_er):
			print("-X  \tSEU Configuration -> Error in Periphery configuration")
		if(strip_er):
			print("-X  \tSEU Configuration -> Error in Strip configuration")
		if(not peri_er and not strip_er):
			print("->  SEU Configuration -> Correct")
		return peri_er, strip_er

	def set_info(self):
		self.ion    = input("Ion    : ")
		self.tilt   = input("Angle  : ")
		self.flux   = input("Flux : ")
		self.folder = input("Folder : ")

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
			print(str(seucounter))
			if( (time.time()-tinit) > runtime):
				return

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
					print([ reg,  r])

			#for reg in strip_reg_map:
			#	for strip in range(1,120):
			#		self.I2C.strip_write(reg, strip, 0x1)
			#		r = self.I2C.strip_read(reg,  strip)
			#		registers.append([ reg,  r])
			#		#if(r != 0x1):
			#		print([ reg,  r])
			CSV.ArrayToCSV(registers, file+ str(i))


	def CheckConfiguration(self, folder = "../SSA_Results/SEU_Results/"):
		labels = []; datalog = [];
		dirs = os.listdir(folder)
		dirs = [s for s in dirs  if "Test_" in s]
		dirs.sort()
		conf_correct = CSV.csv_to_array('ssa_methods/Configuration/ssa_configuration_base.csv')
		conf_default = CSV.csv_to_array('ssa_methods/Configuration/ssa_configuration_reset.csv')
		for dt in dirs:
			errors = []
			for f in os.listdir( folder + '/' + dt + "/CONFIG/" ):
				if(len(re.findall("SEU_SSA_(.+)_configuration.scv", f))>0):
					filename = folder + '/' + dt + "/CONFIG/" + f
					tmp = CSV.csv_to_array( filename )
					print("->  Elaborating file: " + filename)
					conf_read = np.zeros([np.shape(tmp)[0], 8], dtype="|S32")
					conf_read[:,0:4] = tmp[:,0:4]
					for reg in conf_read:
						correct_val = conf_correct[map(lambda x : (str(x[1]) == reg[1]) and (str(x[2]) == reg[2]) , conf_correct )][0][3]
						default_val = conf_default[map(lambda x : (str(x[1]) == reg[1]) and (str(x[2]) == reg[2]) , conf_default )][0][3]
						reg[4] = ''
						reg[6] = str(correct_val)
						reg[7] = str(default_val)
						if((reg[3] == str(correct_val)) or ((reg[2] == 'L1_Latency_lsb') and (reg[3] in ['101', '501'])) or ((reg[2] == 'L1_Latency_msb') and (reg[3] in ['0', '1']))):
							reg[5] = ""
						elif(reg[3] == str(default_val)):
							reg[5] = "Reset"
							errors.append(np.array([filename, reg[0], reg[1], reg[2], reg[3], reg[4], reg[5], reg[6], reg[7]]))
						else:
							reg[5] = "Error"
							errors.append(np.array([filename, reg[0], reg[1], reg[2], reg[3], reg[4], reg[5], reg[6], reg[7]]))

					CSV.array_to_csv(conf_read[:,1:], folder + '/' + dt + "/CONFIG/" + f )
			CSV.array_to_csv(errors, folder + '/' + dt + "/CONFIG/Conf_ErLog.csv")



		#fig = plt.figure(figsize=(16,12))
		#color=iter(sns.color_palette('deep'))
		#plt.semilogy(er_clus_100_t00[:,0], er_clus_100_t00[:,1], 'ro')
		#plt.semilogy(er_clus_500_t00[:,0], er_clus_500_t00[:,1], 'ro')
		#plt.semilogy(er_l100_t00[:,0], er_l100_t00[:,1], 'bo')
		#plt.semilogy(er_l500_t00[:,0], er_l500_t00[:,1], 'go')
		#plt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], 'bo')
		#plt.semilogy(er_l500_t30[:,0], er_l500_t30[:,1], 'go')
		#plt.show()
		#plt.figure(7)
		#plt.semilogy(er_l100[:,0], er_l100[:,1], '-ro')
		#plt.semilogy(l1_data100[:,0], l1_data100[:,1], '-go')
		#plt.semilogy(er_l100_t00[:,0], er_l100_t00[:,1], '-bo')
		#plt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], '-bo')
		#plt.show()
		#return er_l100, er_l100_t00, er_l100_t30

		#lt.figure(7)
		#lt.semilogy(er_clus_100_t30[:,0], er_clus_100_t30[:,1], 'ro')
		#lt.semilogy(er_clus_500_t30[:,0], er_clus_500_t30[:,1], 'ro')
		#lt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], 'bo')
		#lt.semilogy(er_l500_t30[:,0], er_l500_t30[:,1], 'go')
		#lt.show()

		#return er_clus[:,1],er_l100[:,1],er_l500[:,1]
		#plt.figure()
		#plt.plot(er_l100_t00[:,0], er_l100_t00[:,1], 'o')
		#plt.plot(er_l500_t00[:,0], er_l500_t00[:,1], 'o')
		#plt.figure()
		#plt.plot(er_l100[:,0], er_l100[:,1], 'o')
		#plt.figure()
		#plt.plot(er_clus_t00[:,0], er_clus_t00[:,1], 'o')
		#plt.figure()
		#plt.plot(er_clus_t30[:,0], er_clus_t30[:,1], 'o')
		#plt.show()
		#eturn datalog




#for reg in ssa.ctrl.ssa_peri_reg_map:
#	I2C.peri_write(reg, 0xff)
#	print("")
#	print(reg)
#	time.sleep(0.2); print(ssa.ctrl.read_seu_counter())
#	time.sleep(0.2); print(ssa.ctrl.read_seu_counter())
#	time.sleep(0.2); print(ssa.ctrl.read_seu_counter())
#	print(pwr.get)


#6 10, 30, 45, 60
