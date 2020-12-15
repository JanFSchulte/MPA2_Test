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
from matplotlib.ticker import MultipleLocator


class SSA_test_climatic_chamber():

	def __init__(self, toptest, ssa, I2C, fc7, cal, biascal, pwr, test):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.toptest = toptest
		#self.biascal.set_gpib_address(12)

	##########################################################################
	def climatic_chamber_full_test(self, temperature=99, directory = '../SSA_Results/climatic/', maintest=True, digtest=True):
		self.configure_tests(directory)
		self.toptest.ssa.pwr.on(display=False)
		time_init = time.time()
		active = True
		try:
			time_curr = time.time()
			if(maintest):
				self.toptest.RUN(runname = ('climatic_test_T{:d}C'.format(temperature)) , write_header = True )
				utils.print_info('->  Total run time: {:7.3f}'.format(time.time()-time_curr) )
			if(digtest):
				for voltage in [0.8, 0.85, 0.9, 1.00, 1.05, 1.10, 1.15, 1.20, 1.25]:
					ret = self.toptest.idle_routine(voltage=voltage, duration=10, filename = directory+'/Fast_Dig_Test', runname = ('climatic_test_T{:d}C_V{:3.3f}'.format(temperature, voltage)))
		except KeyboardInterrupt:
			active = False
			utils.print_info("\n\n\nUser interrupt. The routine will stop at the end of the iteration.\n\n\n")
		except:
			print('ERROR')
			pass


	##########################################################################
	def configure_tests(self, directory):
		runtest = RunTest('climatic')
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

		#runtest = RunTest('climatic')
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

	def check_data_integrity(self, directory='../SSA_Results/climatic/'):
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		rdsummary = CSV.csv_to_array(directory+'GlobalSummary.csv', noheader = True)
		loglist =  [str(x).strip(' /') for x in rdsummary[1:,:][:,0]]
		for i in loglist:
			if(i not in dirs): print('Missing {:s} from dirs'.format(i))
		for i in dirs:
			if(i not in loglist): print('Missing {:s} from dirs'.format(i))



	def plot_results(self, directory='../SSA_Results/climatic/'):

		Temperature1, header, global_summary   = self._read_summary_data(  directory=directory)
		Temperature2, fe_gain, noise = self._read_frontend_data( directory=directory)
		Temperature3, configuration = self._read_static_configuration_data(directory=directory)

		self.dataset_sum  = Temperature1, header, global_summary
		self.dataset_afe  = Temperature1, header, global_summary, Temperature2, fe_gain, noise
		self.dataset_conf = Temperature3, configuration

		self.plot_parameter(
			parameters = ['I_DVDD_calibrated', 'I_AVDD_calibrated'],
			name='power_consumption',  ylabel = 'Current relative variation', ylim=[14, 26],
			newfigure=True, directory=directory,  dlabel='', dataset=self.dataset_sum)

		self.plot_parameter(
			parameters = ['Bias_D5ALLV_uncalibrated', 'Bias_D5ALLV_calibrated'],
			name='Bias_D5ALLV',  ylabel = 'DAC output voltage [mV]', ylim=[70, 90],
			newfigure=True, directory=directory,  dlabel='', dataset=self.dataset_sum)

		self.plot_parameter(
			parameters = ['Bias_D5BFEED_uncalibrated', 'Bias_D5BFEED_calibrated'],
			name='Bias_D5BFEED',  ylabel = 'DAC output voltage [mV]',  ylim=[70, 90],
			newfigure=True, directory=directory,  dlabel='', dataset=self.dataset_sum)

		self.plot_parameter(
			parameters = ['Bias_BOOSTERBASELINE_uncalibrated', 'Bias_BOOSTERBASELINE_calibrated'],
			name='Bias_BOOSTERBASELINE',  ylabel = 'DAC output voltage [mV]',  ylim=[560, 660],
			newfigure=True, directory=directory,  dlabel='', dataset=self.dataset_sum)

		self.plot_configuration_val(
			parameters = ['Bias_D5BFEED'],
			name='Bias_D5BFEED',  ylabel = 'Configuration value', ylim=[10,20],
			newfigure=True, directory=directory, dlabel='', dataset=self.dataset_conf )

		self.plot_configuration_val(
			parameters = ['Bias_D5ALLI', 'Bias_D5BFEED', 'Bias_D5PREAMP'],
			name='Bias_Config_',  ylabel = 'Configuration value', ylim=[10,20],
			newfigure=True, directory=directory, dlabel='', dataset=self.dataset_conf )

		#self.plot_configuration_val_vref(
		#	parameters = ['Bias_D5ALLI', 'Bias_D5BFEED', 'Bias_D5PREAMP'],
		#	name='Bias_Config_VREF_',  ylabel = 'Configuration value', ylim=[12,32],
		#	newfigure=True, directory=directory, dlabel='', dataset=self.dataset_conf )

		self.plot_configuration_val(
			parameters = ['Bias_D5ALLI', 'Bias_D5BFEED', 'Bias_D5PREAMP', 'ADC_VREF'],
			name='Bias_Config_VREF_',  ylabel = 'Configuration value', ylim=[10, 32],
			newfigure=True, directory=directory, dlabel='', dataset=self.dataset_conf )

		self.plot_configuration_val(
			parameters = ['ADC_VREF'],
			name='Bias_Config',  ylabel = 'Configuration value', ylim=[10,20],
			newfigure=True, directory=directory, dlabel='', dataset=self.dataset_conf )


		self.plot_parameter(
			parameters = ['VBG_calibrated'],
			name='Bias_VBG',  ylabel = 'Bandgap voltage', ylim=[250, 270],
			directory=directory, dataset=self.dataset_sum )

		self.plot_parameter(
			parameters = ['Ring_DEL_BL', 'Ring_INV_BL'],
			name='Ring_INV_DEL_BC',  ylabel = 'Frequency percent variation [%]', ylim=[],
			directory=directory,  dataset=self.dataset_sum)

		self.plot_temperature_sensor(
			directory=directory,  dataset=self.dataset_sum)

		self.plot_fe_noise_evolution_el(
			directory=directory,   dataset=self.dataset_afe)

		self.plot_fe_noise_evolution(
			directory=directory,   dataset=self.dataset_afe)

		self.plot_parameter(
			parameters = ['L1_data_latch_0.9', 'L1_data_latch_1.0', 'L1_data_latch_1.1'],
			name='L1_data_latch',  ylabel = 'DAC output voltage', ylim=[],
			newfigure=True, directory=directory,  dlabel='', dataset=self.dataset_sum)

		self.plot_parameter(
			parameters = ['fe_gain_mean'],
			name='fe_gain_mean',  ylabel = 'mV/fC', ylim=[40, 60],
			newfigure=True, directory=directory,  dlabel='', dataset=self.dataset_sum)



		#self.plot_fe_noise_hist(         directory=directory,   dataset=self.dataset_afe, Temperature_select = [0, -1], labels = [0, 140])
#
		#self.plot_fe_gain_evolution( directory=directory, dataset=self.dataset_afe)
		#self.plot_fe_gain_hist(      directory=directory, dataset=self.dataset_afe, Temperature_select = [0,-1], labels = [0,140] )


	def _read_summary_data(self, directory):
		#directory='../SSA_Results/climatic/'
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		timestart = -1
		Temperature=[]
		rdsummary = CSV.csv_to_array(directory+'GlobalSummary.csv', noheader = True)
		global_summary = rdsummary[1:,:]
		header = [str(x).strip(' ') for x in rdsummary[0]]
		for run in global_summary:
			temperature_tag = np.int(re.findall("Chip_.+T(.+)C_.+", run[0])[0])
			Temperature.append( temperature_tag )
			#run[0] = Temperature[-1]
			#print("->  Temperature = {:7.3f} Mrad".format(Temperature[-1]))
		return Temperature, header, global_summary


	def _read_frontend_data(self, directory):
		fe_gain = []; dac_gain = [];
		Temperature_list = []; noise={};
		cal_list = [1.2, 2.5]
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		for cal in cal_list: noise[cal] = [];
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			if(not os.path.exists(dpath+'/Test_frontend_cal_values.csv')): continue
			temperature_tag = re.findall("Chip_.+T(.+)C_.+", dpath)
			if(len(temperature_tag)==0): continue
			temperature_tag = np.int(temperature_tag[0])
			#print(timetag)
			print("->  Temperature = {:5d} C - ".format(temperature_tag))
			Temperature_list.append(temperature_tag)
			for f in os.listdir( directory +'/'+ ddd ):
				rfn = re.findall(".+_frontend_Q-(.+)_noise.csv", f)
				if(len(rfn)>0):
					cal = np.float(rfn[0])
					if(cal in cal_list):
						noise[cal].append( CSV.csv_to_array(dpath+'Test_frontend_Q-{:0.3f}_noise.csv'.format(cal), noheader=False) )
						fe_gain.append( CSV.csv_to_array(dpath+'/Test_frontend_gain_mVfC.csv', noheader=False)[:,1] )
		for cal in cal_list:
			noise[cal] = np.array(noise[cal], dtype=float);
		return Temperature_list, fe_gain, noise

	def _read_ADC_VREF_data(self, directory='../SSA_Results/climatic/'):
		Temperature_list = []; vref=[];
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			if(not os.path.exists(dpath+'/Test_ADC_VREF/Test___Caracteristics_ADC_VREF.csv')): continue
			temperature_tag = re.findall("Chip_.+T(.+)C_.+", dpath)
			if(len(temperature_tag)==0): continue
			temperature_tag = np.int(temperature_tag[0])
			#print(timetag)
			#print("->  Temperature = {:5d} C - ".format(temperature_tag))
			Temperature_list.append(temperature_tag)
			vref.append(CSV.csv_to_array(dpath+'/Test_ADC_VREF/Test___Caracteristics_ADC_VREF.csv'))
		return Temperature_list, vref

	def _read_ADC_IREF_data(self, directory='../SSA_Results/climatic/'):
		Temperature_list = []; vref=[];
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			if(not os.path.exists(dpath+'/Test_ADC_VREF/Test___Caracteristics_ADC_IREF.csv')): continue
			temperature_tag = re.findall("Chip_.+T(.+)C_.+", dpath)
			if(len(temperature_tag)==0): continue
			temperature_tag = np.int(temperature_tag[0])
			#print(timetag)
			#print("->  Temperature = {:5d} C - ".format(temperature_tag))
			Temperature_list.append(temperature_tag)
			vref.append(CSV.csv_to_array(dpath+'/Test_ADC_VREF/Test___Caracteristics_ADC_IREF.csv'))
		return Temperature_list, vref



	def _read_static_configuration_data(self, directory):
		Temperature_list = [];
		configuration = []
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "Chip_" in s])
		timestart = -1
		for ddd in dirs:
			dpath = directory+'/'+ddd+'/'
			if(not os.path.exists(dpath+'/Test_frontend_cal_values.csv')): continue
			temperature_tag = re.findall("Chip_.+T(.+)C_.+", dpath)
			if(len(temperature_tag)==0): continue
			temperature_tag = np.int(temperature_tag[0])
			#print(timetag)
			print("->  Temperature = {:5d} C - ".format(temperature_tag))
			Temperature_list.append(temperature_tag)
			for f in os.listdir( directory +'/'+ ddd ):
				rfn = re.findall(".+configuration.csv", f)
				if(len(rfn)>0):
					configuration.append(
						self.ssa.ctrl.load_configuration(
							file=directory +'/'+ ddd+'/'+f,
							strips='all', peri=True, display=False, upload_on_chip = False, rtarray = True) )
						#config[config[:,1] == 'Bias_D5BFEED']
		Temperature_list[0] = 1E5
		configuration = np.array(configuration)
		return Temperature_list, configuration




	def plot_parameter_variation(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/climatic/', dlabel='', dataset='calculate'):
		try:
			Temperature, header, global_summary = dataset
		except:
			Temperature, header, global_summary= self._read_summary_data(directory=directory)
		if(newfigure):
			fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		for dataset in parameters:
			variation = np.array(global_summary[:,header.index(dataset)], dtype=float)/np.float(global_summary[:,header.index(dataset)][0])
			plt.plot(Temperature, 100.0*variation, 'x', label=dataset+dlabel)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([-40, 60])
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/climatic_'+name+'_variation.png', bbox_inches="tight");
			plt.close()

	def plot_parameter(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/climatic/', dlabel='', dataset='calculate'):
		try:
			Temperature, header, global_summary = dataset
		except:
			Temperature, header, global_summary= self._read_summary_data(directory=directory)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		for dataset in parameters:
			values = np.array(global_summary[:,header.index(dataset)], dtype=float)
			plt.plot(Temperature, values, 'x', label=dataset)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([-40, 60])
		ax.set_xticks(list(range(-40,60, 10)))
		ax.xaxis.set_minor_locator(MultipleLocator(5))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		#plt.yticks(np.arange(10, 30, 2), fontsize=12)
		if(newfigure): plt.savefig(directory+'/climatic_'+name+'.png', bbox_inches="tight");

	def plot_temperature_sensor(self, newfigure=True, directory='../SSA_Results/climatic/', dlabel='', dataset='calculate'):
		try:
			Temperature, header, global_summary = dataset
		except:
			Temperature, header, global_summary= self._read_summary_data(directory=directory)

		color=iter(sns.color_palette('deep')*3)
		t_mean = np.array(global_summary[:,header.index('adc_TEMP_mean')], dtype=float)
		t_std  = np.array(global_summary[:,header.index('adc_TEMP_std')], dtype=float)
		vref_actual = np.array(global_summary[:,header.index('ADC_VREF_calibrated')], dtype=float)
		vref_ideal = 825
		t_mean_mv = (vref_actual/(2**12))*t_mean
		t_std_mv = (vref_actual/(2**12))*t_std

		fig = plt.figure(figsize=(8,6))
		ax = plt.gca()
		ax2 = ax.twinx()
		ax.get_yaxis().tick_left()

		ax2.plot(Temperature, t_mean, 'x', label='Temperature sensor (mean raw ADC code)',color='blue')
		ax2.errorbar(Temperature, t_mean, color='blue', yerr=3*t_std, xerr=2, linestyle='None', marker='', alpha = 0.3, lw = 2, label='measure error')
		ax2.set_ylim([2**12/8*1.2, 2**12/8*2.5])
		ax2.set_ylabel('ADC output code', fontsize=16)

		ax.plot(Temperature, t_mean_mv, 'x', label='Temperature sensor (normalised for actual Vref)',color='red')
		ax.errorbar(Temperature, t_mean_mv, color='red', yerr=3*t_std_mv, xerr=2, linestyle='None', marker='', alpha = 0.3, lw = 2, label='measure error')
		ax.set_ylim([vref_ideal/8*1.2, vref_ideal/8*2.5])
		ax.set_ylabel('mV', fontsize=16)

		lines, labels = ax.get_legend_handles_labels()
		lines2, labels2 = ax2.get_legend_handles_labels()
		leg = ax2.legend(lines + lines2, labels + labels2, loc=0, fontsize = 10, frameon=True )

		leg.get_frame().set_linewidth(1.0)

		ax.get_xaxis().tick_bottom();
		ax.set_xlim([-40, 60])
		ax.set_xticks(list(range(-40,61, 10)))
		ax.xaxis.set_minor_locator(MultipleLocator(2.5))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')


		ax.set_xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		plt.savefig(directory+'/climatic_adc_temperature_sensor_mV.png', bbox_inches="tight");




	def plot_configuration_val(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/climatic/', dlabel='', dataset='calculate'):
		try:
			Temperature, configuration = dataset
		except:
			Temperature, configuration = self._read_static_configuration_data(directory=directory)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		for par in parameters:
			values = configuration[ configuration[:,:,1] == par][:, 2]
			plt.plot(Temperature, values, 'x', label=par)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([-40, 60])
		ax.set_xticks(list(range(-40,61, 10)))
		ax.xaxis.set_minor_locator(MultipleLocator(2.5))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')
		ax.set_yticks(range(0,33,4))
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		#plt.yticks(np.arange(10, 30, 2), fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/climatic_'+name+'configuration_setting.png', bbox_inches="tight");
			plt.close()


	def plot_configuration_val_vref(self, parameters = [], name='',  ylabel = '', ylim=False, newfigure=True, directory='../SSA_Results/climatic/', dlabel='', dataset='calculate'):
		try:
			Temperature, configuration = dataset
		except:
			Temperature, configuration = self._read_static_configuration_data(directory=directory)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.gca()
		ax2 = ax.twinx()
		for par in parameters:
			values = configuration[ configuration[:,:,1] == par][:, 2]
			ax.plot(Temperature, values, 'x', label=par)
		for par in ['ADC_VREF']:
			values = configuration[ configuration[:,:,1] == par][:, 2]
			ax2.plot(Temperature, values, 'x', label=par)

		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([-40, 60])
		ax.set_xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		ax.set_xticks(list(range(-40,61, 10)))
		ax.xaxis.set_minor_locator(MultipleLocator(2.5))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')
		if(ylim): ax.set_ylim(ylim)
		else: ax.set_ylim(auto=True)
		ax.set_ylabel('Calibration DAC Code', fontsize=16)
		ax2.set_ylim([0, 32])
		ax2.set_ylabel('ADC-Vref DAC Code', fontsize=16)

		lines, labels = ax.get_legend_handles_labels()
		lines2, labels2 = ax2.get_legend_handles_labels()
		leg = ax2.legend(lines + lines2, labels + labels2, loc=0, fontsize = 10, frameon=True )
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)

		#plt.yticks(np.arange(10, 30, 2), fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/climatic_'+name+'configuration_setting.png', bbox_inches="tight");
			plt.close()


	def plot_fe_noise_evolution(self, directory='../SSA_Results/climatic_LDR/', dataset='calculate', dlabel='', newfigure=1, color='red'):
		try:
			Temperature, header, global_summary, Temperature_list, fe_gain, noise = dataset
		except:
			Temperature, header, global_summary = self._read_summary_data(  directory=directory)
			Temperature_list, fe_gain, noise    = self._read_frontend_data( directory=directory)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = Temperature_list
		plt.ylabel("Front-End Noise", fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		ser = np.array(noise[1.2][:,0,1:])
		noise_mean = np.array([np.mean(ser[i,:]) for i in range(len(x)) ])
		noise_std  = np.array([ np.std(ser[i,:]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		plt.plot(x, noise_mean, 'x', color=color, lw=1, label="Front-End mean noise - no sensor connected {:s}".format(dlabel))
		plt.errorbar(x, noise_mean, color=color, yerr=noise_std*2, linestyle='None', marker='', alpha = 0.3, lw = 2, label=r'2$\sigma$ range {:s}'.format(dlabel))
		plt.errorbar(x, noise_mean, color=color, xerr=2, linestyle='None', marker='', alpha = 0.3, lw = 2, label='temperature measurement error {:s}'.format(dlabel))
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([-40, 60])
		ax.set_ylim([1.0, 1.7])
		ax.set_xticks(list(range(-40,61, 10)))
		#ax.set_yticks(list(range(240,351, 10)))
		ax.xaxis.set_minor_locator(MultipleLocator(2.5))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')
		plt.ylabel('Noise [e-]', fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure): plt.savefig(directory+'/climatic_noise_mean_thdac_counts.png', bbox_inches="tight");



	def plot_fe_gain_evolution(self, directory='../SSA_Results/climatic_LDR/', dataset='calculate', dlabel='', newfigure=1, color='red'):
		try:
			Temperature, header, global_summary, Temperature_list, fe_gain, noise = dataset
		except:
			Temperature, header, global_summary = self._read_summary_data(  directory=directory)
			Temperature_list, fe_gain, noise    = self._read_frontend_data( directory=directory)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = np.sort(Temperature_list)
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
		plt.plot(x, gain_mean, 'x', color=color, lw=1, label="gain mean "+str(dlabel))
		plt.errorbar(x, gain_mean, color=color, yerr=gain_std, linestyle='None', marker='', alpha = 0.3, lw = 2, label='gain std '+str(dlabel))
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_ylim([45,65])
		plt.ylabel('Gain [mV/fC]', fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure):
			plt.savefig(directory+'/climatic_FE-Gain_mean_errorbars.png', bbox_inches="tight");
			plt.close()




	def plot_fe_gain_hist(self, directory='../SSA_Results/climatic_LDR/', dataset='calculate', Temperature_select = [0, -1], labels = [0, 100]):
		try:
			Temperature, header, global_summary, Temperature_list, fe_gain, noise = dataset
		except:
			Temperature, header, global_summary = self._read_summary_data(  directory=directory)
			Temperature_list, fe_gain, noise    = self._read_frontend_data( directory=directory)
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		for i in Temperature_select:
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
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.ylabel('Gain [mV/fC]', fontsize=16)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		plt.savefig(directory+'/climatic_FE-Gain_hist.png', bbox_inches="tight");
		plt.close()


	##########################################################################
	def plot_fe_noise_evolution_el(self, directory='../SSA_Results/climatic_LDR/', dataset='calculate', dlabel='', newfigure=1, color='red'):
		try:
			Temperature, header, global_summary, Temperature_list, fe_gain, noise = dataset
		except:
			Temperature, header, global_summary = self._read_summary_data(  directory=directory)
			Temperature_list, fe_gain, noise    = self._read_frontend_data( directory=directory)
		if(newfigure): fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = Temperature_list
		plt.ylabel("Front-End Noise", fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		ser = []

		#return global_summary, header, Temperature_list, noise, fe_gain
		for i in range(len(Temperature_list)):
			ser.append(
				self.Convert_Noise_dac_to_electrons(
					noise = noise[1.2][i ,0,1:],
					ThDAC_Gain = -np.float(global_summary[:,header.index('Bias_THDAC_GAIN')][i]) ,
					FE_Gain = fe_gain[i] ))
		ser = np.array(ser)
		noise_mean = np.array([np.mean(ser[i,:]) for i in range(len(x)) ])
		noise_std  = np.array([ np.std(ser[i,:]) for i in range(len(x)) ])
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		plt.plot(x, noise_mean, 'x', color=color, lw=1, label="Front-End mean noise - no sensor connected {:s} \n(Standard deviation of the error function fitting the S-curve.\n Strip FE Gain evaluated from the local threshold at 1fC and 2fC)".format(dlabel))
		plt.errorbar(x, noise_mean, color=color, yerr=noise_std*2, linestyle='None', marker='', alpha = 0.3, lw = 2, label=r'2$\sigma$ range {:s}'.format(dlabel))
		plt.errorbar(x, noise_mean, color=color, xerr=2, linestyle='None', marker='', alpha = 0.3, lw = 2, label='temperature measurement error {:s}'.format(dlabel))
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([-40, 60])
		ax.set_ylim([240, 351])
		ax.set_xticks(list(range(-40,61, 10)))
		ax.set_yticks(list(range(240,351, 10)))
		ax.xaxis.set_minor_locator(MultipleLocator(2.5))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')
		plt.ylabel('Noise [e-]', fontsize=16)
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(newfigure): plt.savefig(directory+'/climatic_noise_mean_electrons_b.png', bbox_inches="tight");

	##########################################################################
	def plot_ADC_VREF(self, directory='../SSA_Results/climatic/', dataset='calculate', newfigure=1):
		try:
			Temp, header, global_summary, Temp2, fe_gain, noise = dataset
		except:
			Temp, header, global_summary = self._read_summary_data(  directory=directory)
		Temperature_list, vref_list    = self._read_ADC_VREF_data( directory=directory)
		Temperature_list, iref_list    = self._read_ADC_IREF_data( directory=directory)

		if(newfigure): fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylabel("VREF [mV]", fontsize=16)
		plt.xlabel(r"Configuration code", fontsize=16)
		color=iter(sns.color_palette('deep')*5)
		for pltcnt in range(len(Temperature_list)):
			plt.plot(vref_list[pltcnt][:,0], vref_list[pltcnt][:,1]*1E3, 'x', color=next(color), lw=1, label="T=${:3d}^\circ$C".format(Temperature_list[pltcnt]))
		leg = ax.legend(fontsize = 8, frameon=True, ncol=2) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		ax.set_xlim([0, 32])
		ax.set_ylim([600, 900])
		ax.set_xticks(list(range(0,33, 2)))
		ax.set_yticks(list(range(600,901, 25)))
		ax.xaxis.set_minor_locator(MultipleLocator(1))
		ax.grid(which='major', axis='x', linestyle='--')
		ax.grid(which='minor', axis='x', linestyle='--')
		if(newfigure): plt.savefig(directory+'/climatic_ADC_VREF__caracteristics.png', bbox_inches="tight");

		

	def plot_fe_noise_hist(self, directory='../SSA_Results/climatic_LDR/', dataset='calculate', Temperature_select = [0, -1], labels = [0, 100]):
		try:
			Temperature, header, global_summary, Temperature_list, fe_gain, noise = dataset
		except:
			Temperature, header, global_summary = self._read_summary_data(  directory=directory)
			Temperature_list, fe_gain, noise    = self._read_frontend_data( directory=directory)
		fig = plt.figure(figsize=(8,6))
		ax = plt.subplot(111)
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		for i in Temperature_select:
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
		plt.xlabel(r"Temperature ($^\circ$C)", fontsize=16)
		plt.ylabel('Noise [e-]', fontsize=16)
		leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		plt.savefig(directory+'/climatic_noise_e_hist.png', bbox_inches="tight");
		plt.close()


	def Convert_Noise_dac_to_electrons(self, noise, ThDAC_Gain, FE_Gain): # use [lsb - mV/lsb - mV/fC]
		Noise_e = ( np.array(noise) * ThDAC_Gain * 1E-3) / (FE_Gain * 1E12 * ph_const.elementary_charge )
		for i in range(len(Noise_e)):
			if Noise_e[i] > 600:
				print('High Noise strip: ' + str(i) + '   ' + str(noise[i]) + '   ' +   str(ThDAC_Gain) + '   ' +   str(FE_Gain) +  '   ' +   str(noise[i]))
				print('Average:          ' + '  '   + '   ' + str(np.mean(noise)) + '   ' +   str(np.mean(ThDAC_Gain)) + '   ' +   str(np.mean(FE_Gain)) +  '   ' +   str(np.mean(noise)))
		return Noise_e
