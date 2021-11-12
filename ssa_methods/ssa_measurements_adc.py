from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from itertools import product as itertools_product
import seaborn as sns
import re
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate as scipy_interpolate
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
from collections import OrderedDict
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.gridspec as gridspec
from scipy import stats
import re
import datetime


class SSA_measurements_adc():

	def __init__(self, ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal = False):
		self.ssa = ssa; self.I2C = I2C; self.fc7 = fc7; self.utils = utils;
		self.cal = cal; self.bias = biascal; self.muxmap = analog_mux_map;
		self.pwr = pwr; self.seuutil = seuutil;


	#####################################################################
	def dnl_inl_histogram_sample(self, runtime=3600, freq=0.1, show=0, directory='../SSA_Results/adc_measures/', filename='ADC_samples.csv', continue_on_same_file=1):
		if(continue_on_same_file and os.path.exists(directory+'/'+filename)):
			adchist = CSV.csv_to_array(filename=directory+'/'+filename)[:,1]
		else:
			adchist = np.zeros(2**12+1, dtype=int)
		cnt  = 0; told = 0; wd = 0
		self.ssa.analog.adc_measure_ext_pad()
		runtime = round(float(runtime)*freq)/freq #to have n copleate cycles
		#ret = self.ssa.analog.WVF.SetWaveform(func='ramp', freq=freq, offset=-0.1, vpp=1.1)
		#if ret is False: return False
		if(filename == False):
			filename = 'ADC_samples_'+str(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')+'.csv')
		timestart = time.time()
		while ((time.time()-timestart) < runtime):
			wd = 0
			while(wd < 3):
				try:
					res = int(np.round(self.ssa.analog.adc_measure_ext_pad(nsamples=1, reinit_if_error=False)))
					utils.print_inline('{:8d}'.format(res) )
					#time.sleep( randint(0,3)*0.0005 )
					break
				except(KeyboardInterrupt):
					return('User interrupt')
				except:
					wd +=1;
					utils.print_warning('Exception {:d}'.format(wd))
			if res is False: return False
			else: adchist[int(res)]+=1
			cnt+=1
			tcur = time.time()
			if ((tcur-told)>1.1): #update histogram every second
				told = tcur
				utils.print_inline('{:8d} ->  ADC collected {:d} samples'.format(res, cnt))
				#with open(filename, 'w') as fo:
				#	fo.write('{:8d},\n'.format(res))
				CSV.array_to_csv(adchist, filename=directory+'/'+filename)
		#f.close()
		utils.print_log('->  ADC total number of samples taken is '+str(cnt))
		dnlh, inlh = self.dnl_inl_histogram_plot(directory=directory, filename=filename, plot=show)
		return dnlh, inlh, adchist

	#####################################################################
	def dnl_inl_histogram_plot(self, minc=1, maxc=4095, directory='../SSA_Results/adc_measures/', filename='ADC_samples.csv', plot=True):
		dnlh = np.zeros(4096)
		inlh = np.zeros(4096)
		maxim = 0; inl=0.0;
		adchist = CSV.csv_to_array(directory+'/'+filename)[:,1]
		fo=open("../SSA_Results//adc_dnl_inl.csv","w")
		stepsize = float(np.sum(adchist[minc:maxc]))/(maxc-minc)
		for i in range(minc,maxc+1):
			dnl = (float(adchist[i])/stepsize)-1.0
			dnlh[i] = dnl
			inl+=dnl
			inlh[i] = inl
			fo.write("{:8d}, {:9.6f}, {:9.6f}, {:9.6f}\n".format(i, dnl, inl, float(adchist[i])) )
		fo.close()
		plt.clf()
		color=iter(sns.color_palette('deep'))
		if(plot):
			fig = plt.figure(figsize=(18,6))
			ax = plt.subplot(111)
			c = next(color);
			plt.ticklabel_format(axis='y', style='sci')
			plt.plot(range(minc,maxc,1), np.array(adchist[minc:maxc])/np.sum(adchist[minc:maxc]), '-', color=c)
			plt.ylabel('Normalised probability', fontsize=16)
			plt.xlabel('ADC converted value', fontsize=16)
			ax.get_xaxis().tick_bottom();
			ax.get_yaxis().tick_left()
			ax.set_xlim([0, 4096])
			ax.set_xticks(list(range(0,4097, 256)))
			ax.xaxis.set_minor_locator(MultipleLocator(64))
			ax.grid(which='major', axis='x', linestyle='--')
			ax.grid(which='minor', axis='x', linestyle='--')
			plt.savefig(directory+'histogram.png', bbox_inches="tight");
			######################################################
			fig = plt.figure(figsize=(18,6))
			ax = plt.subplot(111)
			c = next(color);
			plt.plot(range(minc,maxc,1), dnlh[minc:maxc], '-', color=c)
			plt.ylabel('DNL', fontsize=16)
			plt.xlabel('ADC converted value', fontsize=16)
			ax.get_xaxis().tick_bottom();
			ax.get_yaxis().tick_left()
			ax.set_xlim([0, 4096])
			ax.set_ylim([-0.25, 1])
			ax.set_xticks(list(range(0,4097, 256)))
			ax.xaxis.set_minor_locator(MultipleLocator(64))
			ax.grid(which='major', axis='x', linestyle='--')
			ax.grid(which='minor', axis='x', linestyle='--')
			plt.savefig(directory+'DNL.png', bbox_inches="tight");
			######################################################
			fig = plt.figure(figsize=(18,6))
			ax = plt.subplot(111)
			c = next(color);
			plt.plot(range(minc,maxc,1), inlh[minc:maxc], '-', color=c)
			plt.ylabel('INL', fontsize=16)
			plt.xlabel('ADC converted value', fontsize=16)
			ax.get_xaxis().tick_bottom();
			ax.get_yaxis().tick_left()
			ax.set_xlim([0, 4096])
			ax.set_ylim([-2.2, 2.2])
			ax.set_xticks(list(range(0,4097, 256)))
			ax.xaxis.set_minor_locator(MultipleLocator(64))
			ax.grid(which='major', axis='x', linestyle='--')
			ax.grid(which='minor', axis='x', linestyle='--')
			plt.savefig(directory+'INL.png', bbox_inches="tight");
		#leg = ax.legend(fontsize = 10, frameon=True )
		#leg.get_frame().set_linewidth(1.0)
		#plt.show()
		return dnlh, inlh
		#adc_dnl_inl_histogram()

	def noise_distribution(nsamples=1E3, directory='../SSA_Results/adc_measures/', filename='ADC_noise_samples.csv'):

		res = int(np.round(self.ssa.analog.adc_measure_ext_pad(nsamples=1, reinit_if_error=False)))
		utils.print_inline('{:8d}'.format(res) )

		#f.close()

	#####################################################################################################
	def adc_plot(filename = '../SSA_Results/adc_measures/Test_ssa_adc_measurements.csv'):
		data = CSV.csv_to_array(filename)
		fig = plt.figure(figsize=(8,6))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(True)
		ax.spines["right"].set_visible(True)
		plt.xticks(list(arange(0,0.9,0.1)), fontsize=16)
		plt.yticks(list(range(0,2**12+1,2**8)), fontsize=16)
		plt.xlabel('Input voltage [V]', fontsize=16)
		plt.ylabel('Converted code', fontsize=16)
		plt.plot(data[:,1]	, data[:,2], 'x')

	#####################################################################################################
	def measure_curve(self, nsamples=10, npoints=2**16, directory='../SSA_Results/ADC/', plot=True, start_point=-0.005, end_point=0.9, note=''):
		vrange = np.linspace(start_point, end_point, npoints+1)
		rcode = []
		time.sleep(0.1)
		self.ssa.analog.set_output_mux('highimpedence')
		self.ssa.analog.adc_measure_ext_pad(nsamples=1)
		self.bias.SetMode('Keithley_Sourcemeter_2410_GPIB')
		self.bias.multimeter.config__voltage_source(compliance=10E-3, range=1)
		time.sleep(0.1)
		ratecounter = [time.time(), 0]
		mrate = 0; timeleft=1
		for vinput in vrange:
			self.bias.multimeter.set_voltage(vinput)
			time.sleep(0.001)
			r = self.ssa.analog.adc_measure_ext_pad(nsamples=nsamples)
			rcode.append(r)
			progress = len(rcode)/np.float(npoints)
			ctime = time.time()
			if((ctime-ratecounter[0]) > 1):
				mrate = (len(rcode)-ratecounter[1]) / (ctime - ratecounter[0])
				ratecounter = [ctime, len(rcode)]
				timeleft = (npoints-len(rcode))/mrate
			utils.print_inline(
				'    Converting {:7.3f} mV to code {:9.3f} | progress: {:5.1f}% | rate: {:5.3f} sample/sec | time left: {:s}        '.format(
				(vinput*1E3), r, progress*100, mrate, str(datetime.timedelta(seconds=timeleft))[:-7] ))
			if not os.path.exists(directory): os.makedirs(directory)
			with open( (directory+'ssa_adc_measurements'+note+'.csv'), 'a') as fo:
				fo.write('\n{:8d}, {:12.6f}, {:12.6f}'.format(len(rcode),(vinput*1E3),r) )
		self.bias.multimeter.config__voltage_measure()
		self.bias.multimeter.disable()
		self.ssa.analog.set_output_mux('highimpedence')
		print('\n')
		rtvect = np.array([vrange, rcode], dtype=float).transpose()
		#CSV.array_to_csv( rtvect,  (directory+'ssa_adc_measurements'+note+'.csv'))
		fitvect = rtvect[ [rtvect[:,0]>0] ]
		fitvect = fitvect[ fitvect[:,0]<0.85 ]
		gain, ofs, sigma = utils.linear_fit(fitvect[:,0], fitvect[:,1])
		utils.print_good("->  Gain({:12s}) = {:9.3f} mV/cnt".format('ADC', gain*1.0E3))
		utils.print_good("->  Offs({:12s}) = {:9.3f} mV    ".format('ADC', ofs*1.0E3))
		if(plot):
			plt.plot(rtvect[:,0], rtvect[:,1], 'x', c='blue')
			plt.plot(np.array([0,0.9]), gain*np.array([0,0.9])+ofs, '-', c='red')
			plt.show()
		return [gain, ofs, sigma]

	#####################################################################################################
	def measure_curve_parametric(self, nsamples=100, npoints=2**7, adc_trimming_range=[0, 15, 31, 47, 63], adc_ref_range=[0, 7, 15, 23, 31], directory='../SSA_Results/ADC/parametric_ref_and_trimming/', chip=''):
		self.bias.SetMode('Keithley_Sourcemeter_2410_GPIB')
		for adc_ref in adc_ref_range:
			self.ssa.analog.adc_set_referenence(adc_ref)
			for adc_trimming in adc_trimming_range:
				self.ssa.analog.adc_set_trimming(adc_trimming)
				self.measure_curve(
					nsamples=nsamples, npoints=npoints, start_point=-0.005, end_point=0.9,
					directory=directory+chip, plot=False,
					note='__ref_{:d}__trim_{:d}'.format(adc_ref, adc_trimming))

	#####################################################################################################
	def measure_curve_parametric_plot(self, directory='../SSA_Results/ADC/parametric_ref_and_trimming/'):
		fig = plt.figure(figsize=(8,6))
		color=iter(sns.color_palette('deep')*3)
		ax = plt.subplot(111)
		ref_range = []; trim_range = [];
		for filename in os.listdir(directory):
			refind = re.findall("ssa_adc_measurements__ref_(\d+)__trim_(\d+).csv", filename)
			if(len(refind)>0):
				ref_range.append(np.int(refind[0][0]))
				trim_range.append(np.int(refind[0][1]))

		for adc_trim in np.unique(trim_range):
			c = next(color)
			for adc_ref in np.unique(ref_range):
				filename = "ssa_adc_measurements__ref_{:d}__trim_{:d}.csv".format(adc_ref, adc_trim)
				data = CSV.csv_to_array(directory+filename)
				plt.plot(data[:,1], data[:,2], 'x', color=c, label='ref_{:d}'.format(adc_ref))

		#leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
		#leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('ADC Count', fontsize=16)
		plt.xlabel('Input Voltage [V]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		#plt.savefig(directory+'/xray_'+name+'_variation.png', bbox_inches="tight");

	#####################################################################################################
	def temperature_sensor(self,  nsamples=100, directory='../SSA_Results/ADC/temperature_sensor/'):
		if(not os.path.exists(directory)): os.makedirs(directory)
		rep = self.ssa.analog.adc_measure_temperature(nsamples=nsamples, raw=True)
		CSV.ArrayToCSV(array = np.array(rep), filename = directory+"adc_Temperature_Sensor_samples.csv", transpose = True)
		tsens_mean, tsens_std, tsens_rms = utils.eval_mean_std_rms(rep)
		utils.print_good('->  ADC parameter measure [{:s}] ->  mean = {:7.3f},  std={:7.3f}'.format('temperature', tsens_mean, tsens_std))
		return [tsens_mean, tsens_std]

	#####################################################################################################
	def measure_param(self, parameter='DVDD', nsamples=100, directory='../SSA_Results/ADC/param/'):
		if(not os.path.exists(directory)): os.makedirs(directory)
		rep = self.ssa.analog.adc_measure(testline=parameter, nsamples=nsamples, raw=True)
		CSV.ArrayToCSV(array = np.array(rep), filename = directory+"adc_{:s}_samples.csv".format(parameter), transpose = True)
		tsens_mean, tsens_std, tsens_rms = utils.eval_mean_std_rms(rep)
		utils.print_good('->  ADC parameter measure [{:s}] ->  mean = {:7.3f},  std={:7.3f}'.format(parameter, tsens_mean, tsens_std))
		return [tsens_mean, tsens_std]

	#####################################################################################################
	def mesure_vref(self, filename='/ADC/VREF/', runname='', chip='chip_0/chip_0'):
		# manual measure switching chips on the testboard
		if not os.path.exists("../SSA_Results/" +filename+chip): os.makedirs("../SSA_Results/" +filename+chip)
		VBG = self.bias.get_voltage('VBG')
		vref = self.dac_linearity(
			name = 'ADC_VREF', eval_inl_dnl = True, nbits = 5, npoints = -1,return_raw=True,
			filename = filename+chip, plot = False, filemode = 'a', runname = runname)
		iref = self.dac_linearity(
			name = 'ADC_IREF', eval_inl_dnl = True, nbits = 5, npoints = -1, return_raw=True,
			filename = filename+chip, plot = False, filemode = 'a', runname = runname)
		[vref_DNL, vref_INL, vref_gain, vref_ofs, vref_raw]  = vref
		[iref_DNL, iref_INL, iref_gain, iref_ofs, iref_raw]  = iref
		vref_min =   vref_raw[1][0]; vref_max =   vref_raw[1][-1]
		iref_min =   iref_raw[1][0]; iref_max =   iref_raw[1][-1]
		fo = "../SSA_Results/" + filename+chip + "_" + str(runname) + "_parameters_" + 'ADC_VREF_IREF'
		data = [['    ', 'vref_min', 'vref_max', 'vref_gain', 'vref_INL', 'vref_DNL', 'VBG'],
				['VREF', vref_min*1E3, vref_max*1E3, vref_gain*1E3, vref_INL, vref_DNL, VBG*1E3],
				['IREF', iref_min*1E3, iref_max*1E3, iref_gain*1E3, iref_INL, iref_DNL, VBG*1E3]]
		CSV.ArrayToCSV(array = np.array(data), filename = fo + ".csv", transpose = True)
		with open("../SSA_Results/" +filename+'ADC_VREF_summary.csv', 'a') as fo:
			fo.write(('\n{:16s}, '+'{:9.3f}, '*9).format(chip, VBG*1E3, vref_min*1E3, vref_max*1E3, vref_gain*1E3, iref_min*1E3, iref_max*1E3, iref_gain*1E3, vref_INL, vref_DNL) )

	#####################################################################################################
	def analize_vref(self, filename='/ADC/VREF/'):
		filename='/ADC/VREF/'
		directory = "../SSA_Results/" +filename
		data = CSV.csv_to_array(directory+'ADC_VREF_summary.csv')
		VBG_data = np.array(data[:,1], dtype=float)
		VBG_mean, VBG_std, VBG_rms = utils.eval_mean_std_rms(VBG_data)
		vdacdata_overall = []; idacdata_overall = []
		vref_min_overall = []; vref_max_overall = []
		dirs = os.listdir(directory)
		dirs = np.sort([s for s in dirs if "chip_" in s])
		for i in dirs:
			for file in os.listdir(directory+i):
				if(fnmatch.fnmatch(file, '*Caracteristics_ADC_VREF.csv')):
					vdacdata = CSV.csv_to_array(directory+'/'+i+'/'+file)[:,1]
				if(fnmatch.fnmatch(file, '*Caracteristics_ADC_IREF.csv')):
					idacdata = CSV.csv_to_array(directory+'/'+i+'/'+file)[:,1]
			VREF_LSB_mv = 1E3*(vdacdata[1:]-vdacdata[0:-1])
			VREF_LSB_mv_mean, VREF_LSB_mv_std, VREF_LSB_mv_rms = utils.eval_mean_std_rms(VREF_LSB_mv)
			VREF_MIN_mv = 1E3*(vdacdata[0])
			vref_min_overall.append(VREF_MIN_mv)
			VREF_MAX_mv = 1E3*(vdacdata[-1])
			vref_max_overall.append(VREF_MAX_mv)
			IREF_LSB_mv = 1E3*(idacdata[1:]-idacdata[0:-1])
			IREF_LSB_mv_mean, IREF_LSB_mv_std, IREF_LSB_mv_rms = utils.eval_mean_std_rms(IREF_LSB_mv)
			print(('|{:8s} | '+'{:7.3f} |'*8).format(i, VREF_LSB_mv_mean, VREF_LSB_mv_std, VREF_LSB_mv_rms, IREF_LSB_mv_mean, IREF_LSB_mv_std, IREF_LSB_mv_rms, VREF_MIN_mv, VREF_MAX_mv  ))
			vdacdata_overall.extend(vdacdata)
			idacdata_overall.extend(vdacdata)
		vdacdata_overall = np.array(vdacdata_overall)
		idacdata_overall = np.array(idacdata_overall)
		VREF_LSB_mv = 1E3*(vdacdata_overall[1:]-vdacdata_overall[0:-1])
		VREF_LSB_mv_mean, VREF_LSB_mv_std, VREF_LSB_mv_rms = utils.eval_mean_std_rms(VREF_LSB_mv)
		IREF_LSB_mv = 1E3*(idacdata_overall[1:]-idacdata_overall[0:-1])
		IREF_LSB_mv_mean, IREF_LSB_mv_std, IREF_LSB_mv_rms = utils.eval_mean_std_rms(IREF_LSB_mv)
		VREF_MIN_mv_mean, VREF_MIN_mv_std, VREF_MIN_mv_rms = utils.eval_mean_std_rms(np.array(vref_min_overall))
		VREF_MAX_mv_mean, VREF_MAX_mv_std, VREF_MAX_mv_rms = utils.eval_mean_std_rms(np.array(vref_max_overall))
		print(('|{:8s} | '+'{:7.3f} |'*6).format('ALL', VREF_LSB_mv_mean, VREF_LSB_mv_std, VREF_LSB_mv_rms, IREF_LSB_mv_mean, IREF_LSB_mv_std, IREF_LSB_mv_rms ))
		print(('|{:8s} | '+'{:7.3f} |'*6).format('ALL', VREF_MIN_mv_mean, VREF_MIN_mv_std, VREF_MIN_mv_rms, VREF_MAX_mv_mean, VREF_MAX_mv_std, VREF_MAX_mv_rms ))

	#####################################################################################################
	def calibrate(self, refvoltage=0.825, calib_point=0.8):
		self.ssa.analog.set_output_mux('highimpedence')
		self.ssa.analog.adc_measure_ext_pad(nsamples=1)
		self.bias.SetMode('Keithley_Sourcemeter_2410_GPIB')
		self.bias.multimeter.config__voltage_measure(range=1)
		sign=9;prevsign=9; time.sleep(0.1);
		while((sign+prevsign)!=0):
			prevval = value
			prevsetting, value = self.bias.get_value_and_voltage('ADC_VREF')
			prevsign = sign
			if(value < refvoltage):
				newsetting = prevsetting+1; sign=1
			else:
				newsetting = prevsetting-1; sign=-1
			self.ssa.analog.adc_set_referenence(newsetting)
		if( np.abs(prevval-refvoltage) >  np.abs(value-refvoltage) ):
			self.ssa.analog.adc_set_referenence(prevsetting)
		setting, value = self.bias.get_value_and_voltage('ADC_VREF')
		utils.print_info('->  VREF set to {:2d} [{:7.3f} mV]'.format(setting, value*1E3))
		#
		#
		#self.ssa.analog.set_output_mux('highimpedence')
		#self.ssa.analog.adc_measure_ext_pad(nsamples=1)
		#self.bias.multimeter.config__voltage_source(compliance=10E-3, range=1)
		#self.bias.multimeter.set_voltage(refvoltage*calib_point)
		#expected = (2**12-1)*calib_point
		#time.sleep(0.001)
		#r = self.ssa.analog.adc_measure_ext_pad(nsamples=10)
		#sign=9;prevsign=9;  time.sleep(0.1);
		#setting, tmp = self.bias.get_value_and_voltage('ADC_VREF')
		##setting=15;
		##self.ssa.analog.adc_set_trimming(setting)
		#
		#value = self.ssa.analog.adc_measure_ext_pad(nsamples=100)
		#while((sign+prevsign)!=0):
		#	prevval = value
		#	prevsetting = setting
		#	value = self.ssa.analog.adc_measure_ext_pad(nsamples=100)
		#	prevsign = sign
		#	if(value < expected):
		#		setting = prevsetting-1; sign=1
		#	else:
		#		setting = prevsetting+1; sign=-1
		#	#if(setting<0 or setting>63): break
		#	print([prevsetting, value])
		#	#self.ssa.analog.adc_set_trimming(setting)
		#	self.ssa.analog.adc_set_referenence(setting)
		#
		#
		#if( np.abs(prevval-expected) >  np.abs(value-refvoltage) ):
		#	self.ssa.analog.adc_set_referenence(prevsetting)


	#########################################################################
	## quick and dirty test
	def manual_measure(self):
		result={}
		for vin in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
			utils.print_log("set input voltage to {:5.3f}".format(vin))
			time.sleep(3)
			result[vin] = ssa.chip.analog.adc_measure('TESTPAD', nsamples=100)
			utils.print_log('-------------------------------------------------')
		return result

	#########################################################################
	## quick and dirty test
	def manual_measure_plot(self):
		data = {}
		plt.clf()
		fig = plt.figure(figsize=(8,6))
		data['0']  = {0.0: 22.44, 0.1: 646.34, 0.2: 1306.04, 0.3: 1979.96, 0.4: 2647.79, 0.5: 3305.76, 0.6: 3969.82, 0.7: 4095.00, 0.8: 4095.0}
		data['7']  = {0.0: 11.07, 0.1: 600.59, 0.2: 1229.38, 0.3: 1854.88, 0.4: 2474.18, 0.5: 3105.9,  0.6: 3721.64, 0.7: 4093.68, 0.8: 4095.0}
		data['15'] = {0.0: 11.23, 0.1: 566.62, 0.2: 1143.58, 0.3: 1729.33, 0.4: 2310.25, 0.5: 2891.36, 0.6: 3471.86, 0.7: 4006.68, 0.8: 4095.0}
		data['23'] = {0.0: 11.13, 0.1: 531.79, 0.2: 1067.91, 0.3: 1608.77, 0.4: 2159.76, 0.5: 2706.12, 0.6: 3250.75, 0.7: 3789.76, 0.8: 4094.33}
		data['31'] = {0.0: 14.57, 0.1: 498.44, 0.2: 1007.13, 0.3: 1519.30, 0.4: 2028.33, 0.5: 2532.94, 0.6: 3053.69, 0.7: 3558.16, 0.8: 4060.9}
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(True)
		ax.spines["right"].set_visible(True)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(list(np.arange(0,0.9,0.1)), fontsize=16)
		plt.yticks(list(range(0,2**12+1,2**8)), fontsize=16)
		plt.xlabel('Input voltage [V]', fontsize=16)
		plt.ylabel('Converted code', fontsize=16)
		color=iter(sns.color_palette('deep'))
		for v in data:
			x = list(data[v].keys())
			y = list(data[v].values())
			c = next(color);
			xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
			if(v in ['31', '23']):
				helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y), bc_type=([(2, 0.0)], [(2, 0.0)]))
			else:
				helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y), bc_type=([(3, 0.0)], [(1, 0.0)]))
			y_smuth = helper_y3(xnew)
			y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 1001, polyorder = 1)
			plt.plot(xnew, y_smuth, lw=1, alpha = 0.5, color=c)
			#plt.plot(xnew, y_hat, color=c, lw=1, alpha = 0.8)
			plt.plot(x, y, 'x', label= "DAC = {:s}".format(v), color=c)
			leg = ax.legend(fontsize = 14, loc=('lower right'), frameon=True )
			leg.get_frame().set_linewidth(1.0)
			ax.get_xaxis().tick_bottom()
			ax.get_yaxis().tick_left()
		plt.show()

	###########################################################
	def dac_linearity(self, name = 'Bias_THDAC', nbits = 8, eval_inl_dnl = True, npoints = 10, average=10, filename = 'temp/temp', plot = True, filemode = 'w', runname = '', return_raw=False):
		utils.activate_I2C_chip(self.fc7)
		if(self.bias == False): return False, False
		if(not (name in self.muxmap)): return False, False
		if(isinstance(filename, str)):
			fo = "../SSA_Results/" + filename
		print(fo)
		if(eval_inl_dnl):
			nlin_params, nlin_data, fit_params, raw = self.bias.measure_dac_linearity(
				name = name, nbits = nbits,	filename = fo,	filename2 = "",
				plot = False, average = 1, runname = runname, filemode = filemode)
			g, ofs, sigma = fit_params
			DNL, INL = nlin_data
			DNLMAX, INLMAX = nlin_params
			x, data = raw
		else:
			g, ofs, raw = self.bias.measure_dac_gain_offset(name = name, nbits = nbits, npoints = npoints)
			x, data = raw
		if name == 'Bias_THDAC':
			baseline = self.bias.get_voltage('Bias_BOOSTERBASELINE')
			data = (0 - np.array(data)) + baseline
		elif name in self.muxmap:
			data = np.array(data)
			baseline = 0
		else:
			return False
		if plot:
			plt.clf()
			plt.figure(1)
			#plt.plot(x, f_line(x, ideal_gain/1000, ideal_offset/1000), '-b', linewidth=5, alpha = 0.5)
			plt.plot(x, data, '-r', linewidth=5,  alpha = 0.5)
			if(eval_inl_dnl):
				plt.figure(2); plt.ylim(-1, 1); plt.bar( x, DNL, color='b', edgecolor = 'b', align='center')
				plt.figure(3); plt.ylim(-1, 1); plt.bar( x, INL, color='r', edgecolor = 'r', align='center')
				plt.figure(4); plt.ylim(-1, 1); plt.plot(x, INL, color='r')
			plt.show()
		#return DNL, INL, x, data
		if(eval_inl_dnl):
			if(return_raw): return [DNLMAX, INLMAX, g, ofs, raw]
			else:           return [DNLMAX, INLMAX, g, ofs]
		else:
			if(return_raw): return [g*1E3, ofs*1E3, baseline*1E3, raw]
			else:           return [g*1E3, ofs*1E3, baseline*1E3]
