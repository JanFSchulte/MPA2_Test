import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import copy
import seaborn as sns
from random import randint

from utilities.tbsettings import *
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *


class ssa_ctrl_analog:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map;
		self.analog_mux_map = analog_mux_map;
		self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
		self.dll_chargepump = 0b00;
		self.bias_dl_enable = False
		self.seu_check_time = -1
		self.testpad_is_enable = -1
		self.seu_cntr = { 'A':{'peri':[0]*2, 'strip':[0]*8, 'all':0}, 'S':{'peri':[0]*2, 'strip':[0]*8, 'all':0} }

	#####################################################################
	def set_output_mux(self, testline = 'highimpedence'):
		if(tbconfig.VERSION['SSA'] >= 2):
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write(    register="ADC_trimming", field='TestPad_Enable',        data=0b1)
			self.I2C.peri_write(    register="ADC_control",  field='ADC_control_input_sel', data=ctrl)
			r = self.I2C.peri_read( register="ADC_control",  field='ADC_control_input_sel')
		else:
			#utils.activate_I2C_chip(self.fc7)
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write('Bias_TEST_LSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_MSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
			self.I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
			r = ((self.I2C.peri_read('Bias_TEST_LSB') & 0xff))
			r = ((self.I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			utils.print_error("Error. Failed to set the MUX")
			return False
		else:
			return True

	#####################################################################
	def adc_measure(self, testline = 'highimpedence', testpad_enable=False, nsamples=1, fast=True):
		r1 = []
		# default: self.testpad_is_enable = -1
		if(testpad_enable or (testline=='TESTPAD')):
			if(self.testpad_is_enable!=1): #to speedup
				self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable', data=0b1 )
				self.testpad_is_enable = 1
		else:
			if(self.testpad_is_enable!=0): #to speedup
				self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable', data=0b0)
				self.testpad_is_enable = 0
		for i in range(nsamples):
			r1.append( self._adc_measure(testline=testline, fast=fast) )
		if(nsamples>1):
			r = np.sum(r1) / float(nsamples)
		else:
			r = r1[0]
		return r

	#####################################################################
	def _adc_measure(self, testline = 'highimpedence', fast=True):
		#start=time.time()
		input_sel = self.analog_mux_map[testline]
		if(fast):
			r =    self.I2C.peri_write( register="ADC_control", field=False, data=(0b11100000 | (input_sel & 0b00011111)) )
			r = r| self.I2C.peri_write( register="ADC_control", field=False, data=(0b11000000 | (input_sel & 0b00011111)) )
		else:
			r =    self.I2C.peri_write( register="ADC_control", field=False                     , data=0x00)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_reset'       , data=0b1)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_reset'       , data=0b0)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_input_sel'   , data=input_sel)
			r = r| self.I2C.peri_write( register="ADC_control", field='ADC_control_enable_start', data=0b11)
		if(not r):
			utils.print_error("Error. Failed to use the ADC")
			return False
		time.sleep(0.001)
		msb = self.I2C.peri_read( register="ADC_out_H", field=False )
		lsb = self.I2C.peri_read( register="ADC_out_L", field=False )
		#print('{:8.3f} ms'.format(1E3*(time.time()-start))); start=time.time()
		if((msb==None) or (lsb==None) or (msb=='Null') or (lsb=='Null') ):
			utils.activate_I2C_chip(self.fc7)
			msb = self.I2C.peri_read( register="ADC_out_H", field=False )
			lsb = self.I2C.peri_read( register="ADC_out_L", field=False )
		if((msb==None) or (lsb==None) or (msb=='Null') or (lsb=='Null') ):
			return False
		res = ((msb<<8) | lsb)
		return res


	#####################################################################
	def adc_set_trimming(self, value):
		r = self.I2C.peri_write( register="ADC_trimming", field='TestPad_Enable',        data=0b1 )
		r = self.I2C.peri_write( register="ADC_trimming", field='ADC_trimming_trim_sel', data=0b1 )
		r = self.I2C.peri_write( register="ADC_trimming", field='ADC_trimming_trim_val', data=value )
		r = self.I2C.peri_read(  register="ADC_trimming", field='ADC_trimming_trim_val' )
		return r

	#####################################################################
	def adc_get_trimming(self):
		r = self.I2C.peri_read(  register="ADC_trimming", field='ADC_trimming_trim_val' )
		return r

	#####################################################################
	def adc_measure_temperature(self, nsamples=10):
		return self.adc_measure('Temperature', nsamples=nsamples)

	#####################################################################
	def adc_measure_THDAC(self, nsamples=10):
		r1 = self.adc_measure('Bias_THDAC', nsamples=nsamples)
		r2 = self.adc_measure('Bias_THDACHIGH', nsamples=nsamples)
		return [r1, r2]

	#####################################################################
	def adc_measure_CALDAC(self, nsamples=10):
		return self.adc_measure('Bias_CALDAC', nsamples=nsamples)

	#####################################################################
	def adc_measure_supply(self, nsamples=1, raw = True, display=True):
		r = np.zeros(6)
		r[0] = self.adc_measure('DVDD', nsamples=nsamples)
		r[1] = self.adc_measure('AVDD', nsamples=nsamples)
		r[2] = self.adc_measure('PVDD', nsamples=nsamples)
		r[3] = self.adc_measure('GND',  nsamples=nsamples)
		r[4] = self.adc_measure('VBG',  nsamples=nsamples)
		r[5] = self.adc_measure('Temperature',  nsamples=nsamples)
		if(not raw):
			r = [r[0]/(2**11), r[1]/(2**11), r[2]/(2**11), r[3], r[4], r[5]]   # 12 bit ADC e partitore 1/2
		if(display):
			utils.print_log('->  ADC measure - DVDD    : {:5d}'.format(int(r[0])))
			utils.print_log('->  ADC measure - AVDD    : {:5d}'.format(int(r[1])))
			utils.print_log('->  ADC measure - PVDD    : {:5d}'.format(int(r[2])))
			utils.print_log('->  ADC measure - GND     : {:5d}'.format(int(r[3])))
			utils.print_log('->  ADC measure - VBG     : {:5d}'.format(int(r[4])))
			utils.print_log('->  ADC measure - Temp    : {:5d}'.format(int(r[5])))
		return r

	#####################################################################
	def adc_measure_ext_pad(self, nsamples=10):
		#start = time.time()
		rp = self.adc_measure(testline='TESTPAD', testpad_enable=True, nsamples=nsamples, fast=True)
		#utils.print_log('{:8.3f} ms'.format(1E3*(time.time()-start)))
		return rp

	#####################################################################
	def adc_sample_histogram(self, runtime=3600, freq=0.1, show=1, filename='../SSA_Results/adc_measures/ADC_samples.csv', continue_on_same_file=0):
		if(continue_on_same_file):
			adchist = CSV.csv_to_array(filename=filename)[:,1]
		else:
			adchist = np.zeros(2**13, dtype=int)
		cnt  = 0; told = 0; wd = 0
		self.adc_measure_ext_pad()
		runtime = round(float(runtime)*freq)/freq #to have n copleate cycles
		#ret = self.WVF.SetWaveform(func='ramp', freq=freq, offset=-0.1, vpp=1.1)
		#if ret is False: return False
		if(filename == False):
			filename = '../SSA_Results/ADC_samples_'+str(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')+'.csv')
		timestart = time.time()
		while ((time.time()-timestart) < runtime):
			wd = 0
			while(wd < 3):
				try:
					res = int(np.round(self.adc_measure_ext_pad(nsamples=1)))
					utils.print_inline('{:8d}'.format(res) )
					time.sleep( randint(0,3)*0.0005 )
					break
				except:
					wd +=1;
					utils.print_warning('Exception {:d}'.format(wd))
			if res is False: return False
			else: adchist[int(res)]+=1
			cnt+=1
			tcur = time.time()
			if ((tcur-told)>1): #update histogram every second
				told = tcur
				utils.print_inline('{:8d} ->  ADC collected {:d} samples'.format(res, cnt))
				#with open(filename, 'w') as fo:
				#	fo.write('{:8d},\n'.format(res))
				CSV.array_to_csv(adchist, filename=filename)
		f.close()
		utils.print_log('->  ADC total number of samples taken is '+str(cnt))
		dnlh, inlh = self.adc_dnl_inl_histogram(filename=filename)
		return dnlh, inlh, adchist

	#####################################################################
	def adc_dnl_inl_histogram(self, minc=3, maxc=4092, filename='../SSA_Results/adc_measures/ADC_samples.csv'):
		dnlh = np.zeros(4096)
		inlh = np.zeros(4096)
		maxim = 0; inl=0.0;
		adchist = CSV.csv_to_array(filename)[:,1]
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
		fig = plt.figure(1, figsize=(18,12))
		c = next(color);
		plt.plot(range(minc,maxc,1), adchist[minc:maxc], 'x', color=c)
		fig = plt.figure(2, figsize=(18,12))
		c = next(color);
		plt.plot(range(minc,maxc,1), dnlh[minc:maxc], 'x', color=c)
		fig = plt.figure(3, figsize=(18,12))
		c = next(color);
		plt.plot(range(minc,maxc,1), inlh[minc:maxc], 'x', color=c)
		plt.show()
		return dnlh, inlh
		#adc_dnl_inl_histogram()

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



	## quick and dirty test
	def adc_manual_measure(self):
		result={}
		for vin in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
			utils.print_log("set input voltage to {:5.3f}".format(vin))
			time.sleep(3)
			result[vin] = ssa.chip.analog.adc_measure('TESTPAD', nsamples=100)
			utils.print_log('-------------------------------------------------')
		return result

	## quick and dirty test
	def adc_manual_measure_plot(self):
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



# ssa_peri_reg_map['Fuse_Mode']              = 43
# ssa_peri_reg_map['Fuse_Prog_b0']           = 44
# ssa_peri_reg_map['Fuse_Prog_b1']           = 45
# ssa_peri_reg_map['Fuse_Prog_b2']           = 46
# ssa_peri_reg_map['Fuse_Prog_b3']           = 47
# ssa_peri_reg_map['Fuse_Value_b0']          = 48
# ssa_peri_reg_map['Fuse_Value_b1']          = 49
# ssa_peri_reg_map['Fuse_Value_b2']          = 50
# ssa_peri_reg_map['Fuse_Value_b3']          = 51
