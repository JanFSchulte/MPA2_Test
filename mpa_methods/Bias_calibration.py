from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.fast_readout_utility import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from myScripts.BasicMultimeter import *
import Gpib

def DAC_linearity(block, point, bit, plot, inst):
	nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
	DAC = nameDAC[point] + str(block)
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)
	data = np.zeros(1 << bit, dtype=np.float)
	for i in range(0, 1 << bit):
		I2C.peri_write(DAC, i)
		data[i] = measure(inst)
		if (i % 10 == 0):
			print "Done point ", i, " of ", 1 << bit
	if plot:
		plt.plot(range(0,1 << bit), data,'o')
		plt.xlabel('DAC voltage [LSB]')
		plt.ylabel('DAC value [mV]')
		plt.show()
	return data

def measure_DAC_testblocks(point, bit, plot = 1,print_file = 0, filename = "../cernbox/MPA_Results/DAC_"):
	inst = init_keithley(3)
	data = np.zeros((7, 1 << bit), dtype=np.float)
	for i in range(0,7):
		data[i] = DAC_linearity(i, point, bit, 0, inst)
		if plot:
			plt.plot(range(0,1 << bit), data[i, :],'o', label = "Test Block #" + str(i))
	if plot:
		plt.xlabel('DAC voltage [LSB]')
		plt.ylabel('DAC value [mV]')
		plt.legend()
		plt.show()
	if print_file:
		CSV.ArrayToCSV (data, str(filename) + "_TP" + str(point) + ".csv")
	return data

def measure_DAC_chip(chip = "Test", plot = 1,print_file = 0, filename = "../cernbox/MPA_Results/ChipDAC_"):
	activate_I2C_chip()
	for i in range(0,7):
		if (i < 5): bit = 5
		else: 		bit = 8
		measure_DAC_testblocks(i, 5, plot = 0,print_file = 1, filename = filename + "_" + chip);

def measure_DAC(block, point):
	data = np.zeros(256, dtype=np.float);
	# do the measurement
	for i in range(0, 256):
		set_threshold(i)
		data[i] = measure(inst)
		if (i % 10 == 0):
			print "Done point ", i, " of ", 256
	return data

def set_DAC(block, point, exp_value):
	activate_I2C_chip()
	inst = init_keithley(3)
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)
	sleep(0.1)
	value = measure(inst)
	nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
	DAC = nameDAC[point] + str(block)
	I2C.peri_write(DAC, value)
