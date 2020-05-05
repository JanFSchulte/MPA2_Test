from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from mpa_methods.mpa_i2c_conf import *
#from mpa_methods.fast_readout_utility import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from myScripts.BasicMultimeter import *
import Gpib

def disable_test():
	activate_I2C_chip(verbose = 0)
	I2C.peri_write('TESTMUX',0b00000000)
	I2C.peri_write('TEST0',0b00000000)
	I2C.peri_write('TEST1',0b00000000)
	I2C.peri_write('TEST2',0b00000000)
	I2C.peri_write('TEST3',0b00000000)
	I2C.peri_write('TEST4',0b00000000)
	I2C.peri_write('TEST5',0b00000000)
	I2C.peri_write('TEST6',0b00000000)


def DAC_linearity(block, point, bit, inst, step = 1, plot = 1):
	nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
	DAC = nameDAC[point] + str(block)
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)
	data = np.zeros(1 << bit, dtype=np.float)
	print "DAC: ", DAC
	for i in range(0, 1 << bit, step):
		I2C.peri_write(DAC, i)
		sleep(0.1)
		data[i] = multimeter.measure(inst)
		if (i % 10 == 0):
			print "Done point ", i, " of ", 1 << bit
	if plot:
		plt.plot(range(0,1 << bit), data,'o')
		plt.xlabel('DAC voltage [LSB]')
		plt.ylabel('DAC value [mV]')
		plt.show()
	return data

def measure_DAC_testblocks(point, bit, step = 1, plot = 1,print_file = 0, filename = "../cernbox/MPA_Results/DAC_"):
	inst = multimeter.init_keithley(3)
	data = np.zeros((7, 1 << bit), dtype=np.float)
	for i in range(0,7):
		data[i] = DAC_linearity(i, point, bit, inst, step, 0)
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

def measure_DAC_chip(chip = "Test", print_file = 1, filename = "../cernbox/MPA_Results/ChipDAC_"):
	activate_I2C_chip(verbose = 0)
	for i in range(0,7):
		if (i < 5): bit = 5
		else: 		bit = 8
		measure_DAC_testblocks(i, bit, plot = 0,print_file = 1, filename = filename + "_" + chip);

def calibrate_bias(point, block, DAC_val, exp_val, inst, gnd_corr):
	nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
	DAC = nameDAC[point] + str(block)
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)
	I2C.peri_write(DAC, 0)
	sleep(0.1)
	off_val = multimeter.measure(inst)
	sleep(0.1)
	I2C.peri_write(DAC, DAC_val)
	sleep(0.1)
	act_val = multimeter.measure(inst)
	LSB = (act_val - off_val) / DAC_val
	DAC_new_val = DAC_val- int(round((act_val - exp_val - gnd_corr)/LSB))
	if DAC_new_val < 0:
		DAC_new_val = 0
	elif DAC_new_val > 31:
		DAC_new_val = 31
	I2C.peri_write(DAC, DAC_new_val)
	new_val = multimeter.measure(inst)
	if (new_val - gnd_corr < exp_val + exp_val*0.05 )&(new_val - gnd_corr > exp_val - exp_val*0.05):
	#if (new_val - gnd_corr < exp_val + exp_val*0.02 )&(new_val - gnd_corr > exp_val - exp_val*0.02):
		i = 1
		print "Calibration bias point ", point, "of test point", block, "--> Done (", new_val, "V for ", DAC_new_val, " DAC)"
	else:
		print "Calibration bias point ", point, "of test point", block, "--> Failed (", new_val, "V for ", DAC_new_val, " DAC)"
	return DAC_new_val

#def measure_gnd():
#	inst = multimeter.init_keithley(3)
#	disable_test()
#	data = np.zeros((7, ), dtype=np.float)
#	for block in range(0,7):
#		test = "TEST" + str(block)
#		I2C.peri_write('TESTMUX',0b00000001 << block)
#		I2C.peri_write(test, 0b10000000)
#		data[block] = multimeter.measure(inst)
#	disable_test()
#	print data
#	return np.mean(data)

def measure_gnd():
	inst = multimeter.init_keithley(3)
	activate_I2C_chip(verbose = 0)
	sleep(1)
	disable_test()
	data = np.zeros((7, ), dtype=np.float)
	for block in range(0,7):
		test = "TEST" + str(block)
		I2C.peri_write('TESTMUX',0b00000001 << block)
		I2C.peri_write(test, 0b10000000)
		sleep(1)
		data[block] = multimeter.measure(inst)
	disable_test()
	print data
	return np.mean(data)

def measure_bg():
	inst = multimeter.init_keithley(3)
	activate_I2C_chip(verbose = 0)
	sleep(1)
	disable_test()
	I2C.peri_write('TESTMUX',0b10000000)
	sleep(1)
	data = multimeter.measure(inst)
	disable_test()
	print data
	return data

def calibrate_chip(gnd_corr, print_file = 1, filename = "test"):
	activate_I2C_chip(verbose = 0)
	inst = multimeter.init_keithley(avg = 10)
	DAC_val = [15, 15, 15, 15, 15]
	exp_val = [0.082, 0.082, 0.108, 0.082, 0.082]
	data = np.zeros((5, 7), dtype = np.int16 )
	for point in range(0,5):
		calrowval = []
		for block in range(0,7):
			data[point, block] = calibrate_bias(point, block, DAC_val[point], exp_val[point], inst, gnd_corr)
	disable_test()
	print "Got all Calib B. Points"
	if print_file:
		CSV.ArrayToCSV (data, str(filename) + ".csv")
	print "Saved!"
	return data

def trimDAC_amplitude(value):
	activate_I2C_chip(verbose = 0)
	for block in range(0,7):
		#curr = I2C.peri_read("C"+str(block))
		#new_value = curr + value
		I2C.peri_write("C"+str(block), value)
	trm_LSB = round(((0.172-0.048)/32.0*value+0.048)/32.0*1000.0,2)
	return trm_LSB

def upload_bias(filename = "bias.csv"):
	nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
	array = CSV.csv_to_array(filename)
	for point in range(0,5):
		for block in range(0,7):
			DAC = nameDAC[point] + str(block)
			I2C.peri_write(DAC, array[point, block+1])
			sleep(0.001)
