from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from collections import OrderedDict
from scipy import interpolate as scipy_interpolate
from scipy import constants as ph_const
from scipy import stats as scipy_stats
import time, sys, inspect, random, re
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


class SSA_test_xray():

	def __init__(self, toptest, ssa, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure; self.toptest = toptest
		#self.biascal.set_gpib_address(12)

	##########################################################################
	def xray_loop(self, period = 10, directory = '../SSA_Results/XRAY/', runtime = 1E8):
		rate = period * 60
		init_wait = 0
		self.configure_tests(directory)
		time_init = time.time()
		time_base = time_init - (rate - init_wait);
		time_curr = time_init;
		active = True
		self.toptest.ssa.pwr.on(display=False)
		while(((time_curr-time_init) < runtime) and active):
			try:
				time_curr = time.time()
				if( float(time_curr-time_base) > float(rate) ):
					time_base = time_curr
					self.toptest.RUN(runname = utils.date_time())
					utils.print_info('->  Total run time: {:7.3f}'.format(time.time()-time_base) )
				else:
					ret = self.toptest.idle_routine(filename = directory+'/idle_routine', runname = utils.date_time(), duration=60)
					if(ret == 'KeyboardInterrupt'): active = False
			except KeyboardInterrupt:
				active = False
				utils.print_info("\n\n\nUser interrupt. The routine will stop at the end of the iteration.\n\n\n")
			except:
				pass

	##########################################################################
	def configure_tests(self, directory):
		runtest = RunTest('xray')
		runtest.set_enable('Power', 'ON')
		runtest.set_enable('Initialize', 'ON')
		runtest.set_enable('Calibrate', 'ON')
		runtest.set_enable('Bias', 'ON')
		runtest.set_enable('alignment', 'ON')
		runtest.set_enable('Lateral_In', 'ON')
		runtest.set_enable('Cluster_Data', 'ON')
		runtest.set_enable('Pulse_Injection', 'ON')
		runtest.set_enable('L1_Data', 'ON')
		runtest.set_enable('Memory', 'ON')
		runtest.set_enable('noise_baseline', 'OFF')
		runtest.set_enable('trim_gain_offset_noise', 'ON')
		runtest.set_enable('DACs', 'ON')
		runtest.set_enable('Configuration', 'ON')
		runtest.set_enable('ring_oscillators', 'ON')
		runtest.set_enable('stub_l1_max_speed', 'ON')
		runtest.set_enable('ADC', 'ON')
		self.toptest.Configure(directory,  runtest )

		#runtest = RunTest('xray')
		#runtest.set_enable('Power', 'OFF')
		#runtest.set_enable('Initialize', 'ON')
		#runtest.set_enable('Calibrate', 'OFF')
		#runtest.set_enable('Bias', 'OFF')
		#runtest.set_enable('alignment', 'ON')
		#runtest.set_enable('Lateral_In', 'ON')
		#runtest.set_enable('Cluster_Data', 'ON')
		#runtest.set_enable('Pulse_Injection', 'ON')
		#runtest.set_enable('L1_Data', 'ON')
		#runtest.set_enable('Memory', 'OFF')
		#runtest.set_enable('noise_baseline', 'OFF')
		#runtest.set_enable('trim_gain_offset_noise', 'OFF')
		#runtest.set_enable('DACs', 'OFF')
		#runtest.set_enable('Configuration', 'OFF')
		#runtest.set_enable('ring_oscillators', 'OFF')
		#runtest.set_enable('stub_l1_max_speed', 'ON')
		#self.toptest.Configure(directory,  runtest )

	##########################################################################
	def plot_results(self, directory='../SSA_Results/XRAY/', doserate = 5.12E6):
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		timestart = -1
		TID=[]
		rdsummary = CSV.csv_to_array(directory+'GlobalSummary.csv', noheader = True)
		global_summary = rdsummary[1:,:]
		header = [str(x).strip(' ') for x in rdsummary[0]]
		for run in global_summary:
			timetag = re.findall("Chip_(.+)-(.+)-(.+)_(.+)-(.+)_.+", run[0])[0]
			timesec = 60*np.int(timetag[4])+3600*np.int(timetag[3])+3600*24*np.int(timetag[2])
			if(timestart<0): timestart = timesec
			TID.append( (timesec-timestart)*(doserate/3600.0)*1E-6 )
			run[0] = TID[-1]
			print("->  TID = {:7.3f}".format(TID[-1]))
		TID[0] = 1E-1
		######################################################################
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		for dataset in ['I_DVDD_calibrated', 'I_AVDD_calibrated', 'I_PVDD_calibrated']:
			variation = np.array(global_summary[:,header.index(dataset)], dtype=float)/np.float(global_summary[:,header.index(dataset)][0])
			plt.semilogx(TID, variation, 'x', label=dataset)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Current [mA]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		plt.savefig(directory+'/xray_power_consumption_variation.png', bbox_inches="tight");
		######################################################################
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		for dataset in ['I_DVDD_calibrated', 'I_AVDD_calibrated']:
			values = np.array(global_summary[:,header.index(dataset)], dtype=float)
			plt.semilogx(TID, values, 'x', label=dataset)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Current [mA]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(np.arange(10, 30, 2), fontsize=12)
		plt.savefig(directory+'/xray_power_consumption.png', bbox_inches="tight");
		######################################################################
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		for dataset in ['adc_AVDD']:
			variation = np.array(global_summary[:,header.index(dataset)], dtype=float)/np.float(global_summary[:,header.index(dataset)][0])
			c = next(color)
			x = TID
			y = np.array(global_summary[:,header.index(dataset)], dtype=float)
			plt.semilogx(x, y, 'x', label=dataset, color=c)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('ADC [count]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(list(range(3080,3181,5)), fontsize=12)
		plt.savefig(directory+'/xray_power_adc_avdd.png', bbox_inches="tight");
		######################################################################
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		for dataset in ['noise_mean_test']:
			variation = np.array(global_summary[:,header.index(dataset)], dtype=float)/np.float(global_summary[:,header.index(dataset)][0])
			#plt.semilogx(TID, variation, 'x', label=dataset)
			c = next(color)
			x = TID
			y = np.array(global_summary[:,header.index(dataset)], dtype=float)
			plt.semilogx(x, y, 'x', label=dataset, color=c)
			#xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
			#helper_y3 = scipy_interpolate.make_interp_spline(TID, y )
			#y_smuth = helper_y3(xnew)
			#y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 511, polyorder = 5)
			#plt.semilogx(xnew, y_hat , color=c, lw=1, alpha = 0.5)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Noise [ThDAC LSB]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		plt.savefig(directory+'/xray_noise_mean_test.png', bbox_inches="tight");

		######################################################################
		fe_gain = []; dac_gain = [];
		TID_list = []; noise={};
		cal_list = [1.2, 2.5]
		for cal in cal_list:
			noise[cal] = [];
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			if(not os.path.exists(dpath+'Test_frontend_cal_values.csv')): continue
			timetag = CSV.csv_to_array(dpath+'timetag.log', noheader = True)[0]
			timesec = timetag[5]+60*timetag[4]+3600*timetag[3]+3600*24*timetag[2]
			if(timestart<0): timestart = timesec
			TID = (timesec-timestart) * (doserate/3600.0)
			print("->  TID = {:7.3f}".format(TID*1E-6))
			TID_list.append(TID)
			for f in os.listdir( directory +'/'+ ddd ):
				rfn = re.findall(".+_frontend_Q-(.+)_noise.csv", f)
				if(len(rfn)>0):
					cal = np.float(rfn[0])
					if(cal in cal_list):
						noise[cal].append( CSV.csv_to_array(dpath+'Test_frontend_Q-{:0.3f}_noise.csv'.format(cal), noheader=False) )
						fe_gain.append( CSV.csv_to_array(dpath+'/Test_frontend_gain_mVfC.csv', noheader=False)[:,1] )

		######################################################################
		for cal in cal_list:
			noise[cal] = np.array(noise[cal], dtype=float);
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = TID_list
		plt.ylabel("Front-End Noise", fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		ser = noise[1.2][:,0,1:]
		noise_mean = np.array([np.mean(ser[:,i]) for i in range(len(x)) ])
		noise_std  = np.array([ np.std(ser[:,i]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_mean)
		noise_mean_smooth = helper_y3(xnew)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_std)
		noise_std_smooth = helper_y3(xnew)
		#noise_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 999, polyorder = 5)
		color=iter(sns.color_palette('deep'))
		c = next(color)
		#plt.fill_between(xnew, noise_mean_smooth - noise_std_smooth,  noise_mean_smooth + noise_std_smooth, color=c, alpha = 0.3, lw = 0)
		plt.semilogx(x, noise_mean, 'x', color='red', lw=1, label="noise mean")
		plt.errorbar(x, noise_mean, color='red', yerr=noise_std, linestyle='None', marker='', alpha = 0.3, lw = 2, label='noise std')
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Noise [ThDAC LSB]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		plt.savefig(directory+'/xray_noise_mean_errorbars.png', bbox_inches="tight");


		######################################################################
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = TID_list
		ser = fe_gain
		gain_mean = np.array([np.mean(ser[i]) for i in range(len(x)) ])
		gain_std  = np.array([ np.std(ser[i]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_mean)
		gain_mean_smooth = helper_y3(xnew)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_std)
		gain_std_smooth = helper_y3(xnew)
		#gain_hat = scypy_signal.savgol_filter(x = gain_mean_smooth , window_length = 999, polyorder = 5)
		color=iter(sns.color_palette('deep'))
		c = next(color)
		#plt.fill_between(xnew, gain_mean_smooth - gain_std_smooth,  gain_mean_smooth + gain_std_smooth, color=c, alpha = 0.3, lw = 0)
		plt.semilogx(x, gain_mean, 'x', color='red', lw=1, label="gain mean")
		plt.errorbar(x, gain_mean, color='red', yerr=gain_std, linestyle='None', marker='', alpha = 0.3, lw = 2, label='gain std')
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Gain [mV/fC]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		plt.savefig(directory+'/xray_FE-Gain_mean_errorbars.png', bbox_inches="tight");
		######################################################################
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		for i in [0, -1]:
			#plt.text(0.95,0.95, 'FE-Geain  0Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[0])),  horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			#plt.text(0.95,0.90, 'FE-Geain 95Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[-1])), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			if(i==0): label = 'FE-Geain  0 Mrad' + '(mean = {:6.2f})'.format(np.mean(fe_gain[0]))
			else:     label = 'FE-Geain 95 Mrad' + '(mean = {:6.2f})'.format(np.mean(fe_gain[-1]))
			ser = fe_gain[i]
			bn = np.arange(min(ser)*0.95, max(ser)*1.15, ((max(ser)-min(ser))/50.0) )
			plt.hist(ser,  density=True, bins = bn, alpha = 0.7, label=label)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser))
			m, s = scipy_stats.norm.fit(ser) # get mean and standard deviation
			pdf_g = scipy_stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			plt.plot(lnspc, pdf_g, 'r') # plot i
			sermean = np.mean(ser)
		plt.xlim(47,58)
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.ylabel('Gain [mV/fC]', fontsize=16)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		plt.savefig(directory+'/xray_FE-Gain_hist.png', bbox_inches="tight");
		##########################################################################
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = TID_list
		plt.ylabel("Front-End Noise", fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		ser = []
		for i in range(len(TID_list)):
			ser.append(
				self.Convert_Noise_dac_to_electrons(
					noise = noise[1.2][i ,0,1:],
					ThDAC_Gain = -np.float(global_summary[:,header.index('Bias_THDAC_GAIN')][i]) ,
					FE_Gain = fe_gain[i]))
		ser = np.array(ser)
		noise_mean = np.array([np.mean(ser[:,i]) for i in range(len(x)) ])
		noise_std  = np.array([ np.std(ser[:,i]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_mean)
		noise_mean_smooth = helper_y3(xnew)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_std)
		noise_std_smooth = helper_y3(xnew)
		#noise_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 999, polyorder = 5)
		color=iter(sns.color_palette('deep'))
		c = next(color)
		#plt.fill_between(xnew, noise_mean_smooth - noise_std_smooth,  noise_mean_smooth + noise_std_smooth, color=c, alpha = 0.3, lw = 0)
		plt.semilogx(x, noise_mean, 'x', color='red', lw=1, label="noise mean")
		plt.errorbar(x, noise_mean, color='red', yerr=noise_std, linestyle='None', marker='', alpha = 0.3, lw = 2, label='noise std')
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Noise [e]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		plt.savefig(directory+'/xray_noise_mean_electrons.png', bbox_inches="tight");

		######################################################################
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		for i in [0, -1]:
			val = ser[:,i]
			#plt.text(0.95,0.95, 'FE-Geain  0Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[0])),  horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			#plt.text(0.95,0.90, 'FE-Geain 95Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[-1])), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			if(i==0): label = 'FE-Noise 0 Mrad' + '(mean = {:6.2f})'.format(np.mean(val[0]))
			else:     label = 'FE-Noise 95 Mrad' + '(mean = {:6.2f})'.format(np.mean(val[-1]))
			bn = np.arange(min(val), max(val), 4)
			plt.hist(val,  density=True, bins = bn, alpha = 0.7, label=label)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(val))
			m, s = scipy_stats.norm.fit(val) # get mean and standard deviation
			pdf_g = scipy_stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			plt.plot(lnspc, pdf_g, 'r') # plot i
			valmean = np.mean(val)
		#plt.xlim(47,58)
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.xlabel('Noise [e]', fontsize=16)
		plt.ylabel('Normalised dist', fontsize=16)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		plt.savefig(directory+'/xray_Noise_hist.png', bbox_inches="tight");




	def Convert_Noise_dac_to_electrons(self, noise, ThDAC_Gain, FE_Gain): # use [lsb - mV/lsb - mV/fC]
		Noise_e = ( np.array(noise) * ThDAC_Gain * 1E-3) / (FE_Gain * 1E12 * ph_const.elementary_charge )
		for i in range(len(Noise_e)):
			if Noise_e[i] > 600:
				print('High Noise strip: ' + str(i) + '   ' + str(noise[i]) + '   ' +   str(ThDAC_Gain) + '   ' +   str(FE_Gain) +  '   ' +   str(Noise[i]))
				print('Average:          ' + '  '   + '   ' + str(np.mean(noise)) + '   ' +   str(np.mean(ThDAC_Gain)) + '   ' +   str(np.mean(FE_Gain)) +  '   ' +   str(np.mean(Noise)))
		return Noise_e
