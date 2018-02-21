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

	def __init__(self, ssa, I2C, fc7, multimeter, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7
		self.multimeter = multimeter
		self.ssa_peri_reg_map = ssa_peri_reg_map
		self.ssa_strip_reg_map = ssa_strip_reg_map
		self.analog_mux_map = analog_mux_map


	def measure_dac_linearity(self, name, nbits, filename = False, filename2 = "", plot = True):
		if(not name in self.analog_mux_map):
			print "->  \tInvalid DAC name"
			return False
		fullscale = 2**nbits
		inst = self.multimeter.init_keithley(3)
		self.ssa.ctrl.set_output_mux(name)	
		data = np.zeros(fullscale, dtype=np.float);

		for i in range(0, fullscale):
			self.I2C.peri_write(name, i)
			sleep(0.1)
			data[i] = self.multimeter.measure(inst)
			utils.ShowPercent(i, fullscale-1, "Measuring "+name+" linearity                         ")
		
		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "_Linearity_" + name + filename2
			CSV.ArrayToCSV (array = data, filename = fo + ".csv", transpose = True)
		
		inl = self.__dac_inl(data = data, nbits = nbits, plot = False)
		inl_max = np.max(np.abs(inl))

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
			if( isinstance(filename, str) ):
				plt.savefig(fo+".pdf")
			else:
				plt.show()

		g, ofs, sigma = utils.linear_fit(range(0,2**nbits), data)
		
		return g, ofs, sigma/g, inl_max
	

	def calibrate_to_nominals(self):
		# init keithley
		inst = self.multimeter.init_keithley()
		# for simplicity define a par class
		class Parameter:
			def __init__(self, full_name, par_name, nominal = -1, best_dac = -1):
				self.full_name = full_name
				self.par_name = par_name
				self.nominal = nominal
				self.best_dac = best_dac
		# define the pars
		par_list = [
			Parameter("Booster Feedback Bias", "Bias_D5BFEED", 82.0), 
			Parameter("Preamplifier Bias", "Bias_D5PREAMP", 82.0), 
			Parameter("TRIM DAC range", "Bias_D5TDR", 115.0), 
			Parameter("DAC for voltage biases","Bias_D5ALLV", 82.0), 
			Parameter("DAC for current biases","Bias_D5ALLI", 82.0), 
			Parameter("DAC for threshold and calibration", "Bias_D5DAC8", 86.0)]
			#Parameter("Threshold DAC", "THDAC", 622.0), 
			#Parameter("Threshold High DAC", "THDACHIGH", 622.0), 
			#Parameter("Calibration DAC", "CALDAC", 100.0)]

		# iterate and measure
		for par in par_list:
			value, voltage = self.__get_value_and_voltage(par.par_name, inst)
			voltage = voltage*1E3
			print par.full_name, ": "
			print "\tCheck the initial value: "
			print ("\t\t DAC: %4d\t V: %8.3f mV") % (value, voltage)
			print "\tTune the value (", par.nominal, "):"
			best_dac = self.__tune_parameter(inst, par.par_name, par.nominal)
			par.best_dac = best_dac

		print "\n\nSummary of tuning (tuned values):"
		for par in par_list:
			value, voltage = self.__get_value_and_voltage(par.par_name, inst)
			voltage = voltage*1E3
			print par.full_name, ": "
			print ("\t Best DAC: %4d,\t V: %8.3f mV") % (value, voltage)
		

	def __dac_inl(self, data, nbits, plot = True):
		fullscale = 2**nbits
		INL = np.zeros(fullscale, dtype=np.float)
		m = float(data[fullscale-1] - data[0]) / (fullscale-1)
		for i in range(0, fullscale):
			INL[i] = (( data[i]-data[0] )/m)-float(i)
		if(plot):
			plt.clf()
			plt.ylim([-2,2])
			plt.plot(range(0,fullscale), INL, '-o')
			plt.plot(range(0,fullscale), [1]*fullscale, 'r')
			plt.plot(range(0,fullscale),[-1]*fullscale, 'r')
			plt.show()
		return INL

		
	def __d5_value(self, name, mode = 'r', value = -1):
		# check the read value
		if ((mode == 'w') & (value == -1)):
			print "Error! Can not use default value for writing. Please set the value"
			exit(1)        
		# write now	
		if (mode == 'w'):
			self.I2C.peri_write(name, value)
		# read back
		read_value = self.I2C.peri_read(name)
		# if it was write - check the result
		if (mode == 'w'):
			if (value != read_value):
				print "Error! The write was not succesfull"
				return -1
			else:
				return 0
		elif (mode == 'r'):
			return read_value
		else:
			return -1
			

	def __get_value_and_voltage(self, name, inst0 = -1):
		# get instrument
		if (inst0 == -1):
			inst = self.multimeter.init_keithley()
		else:
			inst = inst0
		# demux the line
		self.ssa.ctrl.set_output_mux(name)
		# read value
		value = self.__d5_value(str(name), 'r')
		measurement = self.multimeter.measure(inst)
		# return	
		return value, measurement


	def __tune_parameter(self, inst, name, nominal):
		if (nominal == -1):
			return

		# check initials
		dac_value, voltage = self.__get_value_and_voltage(name, inst)
		voltage = voltage*1E3
		print "\t\tInitial Set: ", dac_value, voltage
		# best values
		best_dac_value = dac_value
		best_voltage_diff = abs(voltage-nominal)
		# sign changed 
		start_value = dac_value
		sign_changed = False
		if(dac_value == 0):
			sign = 1
		else:
			sign = -1
		# prev value
		prev_voltage_diff = abs(voltage-nominal)
		while(True):
			# set new value
			dac_value = dac_value + sign
			self.__d5_value(str(name), 'w', dac_value)
			# measure
			voltage = 1E3*self.multimeter.measure(inst)
			print "\t\t\tdac: ", dac_value, " voltage: ", voltage
			# compare
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
						#print "tuning done"
						# then done
						break
				else:
					# it is ok we are moving in the good direction
					pass
			# update the voltage diff
			prev_voltage_diff = current_voltage_diff
		
		# verify the value
		self.__d5_value(str(name), 'w', best_dac_value)
		dac_value, voltage = self.__get_value_and_voltage(name, inst)
		print "\t\tBest Set: ", dac_value, 1E3*voltage

		return best_dac_value



