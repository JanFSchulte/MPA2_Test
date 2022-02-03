from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.logs_utility import *
from collections import OrderedDict
from scipy import interpolate as scipy_interpolate
from scipy import constants as ph_const
from scipy import stats as scipy_stats
import time, sys, inspect, random, re
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


class SSA_test_xray():

	def __init__(self, toptest, ssa, I2C, fc7, cal, biascal, pwr, test):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.toptest = toptest
		#self.biascal.set_gpib_address(12)

	##########################################################################
	def xray_loop(self, period = 20, directory = '../SSA_Results/XRAY/', runtime = 1E8, init_wait=1):
		rate = period * 60
		self.configure_tests(directory)
		self.toptest.ssa.pwr.on(display=False)
		time_init = time.time()
		time_base = time_init - (rate - init_wait);
		time_curr = time_init;
		active = True
		run_counter = 0
		while(((time_curr-time_init) < runtime) and active):
			try:
				time_curr = time.time()
				if( float(time_curr-time_base) > float(rate) ):
					time_base = time_curr
					self.toptest.RUN(runname = utils.date_time(), write_header = (run_counter==0))
					utils.print_info('->  Total run time: {:7.3f}'.format(time.time()-time_base) )
					run_counter += 1
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

	def check_data_integrity(self, directory='../SSA_Results/XRAY/'):
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		rdsummary = CSV.csv_to_array(directory+'GlobalSummary.csv', noheader = True)
		loglist =  [str(x).strip(' /') for x in rdsummary[1:,:][:,0]]
		for i in loglist:
			if(i not in dirs): print('Missing {:s} from dirs'.format(i))
		for i in dirs:
			if(i not in loglist): print('Missing {:s} from dirs'.format(i))








	def plot_results(self, directory='../SSA_Results/XRAY_LDR/', doserate = 0.512E6):

		TID1, header, global_summary   = self.__read_summary_data(  directory=directory, doserate=doserate)
		TID2, fe_gain, noise = self.__read_frontend_data( directory=directory, doserate=doserate)
		TID3, configuration = self.__read_static_configuration_data(directory=directory, doserate=doserate)

		self.dataset_sum  = TID1, header, global_summary
		self.dataset_afe  = TID1, header, global_summary, TID2, fe_gain, noise
		self.dataset_conf = TID3, configuration

		self.plot_parameter_variation(
			parameters = ['I_DVDD_calibrated', 'I_AVDD_calibrated', 'I_PVDD_calibrated'],
			name='power_consumption',  ylabel = 'Current percent variation [%]', ylim=[90, 105],
			newfigure=True, directory=directory, doserate=doserate, dlabel='', dataset=self.dataset_sum )

		self.plot_parameter(
			parameters = ['I_DVDD_calibrated', 'I_AVDD_calibrated'],
			name='power_consumption',  ylabel = 'Current relative variation', ylim=[10, 25],
			newfigure=True, directory=directory, doserate=doserate, dlabel='', dataset=self.dataset_sum)

		self.plot_parameter(
			parameters = ['adc_AVDD'],
			name='adc_AVDD',  ylabel = 'ADC [count]', ylim=[2800, 3200],
			newfigure=True, directory=directory, doserate=doserate, dlabel='', dataset=self.dataset_sum)

		self.plot_parameter_variation(
			parameters = ['Bias_D5ALLV_uncalibrated', 'Bias_D5ALLV_calibrated'],
			name='Bias_D5ALLV',  ylabel = 'DAC output voltage percent variation  [%]', ylim=[],
			newfigure=True, directory=directory, doserate=doserate, dlabel='', dataset=self.dataset_sum)

		#self.plot_configuration_val(
		#	parameters = ['Bias_D5BFEED'],
		#	name='Bias_D5BFEED',  ylabel = 'Configuration value', ylim=[0,31],
		#	newfigure=True, directory=directory, doserate=doserate, dlabel='', dataset=self.dataset_conf )

		#self.plot_configuration_val(
		#	parameters = ['Bias_D5ALLI', 'Bias_D5BFEED', 'Bias_D5PREAMP'],
		#	name='Bias_Config',  ylabel = 'Configuration value', ylim=[0,31],
		#	newfigure=True, directory=directory, doserate=doserate, dlabel='', dataset=self.dataset_conf )

		self.plot_parameter_variation(
			parameters = ['VBG_calibrated'],
			name='Bias_VBG',  ylabel = 'Bandgap voltage percent variation [%]', ylim=[99.4,100.2],
			directory=directory, doserate=doserate,dataset=self.dataset_sum )

		self.plot_parameter_variation(
			parameters = ['Ring_DEL_BL', 'Ring_INV_BL'],
			name='Ring_INV_DEL_BC',  ylabel = 'Frequency percent variation [%]', ylim=[],
			directory=directory, doserate=doserate, dataset=self.dataset_sum)

		#self.plot_fe_noise_evolution(    directory=directory, doserate=doserate,  dataset=self.dataset_afe)
		self.plot_fe_noise_evolution_el( directory=directory, doserate=doserate,  dataset=self.dataset_afe)
		self.plot_fe_noise_hist(         directory=directory, doserate=doserate,  dataset=self.dataset_afe, tid_select = [0, -1], labels = [0, 140])

		self.plot_fe_gain_evolution( directory=directory, doserate=doserate,  dataset=self.dataset_afe)
		self.plot_fe_gain_hist(      directory=directory, doserate=doserate,  dataset=self.dataset_afe, tid_select = [0,-1], labels = [0,140] )



	def plot_all_results(self, directory=['../SSA_Results/XRAY_LDR/', '../SSA_Results/XRAY_HDR/'], doserate=[0.512E6, 5.120E6]):

		self.plot_results(directory=directory[0], doserate = doserate[0])
		self.res_ldr = [self.dataset_sum, self.dataset_afe, self.dataset_conf]

		self.plot_results(directory=directory[1], doserate = doserate[1])
		self.res_hdr = [self.dataset_sum, self.dataset_afe, self.dataset_conf]

		self.plot_fe_gain_evolution_doserates(     directory=directory, doserate=doserate, dataset=[self.res_ldr[1], self.res_hdr[1]] )
		self.plot_fe_noise_evolution_el_doserates( directory=directory, doserate=doserate, dataset=[self.res_ldr[1], self.res_hdr[1]] )

		self.plot_parameter_variation_doserates(
			parameter = ['I_DVDD_calibrated', 'I_AVDD_calibrated', 'I_PVDD_calibrated'],
			name='power_consumption',  ylabel = 'Current percent variation [%]', ylim=[90, 105],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )

		self.plot_parameter_doserates(
			parameter = ['I_DVDD_calibrated', 'I_AVDD_calibrated'],
			name='power_consumption',  ylabel = 'Current relative variation', ylim=[10, 25],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )

		self.plot_parameter_doserates(
			parameter = ['adc_AVDD'],
			name='adc_AVDD',  ylabel = 'ADC [count]', ylim=[2800, 3200],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )

		self.plot_parameter_variation_doserates(
			parameter = ['Bias_D5ALLV_uncalibrated', 'Bias_D5ALLV_calibrated'],
			name='Bias_D5ALLV',  ylabel = 'DAC output voltage percent variation [%]', ylim=[],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )

		self.plot_parameter_variation_doserates(
			parameter = ['VBG_calibrated'],
			name='Bias_VBG',  ylabel = 'Bandgap voltage percent variation [%]', ylim=[99.4,100.2],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )

		self.plot_parameter_variation_doserates(
			parameter = ['Ring_INV_BC'],
			name='Ring_INV_BC',  ylabel = 'Frequency percent variation [%]', ylim=[55,110],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )

		self.plot_parameter_variation_doserates(
			parameter = ['Ring_DEL_BC'],
			name='Ring_DEL_BC',  ylabel = 'Frequency percent variation [%]', ylim=[55,110],
			directory=directory, doserate=doserate, dataset=[self.res_ldr[0], self.res_hdr[0]] )





	def __read_summary_data(self, directory, doserate):
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		timestart = -1
		TID=[]
		rdsummary = CSV.csv_to_array(directory+'GlobalSummary.csv', noheader = True)
		global_summary = rdsummary[1:,:]
		header = [str(x).strip(' ') for x in rdsummary[0]]
		for run in global_summary:
			timetag = re.findall("Chip_(.+)-(.+)-(.+)_(.+)-(.+)_.+", run[0])[0]
			#timesec = 60*np.int(timetag[4])+3600*np.int(timetag[3])+3600*24*np.int(timetag[2])
			date = datetime.datetime(int(timetag[0]), int(timetag[1]), int(timetag[2]), int(timetag[3]), int(timetag[4]))
			time_tuple = date.timetuple()
			timesec = time.mktime(time_tuple)
			if(timestart<0): timestart = timesec
			TID.append( (timesec-timestart)*(doserate/3600.0) )
			run[0] = TID[-1]
			#print("->  TID = {:7.3f} Mrad".format(TID[-1]))
		TID[0] = 1E5
		return TID, header, global_summary




	def __read_frontend_data(self, directory, doserate):
		fe_gain = []; dac_gain = [];
		TID_list = []; noise={};
		cal_list = [1.2, 2.5]
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		for cal in cal_list: noise[cal] = [];
		timestart = -1
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			if(not os.path.exists(dpath+'Test_frontend_cal_values.csv')): continue
			timetag = CSV.csv_to_array(dpath+'timetag.log', noheader = True)[0]
			#timesec = timetag[5]+60*timetag[4]+3600*timetag[3]+3600*24*timetag[2]
			date = datetime.datetime(int(timetag[0]), int(timetag[1]), int(timetag[2]), int(timetag[3]), int(timetag[4]))
			time_tuple = date.timetuple()
			timesec = time.mktime(time_tuple)
			if(timestart<0): timestart = timesec
			TID = (timesec-timestart) * (doserate/3600.0)
			#print(timetag)
			print("->  TID = {:7.3f} Mrad - ".format(TID*1E-6))
			TID_list.append(TID)
			for f in os.listdir( directory +'/'+ ddd ):
				rfn = re.findall(".+_frontend_Q-(.+)_noise.csv", f)
				if(len(rfn)>0):
					cal = np.float(rfn[0])
					if(cal in cal_list):
						noise[cal].append( CSV.csv_to_array(dpath+'Test_frontend_Q-{:0.3f}_noise.csv'.format(cal), noheader=False) )
						fe_gain.append( CSV.csv_to_array(dpath+'/Test_frontend_gain_mVfC.csv', noheader=False)[:,1] )
		for cal in cal_list:
			noise[cal] = np.array(noise[cal], dtype=float);
		TID_list[0] = 1E5
		return TID_list, fe_gain, noise

	def __read_static_configuration_data(self, directory, doserate):
		TID_list = [];
		configuration = []
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		timestart = -1
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			timetag = CSV.csv_to_array(dpath+'timetag.log', noheader = True)[0]
			date = datetime.datetime(int(timetag[0]), int(timetag[1]), int(timetag[2]), int(timetag[3]), int(timetag[4]))
			time_tuple = date.timetuple()
			timesec = time.mktime(time_tuple)
			if(timestart<0): timestart = timesec
			TID = (timesec-timestart) * (doserate/3600.0)
			print("->  TID = {:7.3f} Mrad - ".format(TID*1E-6))
			TID_list.append(TID)
			for f in os.listdir( directory +'/'+ ddd ):
				rfn = re.findall(".+configuration.csv", f)
				if(len(rfn)>0):
					configuration.append(
						self.ssa.ctrl.load_configuration(
							file=directory +'/'+ ddd+'/'+f,
							strips='all', peri=True, display=False, upload_on_chip = False, rtarray = True) )
						#config[config[:,1] == 'Bias_D5BFEED']
		TID_list[0] = 1E5
		configuration = np.array(configuration)
		return TID_list, configuration




	def plot_parameter_variation(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/XRAY/', doserate = 0.512E6, dlabel='', dataset='calculate'):
		try:
			TID, header, global_summary = dataset
		except:
			TID, header, global_summary= self.__read_summary_data(directory=directory, doserate=doserate)
		if(newfigure):
			fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		for dataset in parameters:
			variation = np.array(global_summary[:,header.index(dataset)], dtype=float)/np.float(global_summary[:,header.index(dataset)][0])
			plt.semilogx(TID, 100.0*variation, 'x', label=dataset+dlabel)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([1E5, 1E9])
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/xray_'+name+'_variation.png', bbox_inches="tight");
			plt.close()


	def plot_parameter_variation_doserates(self, parameter, name, ylabel = '', ylim=False, directory=['../SSA_Results/XRAY_LDR/', '../SSA_Results/XRAY_HDR/'], doserate=[0.512E6, 5.120E6], dataset=[False, False]):
		fig = plt.figure(figsize=(8,6))

		self.plot_parameter_variation(
			parameters = parameter, name=name, ylabel=ylabel, ylim = ylim,
			dlabel=' [{:5.3f} Mrad/h]'.format(doserate[0]*1e-6),
			doserate=doserate[0], directory=directory[0],
			newfigure=0, dataset=dataset[0])

		self.plot_parameter_variation(
			parameters = parameter, name=name, ylabel=ylabel, ylim = ylim,
			dlabel=' [{:5.3f} Mrad/h]'.format(doserate[1]*1e-6),
			doserate=doserate[1], directory=directory[1],
			newfigure=0, dataset=dataset[1])

		plt.savefig(directory[0]+'/xray_doserate_'+name+'_variation.png', bbox_inches="tight");
		plt.savefig(directory[1]+'/xray_doserate_'+name+'_variation.png', bbox_inches="tight");
		plt.close()




	def plot_parameter(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/XRAY/', doserate = 0.512E6, dlabel='', dataset='calculate'):
		try:
			TID, header, global_summary = dataset
		except:
			TID, header, global_summary= self.__read_summary_data(directory=directory, doserate=doserate)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		for dataset in parameters:
			values = np.array(global_summary[:,header.index(dataset)], dtype=float)
			plt.semilogx(TID, values, 'x', label=dataset)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([1E5, 1E9])
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		#plt.yticks(np.arange(10, 30, 2), fontsize=12)
		if(newfigure): plt.savefig(directory+'/xray_'+name+'.png', bbox_inches="tight");


	def plot_parameter_doserates(self, parameter, name, ylabel = '', ylim=False, directory=['../SSA_Results/XRAY_LDR/', '../SSA_Results/XRAY_HDR/'], doserate=[0.512E6, 5.120E6], dataset=[False, False]):
		fig = plt.figure(figsize=(8,6))

		self.plot_parameter(
			parameters = parameter, name=name, ylabel=ylabel, ylim = ylim,
			dlabel=' [{:5.3f} Mrad/h]'.format(doserate[0]*1e-6),
			doserate=doserate[0], directory=directory[0],
			newfigure=0, dataset=dataset[0])

		self.plot_parameter(
			parameters = parameter, name=name, ylabel=ylabel, ylim = ylim,
			dlabel=' [{:5.3f} Mrad/h]'.format(doserate[1]*1e-6),
			doserate=doserate[1], directory=directory[1],
			newfigure=0, dataset=dataset[1])

		plt.savefig(directory[0]+'/xray_doserate_'+name+'.png', bbox_inches="tight");
		plt.savefig(directory[1]+'/xray_doserate_'+name+'.png', bbox_inches="tight");
		plt.close()



	def plot_configuration_val(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/XRAY/', doserate = 0.512E6, dlabel='', dataset='calculate'):
		try:
			TID, configuration = dataset
		except:
			TID, configuration = self.__read_static_configuration_data(directory=directory, doserate=doserate)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		for par in parameters:
			values = configuration[ configuration[:,:,1] == par][:, 2]
			plt.semilogx(TID, values, 'x', label=par)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([1E5, 1E9])
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		#plt.yticks(np.arange(10, 30, 2), fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/xray_'+name+'configuration_setting.png', bbox_inches="tight");
			plt.close()


	def plot_fe_noise_evolution(self, directory='../SSA_Results/XRAY_LDR/', doserate = 0.512E6, dataset='calculate'):
		try:
			TID, header, global_summary, TID_list, fe_gain, noise = dataset
		except:
			TID, header, global_summary = self.__read_summary_data(  directory=directory, doserate=doserate)
			TID_list, fe_gain, noise    = self.__read_frontend_data( directory=directory, doserate=doserate)
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = np.sort(TID_list)
		plt.ylabel("Front-End Noise", fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		ser = noise[1.2][:,0,1:]
		#return ser, x
		noise_mean = np.array([np.mean(ser[i,:]) for i in range(len(x)) ])
		noise_std  = np.array([ np.std(ser[i,:]) for i in range(len(x)) ])
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
		plt.errorbar(x, noise_mean, color='red', yerr=noise_std, linestyle='None', marke='', alpha = 0.3, lw = 2, label='noise std')
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_ylim([0,2])
		plt.ylabel('Noise [ThDAC LSB]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		plt.savefig(directory+'/xray_noise_mean_errorbars.png', bbox_inches="tight");
		plt.close()


	def plot_fe_gain_evolution(self, directory='../SSA_Results/XRAY_LDR/', doserate = 0.512E6, dataset='calculate', dlabel='', newfigure=1, color='red'):
		try:
			TID, header, global_summary, TID_list, fe_gain, noise = dataset
		except:
			TID, header, global_summary = self.__read_summary_data(  directory=directory, doserate=doserate)
			TID_list, fe_gain, noise    = self.__read_frontend_data( directory=directory, doserate=doserate)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = np.sort(TID_list)
		ser = fe_gain
		gain_mean = np.array([np.mean(ser[i]) for i in range(len(x)) ])
		gain_std  = np.array([ np.std(ser[i]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		helper_y3 = scipy_interpolate.make_interp_spline(x, gain_mean)
		gain_mean_smooth = helper_y3(xnew)
		helper_y3 = scipy_interpolate.make_interp_spline(x, gain_std)
		gain_std_smooth = helper_y3(xnew)
		#gain_hat = scypy_signal.savgol_filter(x = gain_mean_smooth , window_length = 999, polyorder = 5)
		#color=iter(sns.color_palette('deep'))
		#c = next(color)
		#plt.fill_between(xnew, gain_mean_smooth - gain_std_smooth,  gain_mean_smooth + gain_std_smooth, color=c, alpha = 0.3, lw = 0)
		plt.semilogx(x, gain_mean, 'x', color=color, lw=1, label="gain mean "+str(dlabel))
		plt.errorbar(x, gain_mean, color=color, yerr=gain_std, linestyle='None', marker='', alpha = 0.3, lw = 2, label='gain std '+str(dlabel))
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_ylim([45,65])
		plt.ylabel('Gain [mV/fC]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/xray_FE-Gain_mean_errorbars.png', bbox_inches="tight");
			plt.close()

	def plot_fe_gain_evolution_doserates(self, directory=['../SSA_Results/XRAY_LDR/', '../SSA_Results/XRAY_HDR/'], doserate=[0.512E6, 5.120E6], dataset=[False, False]):
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep'))
		self.plot_fe_gain_evolution( directory=directory[0], doserate=doserate[0],  dataset=dataset[0], dlabel=' [{:5.3f} Mrad/h]'.format(doserate[0]*1e-6), newfigure=0, color=next(color))
		next(color)
		self.plot_fe_gain_evolution( directory=directory[1], doserate=doserate[1],  dataset=dataset[1], dlabel=' [{:5.3f} Mrad/h]'.format(doserate[1]*1e-6), newfigure=0, color=next(color))
		plt.savefig(directory[0]+'/xray_FE-Gain_mean_errorbars.png', bbox_inches="tight");
		plt.savefig(directory[1]+'/xray_FE-Gain_mean_errorbars.png', bbox_inches="tight");
		plt.close()



	def plot_fe_gain_hist(self, directory='../SSA_Results/XRAY_LDR/', doserate = 0.512E6, dataset='calculate', tid_select = [0, -1], labels = [0, 100]):
		try:
			TID, header, global_summary, TID_list, fe_gain, noise = dataset
		except:
			TID, header, global_summary = self.__read_summary_data(  directory=directory, doserate=doserate)
			TID_list, fe_gain, noise    = self.__read_frontend_data( directory=directory, doserate=doserate)
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		for i in tid_select:
			#plt.text(0.95,0.95, 'FE-Geain  0Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[0])),  horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			#plt.text(0.95,0.90, 'FE-Geain 95Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[-1])), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			label = 'FE-Geain {:5.1f} Mrad (mean = {:6.2f})'.format(labels[i], np.mean(fe_gain[i]) )
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
		plt.close()


	##########################################################################
	def plot_fe_noise_evolution_el(self, directory='../SSA_Results/XRAY_LDR/', doserate = 0.512E6, dataset='calculate', dlabel='', newfigure=1, color='red'):
		try:
			TID, header, global_summary, TID_list, fe_gain, noise = dataset
		except:
			TID, header, global_summary = self.__read_summary_data(  directory=directory, doserate=doserate)
			TID_list, fe_gain, noise    = self.__read_frontend_data( directory=directory, doserate=doserate)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = TID_list
		plt.ylabel("Front-End Noise", fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		ser = []
		#return global_summary, header, TID_list, noise, fe_gain
		for i in range(len(TID_list)):
			ser.append(
				self.Convert_Noise_dac_to_electrons(
					noise = noise[1.2][i ,0,1:],
					ThDAC_Gain = -np.float(global_summary[:,header.index('Bias_THDAC_GAIN')][i]) ,
					FE_Gain = fe_gain[i] ))
		ser = np.array(ser)
		noise_mean = np.array([np.mean(ser[i,:]) for i in range(len(x)) ])
		noise_std  = np.array([ np.std(ser[i,:]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_mean)
		noise_mean_smooth = helper_y3(xnew)
		helper_y3 = scipy_interpolate.make_interp_spline(x, noise_std)
		noise_std_smooth = helper_y3(xnew)
		#noise_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 999, polyorder = 5)
		#color=iter(sns.color_palette('deep'))
		#c = next(color)
		#plt.fill_between(xnew, noise_mean_smooth - noise_std_smooth,  noise_mean_smooth + noise_std_smooth, color=c, alpha = 0.3, lw = 0)
		plt.semilogx(x, noise_mean, 'x', color=color, lw=1, label="noise mean {:s}".format(dlabel))
		plt.errorbar(x, noise_mean, color=color, yerr=noise_std, linestyle='None', marker='', alpha = 0.3, lw = 2, label='noise std {:s}'.format(dlabel))
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_ylim([150,450])
		plt.ylabel('Noise [e]', fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure): plt.savefig(directory+'/xray_noise_mean_electrons.png', bbox_inches="tight");


	def plot_fe_noise_evolution_el_doserates(self, directory=['../SSA_Results/XRAY_LDR/', '../SSA_Results/XRAY_HDR/'], doserate=[0.512E6, 5.120E6], dataset=[False, False]):
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep'))
		self.plot_fe_noise_evolution_el( directory=directory[0], doserate=doserate[0],  dataset=dataset[0], dlabel=' [{:5.3f} Mrad/h]'.format(doserate[0]*1e-6), newfigure=0, color=next(color))
		next(color)
		self.plot_fe_noise_evolution_el( directory=directory[1], doserate=doserate[1],  dataset=dataset[1], dlabel=' [{:5.3f} Mrad/h]'.format(doserate[1]*1e-6), newfigure=0, color=next(color))
		plt.savefig(directory[0]+'/xray_doserate_noise_mean_electrons.png', bbox_inches="tight");
		plt.savefig(directory[1]+'/xray_doserate_noise_mean_electrons.png', bbox_inches="tight");
		plt.close()





	def plot_fe_noise_hist(self, directory='../SSA_Results/XRAY_LDR/', doserate = 0.512E6, dataset='calculate', tid_select = [0, -1], labels = [0, 100]):
		try:
			TID, header, global_summary, TID_list, fe_gain, noise = dataset
		except:
			TID, header, global_summary = self.__read_summary_data(  directory=directory, doserate=doserate)
			TID_list, fe_gain, noise    = self.__read_frontend_data( directory=directory, doserate=doserate)
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		for i in tid_select:
			#plt.text(0.95,0.95, 'FE-Geain  0Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[0])),  horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			#plt.text(0.95,0.90, 'FE-Geain 95Mrad' + '= {:6.2f}'.format(np.mean(fe_gain[-1])), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')

			ser = self.Convert_Noise_dac_to_electrons(
				noise = noise[1.2][i ,0,1:],
				ThDAC_Gain = -np.float(global_summary[:,header.index('Bias_THDAC_GAIN')][i]) ,
				FE_Gain = fe_gain[i] )
			label = 'FE-Noise {:5.1f} Mrad (mean = {:6.2f})'.format(labels[i], np.mean(ser) )
			bn = np.arange(min(ser)*0.95, max(ser)*1.15, ((max(ser)-min(ser))/50.0) )
			plt.hist(ser,  density=True, bins = bn, alpha = 0.7, label=label)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser))
			m, s = scipy_stats.norm.fit(ser) # get mean and standard deviation
			pdf_g = scipy_stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			plt.plot(lnspc, pdf_g, 'r') # plot i
		plt.xlim(200,450)
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.xlabel('TID [rad]', fontsize=16)
		plt.ylabel('Noise [e-]', fontsize=16)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		plt.savefig(directory+'/xray_noise_e_hist.png', bbox_inches="tight");
		plt.close()



	def plot_results_old(self, directory='../SSA_Results/XRAY/', doserate = 0.512E6):

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
		plt.close()




	def Convert_Noise_dac_to_electrons(self, noise, ThDAC_Gain, FE_Gain): # use [lsb - mV/lsb - mV/fC]
		Noise_e = ( np.array(noise) * ThDAC_Gain * 1E-3) / (FE_Gain * 1E12 * ph_const.elementary_charge )
		for i in range(len(Noise_e)):
			if Noise_e[i] > 600:
				print('High Noise strip: ' + str(i) + '   ' + str(noise[i]) + '   ' +   str(ThDAC_Gain) + '   ' +   str(FE_Gain) +  '   ' +   str(noise[i]))
				print('Average:          ' + '  '   + '   ' + str(np.mean(noise)) + '   ' +   str(np.mean(ThDAC_Gain)) + '   ' +   str(np.mean(FE_Gain)) +  '   ' +   str(np.mean(noise)))
		return Noise_e
