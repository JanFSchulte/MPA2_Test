from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from myScripts.BasicMultimeter import *

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class ssa_calibration():

	class Parameter():
		def __init__(self, full_name, par_name, nominal = -1, best_dac = -1, curr_value = -1, docalibrate = 'set_dont_calibrate'):
			self.full_name = full_name
			self.par_name = par_name
			self.nominal = nominal
			self.best_dac = best_dac
			self.curr_value = curr_value
			self.docalibrate = docalibrate

	def __init__(self, ssa, I2C, fc7, multimeter, pcbadc, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa = ssa;  self.I2C = I2C;  self.fc7 = fc7;
		self.pcbadc = pcbadc;  self.multimeter = multimeter;
		self.ssa_peri_reg_map = ssa_peri_reg_map;  self.ssa_strip_reg_map = ssa_strip_reg_map;
		self.analog_mux_map = analog_mux_map;  self.initialised = False; self.minst = 0;
		self.SetMode('MULTIMETER');
		self.set_gpib_address(16);
		self.par_list = [
			self.Parameter("Analog Ground Interal ", "GND",                   0.0, -1, -1, 'set_dont_calibrate'),
			self.Parameter("Bandgap Voltage       ", "VBG",                   0.3, -1, -1, 'set_dont_calibrate'),
			self.Parameter("Bandgap Voltage       ", "Bias_BOOSTERBASELINE",  0.6, -1, -1, 'set_dont_calibrate'),
			self.Parameter("Booster Feedback Bias ", "Bias_D5BFEED",         82.0, -1, -1, 'set_calibrate'),
			self.Parameter("Preamplifier Bias     ", "Bias_D5PREAMP",        82.0, -1, -1, 'set_calibrate'),
			self.Parameter("TRIM DAC range        ", "Bias_D5TDR",          115.0, -1, -1, 'set_calibrate'),
			self.Parameter("DAC for voltage biases", "Bias_D5ALLV",          82.0, -1, -1, 'set_calibrate'),
			self.Parameter("DAC for current biases", "Bias_D5ALLI",          82.0, -1, -1, 'set_calibrate'),
			self.Parameter("DAC for th and cal    ", "Bias_D5DAC8",          86.0, -1, -1, 'set_calibrate'),
			self.Parameter("Threshold Low DAC     ", "Bias_THDAC",          622.0, -1, -1, 'set_dont_calibrate'),
			self.Parameter("Threshold High DAC    ", "Bias_THDACHIGH",      622.0, -1, -1, 'set_dont_calibrate'),
			self.Parameter("Calibration DAC       ", "Bias_CALDAC",         100.0, -1, -1, 'set_dont_calibrate')]

	def SetMode(self, mode = 'ADC'):
		''' Modes:  'ADC' or 'MULTIMETER' '''
		self.mode = mode

	def set_gpib_address(self, address):
		self.gpib_address = address

	def __initialise(self):
		self.minst = self.multimeter.init_keithley(address = self.gpib_address, avg = 0)
		self.initialised = True


	def calibrate_to_nominals(self):
		if(not self.initialised and (self.mode == 'MULTIMETER')):
			self.__initialise()
		for par in self.par_list:
			if(par.docalibrate == 'set_calibrate'):
				value, voltage = self.get_value_and_voltage(par.par_name, self.minst)
				voltage = voltage*1E3
				print par.full_name, ": "
				print "\tCheck the initial value: "
				print ("\t\t DAC: %4d\t V: %8.3f mV") % (value, voltage)
				print "\tTune the value (", par.nominal, "):"
				best_dac = self.__tune_parameter(self.minst, par.par_name, par.nominal)
				par.best_dac = best_dac
		print "\n\nSummary of tuning (tuned values):"
		self.measure_bias()
		self.ssa.ctrl.set_output_mux('highimpedence')


	def measure_bias(self, return_data = False):
		if(not self.initialised and (self.mode == 'MULTIMETER')):
			self.__initialise()
		for par in self.par_list:
			value, voltage = self.get_value_and_voltage(par.par_name, self.minst)
			voltage = voltage*1E3
			print "->  \t" + par.full_name + ": " + (" [%3d] %7.3f mV") % (value, voltage)
			par.curr_value = voltage
		self.ssa.ctrl.set_output_mux('highimpedence')
		if return_data:
			data = []
			for par in self.par_list:
				data.append( [par.par_name,  par.curr_value] )
			return data


	def measure_dac_linearity(self, name, nbits, filename = False, filename2 = "", plot = True, average = 5, runname = '', filemode = 'w'):
		# ['Bias_D5BFEED'] ['Bias_D5PREAMP']['Bias_D5TDR']['Bias_D5ALLV']['Bias_D5ALLI']
		# ['Bias_CALDAC']['Bias_BOOSTERBASELINE']['Bias_THDAC']['Bias_THDACHIGH']['Bias_D5DAC8']
		if(not self.initialised and (self.mode == 'MULTIMETER')):
			self.__initialise()
		if(not name in self.analog_mux_map):
			print "->  \tInvalid DAC name"
			return False
		fullscale = 2**nbits
		#if(not self.initialised):
		#	self.__initialise()
		self.ssa.ctrl.set_output_mux(name)
		data = np.zeros(fullscale, dtype=np.float);
		for i in range(0, fullscale):
			self.I2C.peri_write(name, i)
			sleep(0.1)
			if(self.mode == 'MULTIMETER'):
				data[i] = self.multimeter.measure(self.minst)
			else:
				data[i] = self.pcbadc.measure('SSA', average)
			utils.ShowPercent(i, fullscale-1, "Measuring "+name+" linearity                         ")
		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "_" + str(runname) + "_Caracteristics_" + name + filename2
			CSV.ArrayToCSV (array = data, filename = fo + ".csv", transpose = True)
		dnl, inl = self._dac_dnl_inl(data = data, nbits = nbits, plot = False)
		inl_max = np.max(np.abs(inl))
		dnl_max = np.max(np.abs(dnl))
		g, ofs, sigma = utils.linear_fit(range(0,2**nbits), data)
		self.ssa.ctrl.set_output_mux('highimpedence')
		print ""
		print "DAC "+name+'['+str(nbits)+'-bit]:'
		print "->       GAIN = %6.3f mV/cnt" % (g*1000.0)
		print "->     OFFSET = %6.3f mV"     % (ofs*1000.0)
		print "->    INL MAX = %6.3f cnts"   % (inl_max)
		print "->    DNL INL = %6.3f cnts"   % (dnl_max)
		print ""
		if(plot):
			plt.clf()
			plt.figure(1)
			plt.subplot(211)
			plt.ylim([-2,2])
			plt.plot(range(0,fullscale), inl, '-')
			plt.plot(range(0,fullscale), [1]*fullscale, 'r')
			plt.plot(range(0,fullscale),[-1]*fullscale, 'r')
			plt.subplot(212)
			plt.plot(range(0,fullscale), data, '-x')
			#if( isinstance(filename, str) ):
			#	plt.savefig(fo+".pdf")
			#else:
			#	plt.show()
		fit_params = [g, ofs, sigma/g]
		raw = [range(0,fullscale), data]
		nlin_data = [dnl, inl]
		nlin_params = dnl_max, inl_max
		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "_" + str(runname) + "_DNL_INL_" + name + filename2 + '.csv'
			CSV.ArrayToCSV (array = np.array([data, dnl, inl]), filename = fo + ".csv", transpose = True)
			fo = open("../SSA_Results/" + filename + "_Parameters_" + name + filename2 + '.csv', filemode)
			fo.write( "\n%s ; %s10.3f ; %s10.3f ; %s10.3f ;" % (runname, g, ofs, sigma) )
			fo.close()
		return  nlin_params, nlin_data, fit_params, raw


	def _dac_dnl_inl(self, data, nbits, plot = True):
		fullscale = 2**nbits
		INL = np.zeros(fullscale, dtype=np.float)
		DNL = np.zeros(fullscale, dtype=np.float)
		LSB = float(data[fullscale-1] - data[0]) / (fullscale-1)
		for i in range(0, fullscale):
			INL[i] = ((data[i]-data[0])/LSB)-float(i)
		for i in range(1, fullscale):
			DNL[i] = ((data[i]-data[i-1])/LSB)-1
		return DNL, INL


	def get_value_and_voltage(self, name, inst0 = -1, average = 1):
		if (inst0 == -1):
			if(not self.initialised and (self.mode == 'MULTIMETER')):
				self.__initialise()
			inst = self.minst
		else: inst = inst0
		self.ssa.ctrl.set_output_mux(name)
		value = self._d5_value(str(name), 'r')
		if(self.mode == 'MULTIMETER'):
			measurement = self.multimeter.measure(inst)
		else:
			measurement = self.pcbadc.measure('SSA', average)
		#self.ssa.ctrl.set_output_mux('highimpedence')
		return value, measurement


	def get_voltage(self, name, inst0 = -1, average = 1):
		if (inst0 == -1):
			if(not self.initialised and (self.mode == 'MULTIMETER')):
				self.__initialise()
			inst = self.minst
		else:
			inst = inst0
		self.ssa.ctrl.set_output_mux(name)
		if(self.mode == 'MULTIMETER'):
			measurement = self.multimeter.measure(inst)
		else:
			measurement = self.pcbadc.measure('SSA', average)
		self.ssa.ctrl.set_output_mux('highimpedence')
		return measurement


	def _d5_value(self, name, mode = 'r', value = -1):
		if ((mode == 'w') & (value == -1)):# check the read value
			print "Error! Can not use default value for writing. Please set the value"
			exit(1)
		if (mode == 'w'):# write now
			self.I2C.peri_write(name, value)
		if(name in self.ssa_peri_reg_map):
			read_value = self.I2C.peri_read(name) # read back
		else:
			return -1
		if (mode == 'w'):# if it was write - check the result
			if (value != read_value):
				print "Error! The write was not succesfull"
				return -1
			else:
				return 0
		elif (mode == 'r'):
			return read_value
		else:
			return -1


	def __tune_parameter(self, inst, name, nominal):
		if (nominal == -1):return
		dac_value, voltage = self.get_value_and_voltage(name, inst)
		voltage = voltage*1E3
		print "\t\t\tdac: ", dac_value, " voltage: ", voltage
		best_dac_value = dac_value
		best_voltage_diff = abs(voltage-nominal)
		start_value = dac_value
		sign_changed = False
		if(dac_value == 0): sign = 1
		else: sign = -1
		# prev value
		prev_voltage_diff = abs(voltage-nominal)
		while(True):
			# set new value
			dac_value = dac_value + sign
			self._d5_value(str(name), 'w', dac_value)
			dac_value, voltage = self.get_value_and_voltage(name, inst)
			voltage *= 1E3
			print "\t\t\tdac: ", dac_value, " voltage: ", voltage
			current_voltage_diff = abs(voltage-nominal)
			if current_voltage_diff < best_voltage_diff:
				best_voltage_diff = current_voltage_diff
				best_dac_value = dac_value
			else:
				# if the diff is worse than previous we should flip the sign, or if already flipped terminate
				if (current_voltage_diff > prev_voltage_diff):
					if (not sign_changed):
						dac_value = start_value
						sign = -1*sign
						if(start_value == 0):
							break
						else:
							sign_changed = True
					else:
						break
				else:
					pass # it is ok we are moving in the good direction
			prev_voltage_diff = current_voltage_diff  # update the voltage diff
		self._d5_value(str(name), 'w', best_dac_value) # verify the value
		dac_value, voltage = self.get_value_and_voltage(name, inst)
		print "\t\tBest Set: ", dac_value, 1E3*voltage
		return best_dac_value
