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
import traceback
from scipy import stats

from collections import OrderedDict
from functools import reduce
from pandas.core.common import flatten as pandas_flatten
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate
from scipy.optimize import curve_fit
from scipy.special import erfc
from scipy.special import erf
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import exp, loadtxt, pi, sqrt
from lmfit import Model

from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from utilities.tbsettings import *
from myScripts.ArrayToCSV import *

class SSA_SEU():

	def __init__(self, ssa, seuutil, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.seuutil = seuutil; self.fc7 = fc7; self.cal = cal;
		self.pwr = pwr;   self.test = test; self.biascal = biascal; self.measure = measure;
		self.init_parameters()

	##############################################################
	def main_test(self, niterations=16, run_time=30, memory_select='SRAM', delay_adjust=0, reset_chip=True):
		self.run_time = run_time
		self.set_info()
		self.time   = utils.date_time()
		self.filename = "SEU_SSA_" + self.time + "__Ion-" + self.ion + "__Tilt-" + str(self.tilt) + "__Flux-" + str(self.flux) + "__"
		self.seu_test(
			filename=self.filename, folder=self.folder, niterations=niterations,
			memory_select=memory_select, delay_adjust=delay_adjust, reset_fc7=True, reset_chip=reset_chip, align=True)

	##############################################################
	def seu_test(self, filename = 'Try', folder = '../SSA_Results/SEU_tmp/', niterations=16, memory_select='SRAM', delay_adjust=0, reset_fc7=True, reset_chip=True, align=True):
		print(folder)
		runname = self.run_info()
		logfile = folder + filename + '__full.log'
		errfile = folder + filename + '__errors.log'
		summary = folder + filename + '__summary.csv'
		fc7_al  = folder + filename + '__fc7_phase_status.csv'
		stublog = folder + '/CL-FIFO/'+ filename +'__'+str(runname)+'__'
		l1dtlog = folder + '/L1-FIFO/'+ filename +'__'+str(runname)+'__'
		conflog = folder + '/CONFIG/' + filename +'__'+str(runname)+'__'
		cntlog  = folder + '/SEUCNT/' + filename +'__'+str(runname)+'__'

		utils.set_log_files(logfile, errfile)
		starttime=time.time()
		compare_del = 74+delay_adjust
		for latency in self.l1_latency:
			if(self.terminate): break
			#striplist = []
			#stavailable = range(1,121)
			for iteration in list(range(niterations)):
				if(self.terminate): break
				wd=0
				while (wd < 3):
					try:
						utils.print_info('_____________________________________')
						utils.print_info('Starting iteration {:d}'.format(iteration))
						if(reset_chip):
							self.ssa.reset(display = True)
						else:
							print('->  No reset')
						init_time = time.time();
						start_date_time = utils.date_and_time()
						time.sleep(0.2); #after reset
						self.ssa.ctrl.load_basic_calib_configuration(strips=[], peri=True, display=0)
						self.ssa.ctrl.set_active_memory(memory_select, memory_select)
						#if(align): self.ssa.init(edge = 'negative', display = False)
						#self.test.lateral_input_phase_tuning(shift = 1)
						#stavailable = [x for x in stavailable if x not in striplist]
						#striplist = sorted(random.sample(stavailable, 7))
						#hipflags  = sorted(random.sample(striplist, np.random   ))
						striplist, centroids, hip_hits, hip_flags  = self.test.generate_clusters(
							nclusters=8, min_clsize=1, max_clsize=2, smin=1,
							smax=119, HIP_flags=True)

						self.ssa.ctrl.read_seu_counter(display=False, return_rate=True) #only to initialize timer for rate calculation

						results = self.seuutil.Run_Test_SEU(
							check_stub=True, check_l1=True, check_lateral=False, create_errors = False,
							strip = striplist, centroids=centroids, hipflags = hip_hits, delay = compare_del, run_time = self.run_time,
							cal_pulse_period = 1, l1a_period = 39, latency = latency, display = 1, stop_if_fifo_full = 1, reset_fc7=reset_fc7, align=align)

						[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1, fc7_alignment_status]  = results

						utils.print_info("->  Active strips     -> " + str(striplist))
						utils.print_info("->  HIP strips        -> " + str(hip_hits))
						utils.print_info("->  L1 Latency        -> " + str(latency))

						time_since_reset = time.time()-init_time

						seucounter = self.ssa.ctrl.read_seu_counter(display=True, return_short_array=True, printmode='info', filename=cntlog+str(iteration)+'_'+str(latency))

						self.seuutil.Stub_ReadFIFOs( nevents = 'all', filename = stublog +str(iteration)+'_'+str(latency))

						self.seuutil.L1_ReadFIFOs( nevents = 'all', filename = l1dtlog +str(iteration)+'_'+str(latency))

						conf_p_er, conf_s_er = self.check_configuration(
							filename = (conflog + str(iteration)+'_'+str(latency)),
							active_strip_list = striplist, active_HIP_list = hip_hits,
							latency = latency, memory_select=memory_select)

						self.write_summary(
							summary, results, fc7_al, striplist, hip_hits, time_since_reset, seucounter, iteration,
							latency, runname,  conf_p_er,  conf_s_er, memory_select, start_date_time)

						utils.print_log('->  Total time since the start of testing is {:s}'.format(utils.time_delta(time_init=starttime) ))
						break
					except(KeyboardInterrupt):
						utils.print_warning("\n->  Keyboard Interrupt request. Exiting SEU test procedure.")
						self.terminate = True
						break
					except:
						utils.print_warning("\n\nX>  Exception.. Reiterating..." + str(wd))
						self.exc_info = sys.exc_info()
						utils.print_warning("======================")
						exeptinfo = traceback.format_exception(*self.exc_info )
						for extx in exeptinfo:
							utils.print_warning(extx)
						utils.print_warning("======================")
						self.fc7.reset(); time.sleep(0.1)
						self.fc7.reset(); time.sleep(0.1)
						wd +=1;
		utils.print_good('->  SEE test procedure completed! (total time: {:s})'.format(utils.time_delta(time_init=starttime) ))

	##############################################################
	def evaluate_error_rate(self, directory = '../SSA_Results/SEU_Results/'):
		data_set = {};

		self.compile_logs(
			directory=directory,
			use_run_precise_info = True)

		data_set['stub_data'] = CSV.csv_to_array( directory+'stub.csv')
		data_set['sram_500']  = CSV.csv_to_array( directory+'sram_500.csv')
		data_set['latch_500'] = CSV.csv_to_array( directory+'latch_500.csv')
		# s0_e, s_e, E0_e, W_e
		self.fit_and_evaluate_error_rate(
			name_list    = ['stub_data'],
			dataset_list = [data_set['stub_data']],
			corr_list    = [[1E-3,1E-1,1E-2,1E3]] )

		self.fit_and_evaluate_error_rate(
			name_list = ['sram_500', 'latch_500'],
			dataset_list = [data_set['sram_500'], data_set['latch_500']],
			corr_list = [[1E-4,1E-2,1E-1,100] ,[1E-4,1E-2,1E-1,100]]  )

	##############################################################
	def fit_and_evaluate_error_rate(self, name_list, dataset_list, corr_list=[[0,0,0,0]], sensitive_depth=1E-6, directory = '../SSA_Results/SEU_Results/'):
		si_density   = [2.3290E3, 'mg/cm3']
		sens_volume  = [1*1*sensitive_depth, 'um^3']
		rate_tracker = CSV.csv_to_array( directory+'seu_rate_lhc_tracker.csv')
		total_crossection = {};
		hadron_flux  = CSV.csv_to_array( directory+'fluka_hadrons_gt20MeV_central_region_data.csv', noheader=True)
		fig = plt.figure(figsize=(12,8))
		color=iter(sns.color_palette('deep'))
		dataselect = 0; filename = '';
		for data in dataset_list:
			#data = data_set[name_list]
			LET  = np.array(data[:,3], dtype=np.double)
			Edep = LET * (sensitive_depth  * 1E2 * si_density[0] )
			cross_section = np.array(data[:,6], dtype=np.double)
			c = next(color)
			y = np.array(data[:,6], dtype=np.double)
			param_bounds =([0,0,0,0],[1E-1,1E2,1E2,1E5])
			init_param   = [corr_list[dataselect][0], corr_list[dataselect][1], corr_list[dataselect][2], corr_list[dataselect][3]]
			par, cov = curve_fit(f = f_weibull_cumulative, xdata = Edep, ydata = cross_section,  p0 = init_param, bounds=param_bounds)
			perr = np.sqrt(np.diag(cov))
			s0, s, E0, W = par
			s0_e, s_e, E0_e, W_e = perr
			utils.print_good('\nCumulative weibull fitting parameters: \n            Value   |  Error')
			utils.print_good('    W  = {:10.6e} | {:10.6e}'.format(W, W_e))
			utils.print_good('    s  = {:10.6e} | {:10.6e}'.format(s, s_e))
			utils.print_good('    s0 = {:10.6e} | {:10.6e}'.format(s0, s0_e))
			utils.print_good('    E0 = {:10.6e} | {:10.6e}\n'.format(E0, E0_e))
			plt.semilogy(Edep, cross_section,'o--', color = c)
			xl = np.linspace(-5,Edep[-1], 10000)
			plt.semilogy(xl, f_weibull_cumulative1(xl, s0, s, E0, W) , color = c)
			total_crossection[dataselect] = [0, '[cm^2]']
			for i in range(len(rate_tracker)-1):
				delta = (f_weibull_cumulative1(rate_tracker[i+1,0], s0,s,E0,W) - f_weibull_cumulative1(rate_tracker[i,0], s0,s,E0,W))/s0
				if(delta >0): total_crossection[dataselect][0] += (s0 / 1E-8) * rate_tracker[i,1] * delta
			utils.print_good('\nCross-section for CMS tracker environment: ')
			utils.print_good("    cs = {:10.6e}  | {:10.6e}\n".format(total_crossection[dataselect][0], 0))
			filename += '_{:s}'.format(name_list[dataselect])
			dataselect += 1
		ax = plt.subplot(111)
		leg = ax.legend(fontsize = 16, loc=('lower right'), frameon=True )
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.ylabel("$ \sigma [cm^{2}] $", fontsize=20)
		plt.xlabel("$ E_{DEP} [MeV] $", fontsize=20)
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.savefig(directory+'/see_plot_cross_section_fit_{:s}.png'.format(filename), bbox_inches="tight");
		dataselect = 0
		for data in dataset_list:
			fig = plt.figure(figsize=(12,8))
			color=iter(sns.color_palette('deep'))
			for r in [22, 40, 60]:
				r_index = np.where(hadron_flux[:,0]==r)[0][0]
				z_index = [hadron_flux[0,1:], '[cm]']
				z_flux = [hadron_flux[r_index, 1:], '[cm^{-2} s^{-1}]']
				upset_rate = [z_flux[0]*total_crossection[dataselect][0], '[s^{-1} chip^{-1}]']
				c = next(color)
				plt.plot(z_index[0], upset_rate[0], '.', label='r = {:6.1f}'.format(r))
				ax = plt.subplot(111)
				leg = ax.legend(fontsize=16, loc=('lower right'), frameon=True )
				leg.get_frame().set_linewidth(1.0)
				ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
				plt.ylabel("Upset rate "+upset_rate[1], fontsize=20)
				plt.xlabel("z "+z_index[1], fontsize=20)
				plt.xticks(fontsize=16)
				plt.yticks(fontsize=16)
				errors_expected = upset_rate[0][ np.where(z_index[0]==(r))[0][0] ]
				self.r = r; self.b = z_flux[0]; self.c = errors_expected
				#utils.print_good('Expected errorr at r={:d} z=- flux={:7.3e} -> {:9.6e} errors/(s*chip)'.format(r, z_flux[0], errors_expected))
			self.total_crossection =  total_crossection
			plt.savefig(directory+'/see_plot_error_rate_tracker_{:s}.png'.format(name_list[dataselect]), bbox_inches="tight");

			max_flux_compare_cic = 4.3E7
			upset_rate = [max_flux_compare_cic*total_crossection[dataselect][0], '[s^{-1} chip^{-1}]']
			dataselect += 1
			utils.print_good('Expected errorr at flux = {:7.3e} -> {:9.6e} errors/(s*chip)'.format(max_flux_compare_cic, upset_rate[0]))

	##############################################################
	def compile_logs(self, directory='../SSA_Results/SEU_Results/', use_run_precise_info = True):
		let_map = {'C':1.3, 'Al':5.7, 'Ar':9.9, 'Cr':16.1, 'Ni':20.4, 'Kr':32.4, 'Rh':46.1, 'Xe':62.5}
		fluence_limit_all_ions = 0
		if(use_run_precise_info):
			run_info = CSV.csv_to_array(directory+'see_test_ions_flux.csv')
			ion_info = [[],[]]
			for info in run_info:
				ion_info[0].append( (re.split('-', info[10])[0]).strip() ) # run ion
				ion_info[1].append( info[5] ) # run number
			ion_info = np.array(ion_info)
		dirs = os.listdir(directory)
		dirs = [s for s in dirs if "Ion-" in s]
		dirs.sort()
		global_summary = {'latch_500':[], 'latch_100':[], 'sram_500':[], 'sram_100':[], 'stub':[],'sram_stub':[],'latch_stub':[] }
		for ddd in dirs:
			for f in os.listdir( directory +'/'+ ddd ):
				run_summary = re.findall("SEU_SSA.+_summary.csv", f)
				if(len(run_summary)>0):
					run_summary = directory +'/'+ ddd +'/'+ run_summary[0]
					rfn = re.findall("SEU_SSA.+Ion-(.+)__Tilt-(.+)__Flux-(.+)_run(.+)____summary.csv", f)
					if(len(rfn)>0):
						print("->  Elaborating file: " + str(run_summary))
						[ion, angle, memory, run] = rfn[0]
						run_data = CSV.csv_to_array(  run_summary )
						if(use_run_precise_info):
							index = np.where( (ion_info[0, :] == ion) & (ion_info[1, :] == run) )
							if(len(index[0])>1):
								print('    Found repeated test: ion={:s}, run={:s}, index={:s}'.format(ion, run, str(index)))
							dose = run_info[index][0][9]
							LET = run_info[index][0][11]
							mean_flux = run_info[index][0][8]
							run_time = np.sum( run_data[:, 5] )
							fluence = mean_flux * run_time
						else:
							dose = 0
							LET = let_map[ ion ] / np.cos(np.radians(float(angle)) )
							mean_flux = 15000 * np.cos(np.radians(float(angle)) )
							run_time = np.sum( run_data[:, 5] )
							fluence = mean_flux * run_time
						fluence_limit_all_ions += fluence
						error_l1_sum = [0]*2; good_l1_sum = [0]*2; time_l1_sum = [0]*2 ; error_rate_l1_sum = [0]*2;
						error_rate_l1_sum_normalised = [0]*2; error_rate_stub_sum_normalised = 0;
						error_stub_sum = 0; good_stub_sum = 0; error_rate_stub_sum = 0; counters_a = 0; counters_s = 0;
						for shortrun in run_data:
							shortrun_duration = shortrun[5]
							if(shortrun_duration>1): #exclude early stopped runs
								error_stub_sum += shortrun[12]
								good_stub_sum += shortrun[8]
								if(shortrun[6]>250): #high latency run
									error_l1_sum[1] += shortrun[14]
									good_l1_sum[1] += shortrun[10]
								else:
									error_l1_sum[0] += shortrun[14]
									good_l1_sum[0] += shortrun[10]
							#else:
							#	print('Excluded: ' + str(shortrun_duration) + str(shortrun))
						error_rate_l1_sum[0] = error_l1_sum[0] / fluence
						error_rate_l1_sum[1] = error_l1_sum[1] / fluence
						error_rate_stub_sum  = error_stub_sum  / fluence
						try: error_rate_l1_sum_normalised[1] = (error_l1_sum[1]/(error_l1_sum[1]+good_l1_sum[1]))/ mean_flux
						except ZeroDivisionError: error_rate_l1_sum_normalised[1] = -1
						try: error_rate_l1_sum_normalised[0] = (error_l1_sum[0]/(error_l1_sum[0]+good_l1_sum[0]))/ mean_flux
						except ZeroDivisionError: error_rate_l1_sum_normalised[0] = -1
						try: error_rate_stub_sum_normalised  = (error_stub_sum/(error_stub_sum+good_stub_sum))/ mean_flux
						except ZeroDivisionError: error_rate_stub_sum_normalised = -1
						#print(mean_flux)
						if(memory=='latch' ):
							global_summary['latch_500'].append([ion, angle, LET, good_l1_sum[1], error_l1_sum[1], error_rate_l1_sum[1], error_rate_l1_sum_normalised[1], run_time, mean_flux, fluence])
							global_summary['latch_100'].append([ion, angle, LET, good_l1_sum[0], error_l1_sum[0], error_rate_l1_sum[0], error_rate_l1_sum_normalised[0], run_time, mean_flux, fluence ])
							global_summary['latch_stub'].append([ion, angle, LET, good_stub_sum, error_stub_sum, error_rate_stub_sum, error_rate_stub_sum_normalised, run_time, mean_flux, fluence])
						elif(memory=='sram'):
							global_summary['sram_500'].append( [ion, angle, LET, good_l1_sum[1], error_l1_sum[1], error_rate_l1_sum[1], error_rate_l1_sum_normalised[1], run_time, mean_flux, fluence ])
							global_summary['sram_100'].append( [ion, angle, LET, good_l1_sum[0], error_l1_sum[0], error_rate_l1_sum[0], error_rate_l1_sum_normalised[0], run_time, mean_flux, fluence ])
							global_summary['sram_stub'].append([ion, angle, LET, good_stub_sum, error_stub_sum, error_rate_stub_sum, error_rate_stub_sum_normalised, run_time, mean_flux, fluence] )
		#return global_summary
		global_summary['latch_500'] = np.array(global_summary['latch_500'])
		global_summary['latch_500'] = global_summary['latch_500'][np.argsort(np.array(global_summary['latch_500'][:,2],dtype=float ))]
		global_summary['latch_100'] = np.array(global_summary['latch_100'])
		global_summary['latch_100'] = global_summary['latch_100'][np.argsort(np.array(global_summary['latch_100'][:,2],dtype=float ))]
		global_summary['sram_500'] = np.array(global_summary['sram_500'])
		global_summary['sram_500'] = global_summary['sram_500'][np.argsort(np.array(global_summary['sram_500'][:,2],dtype=float ))]
		global_summary['sram_100'] = np.array(global_summary['sram_100'])
		global_summary['sram_100'] = global_summary['sram_100'][np.argsort(np.array(global_summary['sram_100'][:,2],dtype=float ))]
		CSV.array_to_csv( np.array(global_summary['latch_500']), directory+'latch_500.csv')
		CSV.array_to_csv( np.array(global_summary['latch_100']), directory+'latch_100.csv')
		CSV.array_to_csv( np.array(global_summary['sram_500']), directory+'sram_500.csv')
		CSV.array_to_csv( np.array(global_summary['sram_100']), directory+'sram_100.csv')
		tmpvect = {}
		global_summary['stub'] = global_summary['latch_stub'].copy()
		for idx in range(len(global_summary['stub'])):
			if(global_summary['latch_stub'][idx][0:2] == global_summary['sram_stub'][idx][0:2]):
				global_summary['stub'][idx][3] = global_summary['sram_stub'][idx][3] + global_summary['latch_stub'][idx][3] #good_stub_sum
				global_summary['stub'][idx][4] = global_summary['sram_stub'][idx][4] + global_summary['latch_stub'][idx][4] #error_stub_sum
				global_summary['stub'][idx][5] = (global_summary['sram_stub'][idx][5] + global_summary['latch_stub'][idx][5])/2.0 #error_rate_stub_sum
				global_summary['stub'][idx][6] = (global_summary['sram_stub'][idx][6] + global_summary['latch_stub'][idx][6])/2.0	#error_rate_stub_sum_normalised
				global_summary['stub'][idx][7] = global_summary['sram_stub'][idx][7] + global_summary['latch_stub'][idx][7] #error_stub_sum
				global_summary['stub'][idx][8] = (global_summary['sram_stub'][idx][8] + global_summary['latch_stub'][idx][8])/2.0	#error_rate_stub_sum_normalised
				global_summary['stub'][idx][9] = global_summary['sram_stub'][idx][9] + global_summary['latch_stub'][idx][9] #error_stub_sum
			else:
				print('ERROR')
		for stubdata in global_summary['stub']:
			if(stubdata[2] in tmpvect):
				tmpvect[stubdata[2]][3] += stubdata[3]
				tmpvect[stubdata[2]][4] += stubdata[4]
				tmpvect[stubdata[2]][5] += stubdata[5]
			else:
				tmpvect[stubdata[2]] = stubdata
		global_summary['stub'] = []
		for i in tmpvect:
			global_summary['stub'].append(tmpvect[i])
		global_summary['stub'] = np.array(global_summary['stub'])
		global_summary['stub'] = global_summary['stub'][np.argsort(np.array(global_summary['stub'][:,2],dtype=float ))]
		CSV.array_to_csv( np.array(global_summary['stub']), directory+'stub.csv')
		utils.print_good('Fluence limit for all ions -> {:9.6f}E+6'.format(fluence_limit_all_ions*1E-6))
		#return global_summary

	##############################################################
	def quick_plot_logs(self, directory='../SSA_Results/SEU_Results/', cross_section_or_error_rate=0):
		stubs = CSV.csv_to_array( directory+'stub.csv')
		sram_500 = CSV.csv_to_array( directory+'sram_500.csv')
		latch_500 = CSV.csv_to_array( directory+'latch_500.csv')
		if(cross_section_or_error_rate): selindex = 6
		else: selindex = 7
		fig = plt.figure(figsize=(16,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(True)
		ax.spines["right"].set_visible(True)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Errors per ..", fontsize=16)
		plt.xlabel('LET', fontsize=16)
		color=iter(sns.color_palette('deep'))
		#plt.ylim(bottom = 1E-9)
		c = next(color)
		plt.semilogy(
			np.array(stubs[:,3], dtype=float), np.array(stubs[:,selindex], dtype=float),
			'--o', color = c, markersize = 10, markeredgewidth = 0, label='Stub data')
		c = next(color)
		plt.semilogy(
			np.array(sram_500[:,3], dtype=float), np.array(sram_500[:,selindex], dtype=float),
			'--o', color = c, markersize = 10, markeredgewidth = 0, label='L1 SRAM')
		c = next(color)
		plt.semilogy(
			np.array(latch_500[:,3], dtype=float), np.array(latch_500[:,selindex], dtype=float),
			'--o', color = c, markersize = 10, markeredgewidth = 0, label='L1 latch')
		leg = plt.legend(fontsize = 12, loc=('lower right'), frameon=True )
		x = np.array(stubs[:,3], dtype=float)
		y = np.array(stubs[:,selindex], dtype=float),
		return [x, y]

	##############################################################
	def seucounter_try(self, iterations = 1000):
		curtime = time.time()
		for i in range(iterations):
			cnt = self.ssa.ctrl.read_seu_counter()
			print("->  %10.6f -> %3d" % ( (time.time()-curtime), cnt))

	##############################################################
	def check_configuration(self, filename = '../SSA_Results/SEU/test', active_strip_list = [], active_HIP_list = [], latency = 500, memory_select='SRAM'):
		#t = time.time()
		utils.print_info("->  Saving configuration to " + str(filename))

		conf_new = self.ssa.ctrl.save_configuration(
			rtarray = True, display=False, strip_list = 'all',
			file = (filename+'__configuration.scv'),
			notes = [['note','active_strip_and_HIPs','[{:s}] - [{:s}]'.format(
				', '.join(map(str, active_strip_list)), ', '.join(map(str, active_HIP_list))   ) ]] )

		utils.print_info("->  Reading default configuration ")
		conf_ref = self.ssa.ctrl.load_configuration(
			rtarray = True, display=False, upload_on_chip = False,
			file = 'ssa_methods/Configuration/ssa_configuration_base_calib_v{:d}.csv'.format(tbconfig.VERSION['SSA']))
		ctrl_3_val = latency & 0x00ff
		if(memory_select == 'LATCH'):
			ctrl_1_val = ((latency&0x0100)>>4)|0b01100100
		else:
			ctrl_1_val = ((latency&0x0100)>>4)|0b00000100
		conf_ref = self.ssa.ctrl._change_config_value(field='StripControl1',     new_value=0b00001001,  conf=conf_ref, strips=active_strip_list )
		conf_ref = self.ssa.ctrl._change_config_value(field='DigCalibPattern_L', new_value=0b00000001,  conf=conf_ref, strips=active_strip_list )
		conf_ref = self.ssa.ctrl._change_config_value(field='DigCalibPattern_H', new_value=0b00000001,  conf=conf_ref, strips=active_HIP_list )
		conf_ref = self.ssa.ctrl._change_config_value(field='control_1',         new_value=ctrl_1_val,  conf=conf_ref, strips=[-1] )
		conf_ref = self.ssa.ctrl._change_config_value(field='control_3',         new_value=ctrl_3_val,  conf=conf_ref, strips=[-1] )

		utils.print_info("->  Comparing configuration")
		error = self.ssa.ctrl.compare_configuration(conf_new, conf_ref)
		#print(time.time() - t)
		peri_er = bool(error[0])
		strip_er = not all(v == 0 for v in error[1:])
		if(peri_er):
			utils.print_error("->  SEU Configuration -> Error in Periphery configuration")
		if(strip_er):
			utils.print_error("->  SEU Configuration -> Error in Strip configuration")
		if(not peri_er and not strip_er):
			utils.print_good("->  SEU Configuration -> Correct")
		return peri_er, strip_er

	##############################################################
	def set_info(self):
		self.ion    = input("Ion    : ")
		self.tilt   = input("Angle  : ")
		self.flux   = input("Flux : ")
		self.folder = "../SSA_Results/SEU_Results/" + "Ion-" + self.ion + "__Tilt-" + str(self.tilt) + "__Flux-" + str(self.flux) + '/'
		if not os.path.exists(self.folder):
			os.makedirs(self.folder)

	##############################################################
	def write_summary(self, summary, results, fc7_al, striplist, hip_hits, time_since_reset, seucounter, iteration, latency, runname, conf_p_er,  conf_s_er, memory, start_time):
		striplist.extend([0]*(8-len(striplist)))
		hip_hits.extend([0]*(8-len(hip_hits)))
		utils.print_log('->  Writing summary')
		[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1, fc7_alignment_status]  = results
		logdata = list(pandas_flatten([
			runname, iteration, start_time,  time_since_reset, test_duration, latency, memory,
			CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, conf_p_er,  conf_s_er, fifo_full_stub, fifo_full_L1,
			seucounter, list(striplist), list(hip_hits),
			]))
		header = [
			'runname'   , 'iteration' , 'date',     'start_time'  , 'time_reset', 'time_test' , 'latency'  , 'memory',
			'CL_ok'     , 'LA_ok'     , 'L1_ok'     , 'LH_ok'     , 'CL_er'     , 'LA_er'     , 'L1_er'    , 'LH_er', 'conf_p_er',  'conf_s_er',
			'FIFO_Stub' , 'FIFO_L1'   , 'seucnt_A_P', 'seucnt_A_S', 'seucnt_S_P', 'seucnt_S_S', 'seucnt_T' ,
			'strip_0'   , 'strip_1'   , 'strip_2'   , 'strip_3'   , 'strip_4'   , 'strip_5'   , 'strip_6'  , 'strip_7',
			'hip_0'     , 'hip_1'     , 'hip_2'     , 'hip_3'     , 'hip_4'     , 'hip_5'     , 'hip_6'    , 'hip_7'  ]
		msg = ''
		if(not os.path.exists(summary)):
			for data in header:
				msg += self.__write_fixed_width(data)
			msg += '\n'
		for data in logdata:
			msg += self.__write_fixed_width(data)
		with open(summary, 'a') as fo:
			fo.write(msg + '\n')
		with open(fc7_al, 'a') as fo:
			fc7_alignment = np.concatenate( [[runname, iteration, start_time[0], start_time[1]], fc7_alignment_status[:,1], fc7_alignment_status[:,2], fc7_alignment_status[:,3], fc7_alignment_status[:,4], fc7_alignment_status[:,5]] )
			for st in fc7_alignment:
				fo.write('{:8s}, '.format(str(st)))
			fo.write('\n')

	##############################################################
	def __write_fixed_width(self, data):
		if  (type(data)==int):    msg = '{:10d}, '.format(data)
		elif(type(data)==str):    msg = '{:10s}, '.format(data)
		elif(type(data)==float):  msg = '{:10.3f}, '.format(data)
		elif(type(data)==bool):   msg = '{:10s}, '.format(str(data))
		else:                     msg = str(data)
		return msg

	##############################################################
	def init_parameters(self):
		self.summary = results()
		self.runtest = RunTest('default')
		self.l1_latency = [501, 101]
		self.run_time = 5 #sec
		self.terminate = False



















	##############################################################
	##### OLD METHODS ############################################
	##############################################################

	def analyse_stub_error_buffer_OLD(self, folder = "../SSA_Results/SEU_Results_anl"):
		labels = []
		datalog = []
		self.dirs = os.listdir(folder)
		self.dirs = [s for s in self.dirs  if "Test_" in s]
		self.dirs.sort()


	##############################################################
	def run_seu_counter_OLD(self, folder, filename, runtime = 60):
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

	##############################################################
	def plot_logs_OLD(self, folder = "../SSA_Results/SEU_Results", compile_data = True, cl_cut = 70, l1_cut = 70):
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
	def CheckConfiguration_OLD(self, folder = "../SSA_Results/SEU_Results/"):
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

	##############################################################
	def I2C_test(self, file='../SSA_Results/I2C/I2C_fast_test', niterations=1000, display=1):
		for iter in range(niterations):
			registers = []; rm = []

			peri_reg_map  = self.ssa.ctrl.ssa_peri_reg_map.copy()
			for i in peri_reg_map:
				if('Fuse' in i): rm.append(i)
				if('SEU' in i): rm.append(i)
				if('mask' in i): rm.append(i)
			for k in rm:
				peri_reg_map.pop(k, None)

			strip_reg_map = self.ssa.ctrl.ssa_strip_reg_map.copy()
			for i in strip_reg_map:
				if('ReadCounter' in i): rm.append(i)
				if('Fuse' in i): rm.append(i)
				if('mask' in i): rm.append(i)
				if('SEU' in i): rm.append(i)
			for k in rm:
				strip_reg_map.pop(k, None)

			for reg in peri_reg_map:
				if(peri_reg_map[reg]['permissions']=='RW'):
					time.sleep(0.001)
					self.I2C.peri_write(register=reg, field=False, data=0x1)
					time.sleep(0.001)
					r = self.I2C.peri_read(register=reg)
					time.sleep(0.001)
					registers.append([ reg,  r])
					if(r != 0x1):
						if(display>0): utils.print_error([ reg,  r])
					else:
						if(display>1): utils.print_good([ reg,  r])

			for reg in strip_reg_map:
				for strip in range(1,120):
					if(strip_reg_map[reg]['permissions']=='RW'):
						time.sleep(0.001)
						self.I2C.strip_write( register=reg, field=False, strip=strip, data=0x1)
						time.sleep(0.001)
						r = self.I2C.strip_read(register=reg,  strip=strip)
						time.sleep(0.001)
						registers.append([ reg,  r])
						if(r != 0x1):
							if(display>0): utils.print_error([ reg,  r])
						else:
							if(display>1): utils.print_good([ reg,  r])
			CSV.ArrayToCSV(registers, file+ str(iter))

	##############################################################
	def compile_logs_old(self, folder = "../SSA_Results/SEU_Results", cl_cut = 100, l1_cut = 100):
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


		#fig = plt.figure(figsize=(16,12))
		#color=iter(sns.color_palette('deep'))
		#plt.semilogy(er_clus_100_t00[:,0], er_clus_100_t00[:,1], 'ro')
		#plt.semilogy(er_clus_500_t00[:,0], er_clus_500_t00[:,1], 'ro')
		#plt.semilogy(er_l100_t00[:,0], er_l100_t00[:,1], 'bo')
		#plt.semilogy(er_l500_t00[:,0], er_l500_t00[:,1], 'go')
		#plt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], 'bo')
		#plt.semilogy(er_
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











'''
	def fit_and_evaluate_error_rate_2(self, name_list, dataset_list, corr_list=[[0,0,0,0]], sensitive_depth=1E-6, directory = '../SSA_Results/SEU_Results/'):
		si_density   = [2.3290E3, 'mg/cm3']
		sens_volume  = [1*1*sensitive_depth, 'um^3']
		rate_tracker = CSV.csv_to_array( directory+'seu_rate_lhc_tracker.csv')
		total_crossection = {};
		hadron_flux  = CSV.csv_to_array( directory+'fluka_hadrons_gt20MeV_central_region_data.csv', noheader=True)
		fig = plt.figure(figsize=(6,4))
		color=iter(sns.color_palette('deep'))
		dataselect = 0; filename = '';
		for data in dataset_list:
			#data = data_set[name_list]
			LET  = np.array(data[:,3], dtype=np.double)
			#Edep = LET * (sensitive_depth  * 1E2 * si_density[0] )
			cross_section = np.array(data[:,6], dtype=np.double)
			c = next(color)
			y = np.array(data[:,6], dtype=np.double)
			param_bounds =([0,0,0,0],[5E-2,5E0,1E1,1E3])
			init_param   = [corr_list[dataselect][0], corr_list[dataselect][1], corr_list[dataselect][2], corr_list[dataselect][3]]
			par, cov = curve_fit(f = f_weibull_cumulative, xdata = LET, ydata = cross_section,  p0 = init_param, bounds=param_bounds)
			perr = np.sqrt(np.diag(cov))
			s0, s, E0, W = par
			s0_e, s_e, E0_e, W_e = perr
			utils.print_good('\nCumulative weibull fitting parameters: \n            Value   |  Error')
			utils.print_good('    W  = {:10.6e} | {:10.6e}'.format(W, W_e))
			utils.print_good('    s  = {:10.6e} | {:10.6e}'.format(s, s_e))
			utils.print_good('    s0 = {:10.6e} | {:10.6e}'.format(s0, s0_e))
			utils.print_good('    E0 = {:10.6e} | {:10.6e}\n'.format(E0, E0_e))
			plt.semilogy(LET, cross_section,'o--', color = c)
			xl = np.linspace(-5,LET[-1], 10000)
			plt.semilogy(xl, f_weibull_cumulative1(xl, s0, s, E0, W) , color = c)
			total_crossection[dataselect] = [0, '[cm^2]']

			for i in range(len(rate_tracker)-1):
				E_i0 = rate_tracker[i,0]
				E_i1 = rate_tracker[i+1,0]
				LET_i0 = E_i0 / (sensitive_depth  * 1E2 * si_density[0] )
				LET_i1 = E_i1 / (sensitive_depth  * 1E2 * si_density[0] )
				delta = (f_weibull_cumulative1(LET_i1, s0,s,E0,W) - f_weibull_cumulative1(LET_i0, s0,s,E0,W))/s0
				if(delta >0): #below E0 the value is not defined
					total_crossection[dataselect][0] += (s0 * 1E8) * rate_tracker[i+1,1] * delta
				print(LET_i1)
				print(LET_i0)
				print('=====')
			utils.print_good('\nCross-section for CMS tracker environment: ')
			utils.print_good("    cs = {:10.6e}  | {:10.6e}\n".format(total_crossection[dataselect][0], 0))
			print(total_crossection)
			filename += '_{:s}'.format(name_list[dataselect])
			dataselect += 1
		plt.savefig(directory+'/plot_cross_section_fit_{:s}.png'.format(filename), bbox_inches="tight");
		dataselect = 0
		for data in dataset_list:
			fig = plt.figure(figsize=(6,4))
			color=iter(sns.color_palette('deep'))
			for r in [21, 40, 60]:
				r_index = np.where(hadron_flux[:,0]==r)[0][0]
				z_index = [hadron_flux[0,1:], '[cm]']
				z_flux = [hadron_flux[r_index, 1:], '[cm^{-2} s^{-1}]']
				upset_rate = [z_flux[0]*total_crossection[dataselect][0], '[s^{-1} chip^{-1}]']
				c = next(color)
				plt.plot(z_index[0], upset_rate[0], '.', label='r = {:6.1f}'.format(r))
				ax = plt.subplot(111)
				leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
				leg.get_frame().set_linewidth(1.0)
				ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
				plt.ylabel("Upset rate "+upset_rate[1], fontsize=16)
				plt.xlabel("z "+z_index[1], fontsize=16)
				plt.xticks(fontsize=12)
				plt.yticks(fontsize=12)
			plt.savefig(directory+'/plot_error_rate_tracker_{:s}.png'.format(name_list[dataselect]), bbox_inches="tight");
			dataselect += 1


def evaluate_error_rate_cic(s0, s, E0, W, sensitive_depth=1E-6, directory = '../SSA_Results/SEU_Results/'):
	si_density   = [2.3290, 'g/cm3']
	sens_depth   = [sensitive_depth*10E2, 'cm']
	sens_volume  = [1*1*sensitive_depth, 'um^3']
	rate_tracker = CSV.csv_to_array( directory+'seu_rate_lhc_tracker.csv')
	total_crossection = {};
	hadron_flux  = CSV.csv_to_array( directory+'fluka_hadrons_gt20MeV_central_region_data.csv', noheader=True)
	fig = plt.figure(figsize=(6,4))
	color=iter(sns.color_palette('deep'))
	dataselect = 0; filename = '';
	c = next(color)
	utils.print_good('\nCumulative weibull fitting parameters: \n            Value   |  Error')
	utils.print_good('    W  = {:10.6e}'.format(W))
	utils.print_good('    s  = {:10.6e}'.format(s))
	utils.print_good('    s0 = {:10.6e}'.format(s0))
	utils.print_good('    E0 = {:10.6e}\n'.format(E0))
	xl = np.linspace(-5, 0.4, 10000)
	plt.semilogy(xl, f_weibull_cumulative1(xl, s0, s, E0, W) , color = c)
	total_crossection[dataselect] = [0, '[cm^2]']
	for i in range(len(rate_tracker)-1):
		delta = (f_weibull_cumulative1(rate_tracker[i+1,0], s0,s,E0,W) - f_weibull_cumulative1(rate_tracker[i,0], s0,s,E0,W))
		if(delta >0):
			total_crossection[dataselect][0] += (s0 / 1E-8) * rate_tracker[i,1] * delta
	utils.print_good('\nCross-section for CMS tracker environment: ')
	utils.print_good("    cs = {:10.6e}  | {:10.6e}\n".format(total_crossection[dataselect][0], 0))
	print(total_crossection)
	dataselect += 1
	dataselect = 0
	fig = plt.figure(figsize=(6,4))
	color=iter(sns.color_palette('deep'))
	for r in [21, 40, 60]:
		r_index = np.where(hadron_flux[:,0]==r)[0][0]
		z_index = [hadron_flux[0,1:], '[cm]']
		z_flux = [hadron_flux[r_index, 1:], '[cm^{-2} s^{-1}]']
		upset_rate = [z_flux[0]*total_crossection[dataselect][0], '[s^{-1} chip^{-1}]']
		c = next(color)
		plt.plot(z_index[0], upset_rate[0], '.', label='r = {:6.1f}'.format(r))
		ax = plt.subplot(111)
		leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.ylabel("Upset rate "+upset_rate[1], fontsize=16)
		plt.xlabel("z "+z_index[1], fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
	dataselect += 1

'''

# evaluate_error_rate_cic(2.079979e-02, 9.520022e-01, 6.366344e-04, 1.362656e+02)



	# 1E-2, 1, 0, 100


		#plt.show()



# fit(['stub_data'], [0,0,0,0])
# fit(['sram_500'], [0,0,0,0])
#
# correction = {'stub_data':[0,0,0,0],'sram_500':[-5E-3,-0.25,0,0], 'latch_500':[0,0,0,0]}
# fit(['stub_data', 'sram_500'], correction)
