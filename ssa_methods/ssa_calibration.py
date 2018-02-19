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
	def __init__(self, ssa, I2C, fc7, multimeter):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7
		self.multimeter = multimeter
		
	def d5_value(self, name, mode = 'r', value = -1):
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
			
	def get_value_and_voltage(self, name, inst0 = -1):
		# get instrument
		if (inst0 == -1):
			inst = self.multimeter.init_keithley()
		else:
			inst = inst0
		# demux the line
		self.set_measurement(name)
		# read value
		value = self.d5_value('Bias_'+str(name), 'r')
		measurement = self.multimeter.measure(inst)
		# return	
		return value, measurement

	def tune_parameter(self, inst, name, nominal):
		if (nominal == -1):
			return

		# check initials
		dac_value, voltage = self.get_value_and_voltage(name, inst)
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
			self.d5_value('Bias_'+str(name), 'w', dac_value)
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
		self.d5_value('Bias_'+str(name), 'w', best_dac_value)
		dac_value, voltage = self.get_value_and_voltage(name, inst)
		print "\t\tBest Set: ", dac_value, 1E3*voltage

		return best_dac_value

	def check_nominals(self):
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
			Parameter("Booster Feedback Bias", "D5BFEED", 82.0), 
			Parameter("Preamplifier Bias", "D5PREAMP", 82.0), 
			Parameter("TRIM DAC range", "D5TDR", 115.0), 
			Parameter("DAC for voltage biases","D5ALLV", 82.0), 
			Parameter("DAC for current biases","D5ALLI", 82.0), 
			Parameter("DAC for threshold and calibration", "D5DAC8", 86.0)]
			#Parameter("Threshold DAC", "THDAC", 622.0), 
			#Parameter("Threshold High DAC", "THDACHIGH", 622.0), 
			#Parameter("Calibration DAC", "CALDAC", 100.0)]

		# iterate and measure
		for par in par_list:
			value, voltage = self.get_value_and_voltage(par.par_name, inst)
			voltage = voltage*1E3
			print par.full_name, ": "
			print "\tCheck the initial value: "
			print ("\t\t DAC: %4d\t V: %8.3f mV") % (value, voltage)
			print "\tTune the value (", par.nominal, "):"
			best_dac = self.tune_parameter(inst, par.par_name, par.nominal)
			par.best_dac = best_dac

		print "\n\nSummary of tuning (tuned values):"
		for par in par_list:
			value, voltage = self.get_value_and_voltage(par.par_name, inst)
			voltage = voltage*1E3
			print par.full_name, ": "
			print ("\t Best DAC: %4d,\t V: %8.3f mV") % (value, voltage)
			

	def measure_vth_linearity(self):
		inst = self.multimeter.init_keithley(3)
		activate_I2C_chip()
		
		# demux the line
		self.I2C.peri_write("Bias_TEST_LSB", 0b10000000)
		self.I2C.peri_write("Bias_TEST_MSB", 0)	
		
		#array
		data = np.zeros(256, dtype=np.float);

		# do the measurement
		for i in range(0, 256):
			#set_threshold(i)
			self.I2C.peri_write("Bias_THDAC", i)
			sleep(0.1)
			data[i] = self.multimeter.measure(inst)
			if (i % 10 == 0):
				print "Done point ", i, " of ", 256

		return data


	def measure_booster_linearity(self):
		inst = init_keithley(3)
		activate_I2C_chip()
		
		# demux the line
		self.set_measurement("D5BFEED")	
		
		#array
		data = np.zeros(32, dtype=np.float);

		# do the measurement
		for i in range(0, 32):
			#set_threshold(i)
			self.I2C.peri_write("Bias_D5BFEED", i)
			sleep(0.1)
			data[i] = self.multimeter.measure(inst)
			print "Done point ", i, " of ", 32

		return data

	def set_measurement(self, name = "none"):
		# set all zeros now
		self.I2C.peri_write("Bias_TEST_LSB", 0)
		self.I2C.peri_write("Bias_TEST_MSB", 0)
		
		# now set whatever you want
		if name == "none":
			pass
		elif name == "D5BFEED":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000001)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "D5PREAMP":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000010)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "D5TDR":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000100)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "D5ALLV":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00001000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "D5ALLI":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00010000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "CALDAC":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00100000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "BOOSTERBASELINE":
			self.I2C.peri_write("Bias_TEST_LSB", 0b01000000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "THDAC":
			self.I2C.peri_write("Bias_TEST_LSB", 0b10000000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000000)
		elif name == "THDACHIGH":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000001)
		elif name == "D5DAC8":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000010)
		elif name == "VBG":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00000100)
		elif name == "GND":
			self.I2C.peri_write("Bias_TEST_LSB", 0b00000000)
			self.I2C.peri_write("Bias_TEST_MSB", 0b00001000)
		else:
			print "Error. Wrong name"