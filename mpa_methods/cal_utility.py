#from mpa_methods.set_calibration import *
#send_cal_pulse(127, 150, range(1,2), range(1,5))
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
def set_calibration(cal):
	I2C.peri_write('CalDAC0',cal)
	I2C.peri_write('CalDAC1',cal)
	I2C.peri_write('CalDAC2',cal)
	I2C.peri_write('CalDAC3',cal)
	I2C.peri_write('CalDAC4',cal)
	I2C.peri_write('CalDAC5',cal)
	I2C.peri_write('CalDAC6',cal)

def set_threshold(th):
	I2C.peri_write('ThDAC0',th)
	I2C.peri_write('ThDAC1',th)
	I2C.peri_write('ThDAC2',th)
	I2C.peri_write('ThDAC3',th)
	I2C.peri_write('ThDAC4',th)
	I2C.peri_write('ThDAC5',th)
	I2C.peri_write('ThDAC6',th)

def disable_test():
	activate_I2C_chip()
	I2C.peri_write('TESTMUX',0b00000000)
	I2C.peri_write('TEST0',0b00000000)
	I2C.peri_write('TEST1',0b00000000)
	I2C.peri_write('TEST2',0b00000000)
	I2C.peri_write('TEST3',0b00000000)
	I2C.peri_write('TEST4',0b00000000)
	I2C.peri_write('TEST5',0b00000000)
	I2C.peri_write('TEST6',0b00000000)

def enable_test(block, point):
	activate_I2C_chip()
	disable_test()
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)

def set_DAC(block, point, value):
	activate_I2C_chip()
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)
	nameDAC = ["A", "B", "C", "D", "E", "F"]
	DAC = nameDAC[point] + str(block)
	I2C.peri_write(DAC, value)


def activate_async():
	I2C.peri_write('ReadoutMode',0b01)
def activate_sync():
	I2C.peri_write('ReadoutMode',0b00)
def enable_pix_counter(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x53)
def enable_pix_EdgeBRcal(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x47)
def disable_pixel(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x00)
def send_pulses(n_pulse):
	open_shutter()

	for i in range(0, n_pulse):
		SendCommand_CTRL("reset_trigger")
		send_test()
		SendCommand_CTRL("fast_trigger")
	close_shutter()
def send_pulses_fast(number_of_test_pulses = 0, delay_after_fast_reset = 50, 	delay_after_test_pulse = 200, delay_before_next_pulse = 400):
	## now we can set the desired parameters for the test pulse
	# in 40MHz clock cycles

	# 0 - infinite number of sequencies, otherwise as specified

	fc7.write("cnfg_fast_backpressure_enable", 0)
	## now configure the test pulse machine
	Configure_TestPulse(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses)
	open_shutter()
	SendCommand_CTRL("start_trigger")
	sleep(1)
	close_shutter()


def read_pixel_counter(row, pixel):
	data1 = I2C.pixel_read('ReadCounter_LSB',row, pixel)
	data2 = I2C.pixel_read('ReadCounter_MSB',row, pixel)
	if ((data1 == None) or (data2 == None)):
		data1 = I2C.pixel_read('ReadCounter_LSB',row, pixel, 0.01) # Repeat with higher timeout time
		data2 = I2C.pixel_read('ReadCounter_MSB',row, pixel, 0.01) # Repeat with higher timeout time
	if ((data1 == None) or (data2 == None)):
		sleep(1)
		activate_I2C_chip()
		sleep(1)
		data1 = I2C.pixel_read('ReadCounter_LSB',row, pixel, 0.01) # Repeat with higher timeout time
		data2 = I2C.pixel_read('ReadCounter_MSB',row, pixel, 0.01) # Repeat with higher timeout time
	if ((data1 == None) or (data2 == None)):
		print "Error Reading I2C"
		data = 0
	else:
		data = ((data2 & 0x0ffffff) << 8) | (data1 & 0x0fffffff)
	return data
#a = s_curve(100, 50, [1],[2,7],  32)
def s_curve(n_pulse, cal, row, pixel, step = 1, start = 0, stop = 256, print_file =1, filename = "../cernbox/MPA_Results/scurve"):
	clear_counters()
	clear_counters()
	activate_I2C_chip()
	t0 = time.time()
	pixel = np.array(pixel)
	row = np.array(row)
	nrow = int(row.shape[0])
	npix = int(pixel.shape[0])
	data_array = np.zeros(((stop-start)/step+2, nrow*npix+1), dtype = np.int )
	data_array[0,0] = n_pulse
	count = 1
	for r in row:
		for p in pixel:
			enable_pix_counter(r, p)
			data_array[0, count] =  (r-1)*120 + p
			count += 1
	sys.stdout.write("Progress:")
	sys.stdout.flush()
	activate_async()
	set_calibration(cal)
	count_th = 1
	for th in range(start, stop, step): # Temoporary: need to add clear counter fast command
		set_threshold(th)
		sys.stdout.write(str(count_th*100/((stop-start)/step+2)) + "% | ")
		sys.stdout.flush()
		send_pulses(n_pulse)
		data_array[count_th,0] = th
		count = 1
		for r in row:
			for p in pixel:
				data = read_pixel_counter(r, p)
				data_array[count_th, count] =  data
				count += 1
		clear_counters()
		clear_counters()
		count_th += 1
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + ".csv")
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return data_array

#hit_map(100, 250, 200)
def hit_map(n_pulse, cal, th, row = range(1,17), pixel = range (2,120) , print_file =1, filename = "../cernbox/MPA_Results/hitmap"):
	clear_counters()
	clear_counters()
	#activate_I2C_chip()
	t0 = time.time()
	pixel = np.array(pixel)
	row = np.array(row)
	nrow = int(row.shape[0])
	npix = int(pixel.shape[0])
	data_array = np.zeros((nrow,npix), dtype = np.int )
	activate_async()
	set_calibration(cal)
	set_threshold(th)
	#sys.stdout.write("Start Test\n")
	#sys.stdout.flush()
	count_r = 0
	for r in row:
		#sys.stdout.write(str(r*100/16) + "% | " )
		#sys.stdout.flush()
		disable_pixel(0, 0)
		enable_pix_counter(r, 0)
		send_pulses(n_pulse)
		count_p = 0
		for p in pixel:
			data = read_pixel_counter(r, p)
			data_array[count_r, count_p] =  data
			count_p += 1
		count_r += 1
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal" + str(cal) + "_th" + str(th) + ".csv")
	t1 = time.time()
	#print "END"
	#print "Elapsed Time: " + str(t1 - t0)
	return data_array
#a = s_curve_rbr(100, 50, [1], 1)

def s_curve_rbr(n_pulse, cal, row, step = 1, start = 0, stop = 256, print_file =1, filename = "../cernbox/MPA_Results/scurve"):
	t0 = time.time()
	clear_counters()
	clear_counters()
	activate_I2C_chip()
	row = np.array(row)
	nrow = int(row.shape[0])
	data_array = np.zeros(((stop-start)/step+1, nrow*118), dtype = np.int )
	data_array[0,0] = n_pulse
	activate_async()
	set_calibration(cal)
	count = 1
	for r in row:
		disable_pixel(0, 0)
		enable_pix_counter(r, 0)
		sys.stdout.write("Progress Row: " + str(r) + " ")
		sys.stdout.flush()
		count_th = 0
		for th in range(start, stop, step): # Temoporary: need to add clear counter fast command
			set_threshold(th)
			sys.stdout.write(str(count_th*100/((stop-start)/step+2)) + "% | ")
			sys.stdout.flush()
			send_pulses(n_pulse)
			data_array[count_th,0] = th
			count = (r-1)*118
			for p in range(2,120):
				data = read_pixel_counter(r, p)
				data_array[count_th, count] =  data
				count += 1
			clear_counters()
			clear_counters()
			count_th += 1
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + ".csv")
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return data_array

def s_curve_rbr_fr(n_pulse = 1000, cal = 50, row = range(1,17), step = 1, start = 0, stop = 256, plot = 1, print_file =1, filename = "../cernbox/MPA_Results/scurve_fr_"):
	t0 = time.time()
	clear_counters()
	clear_counters()
	activate_I2C_chip()
	row = np.array(row)
	nrow = int(row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((2040, nstep), dtype = np.int16 )
	#data_array[0,0] = n_pulse
	#data_array = np.zeros(((stop-start)/step+1, nrow*118), dtype = np.int )
	activate_async()
	set_calibration(cal)
	count_th = 0
	sys.stdout.write("Progress Scurve: ")
	sys.stdout.flush()
	for th in range(start, stop, step): # Temoporary: need to add clear counter fast command
		set_threshold(th)
		sys.stdout.write(str(count_th*100/((stop-start)/step+2)) + "% | ")
		sys.stdout.flush()
		for r in row:
			disable_pixel(0, 0)
			enable_pix_counter(r, 0)
			send_pulses(n_pulse)
		temp = ReadoutCounters()
		data_array [:, count_th]= temp
		clear_counters()
		clear_counters()
		count_th += 1
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + ".csv")
	if plot:
		for r in row:
			for p in range(1,120):
				plt.plot(range(0,nstep), data_array[p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()

	return data_array

def check_clear_counters(change = 1):
	for i in range(0,168):
		hit_map(10, 250, 200, [6], [7])
		clear_counters()
		value = read_pixel_counter(6,7)
		if change: fc7.write("ctrl_phy_fast_cmd_phase",1)
		if (value != 0):
			print str(i) + " " + str(value)


def s_curve_pbp_fr(n_pulse = 1000, cal = 50, row = range(1,17), step = 1, start = 0, stop = 256, plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/scurve_fr_"):
	t0 = time.time()
	clear_counters()
	clear_counters()
	activate_I2C_chip()
	row = np.array(row)
	nrow = int(row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((2040, nstep), dtype = np.int16 )
	#data_array[0,0] = n_pulse
	#data_array = np.zeros(((stop-start)/step+1, nrow*118), dtype = np.int )
	activate_async()
	set_calibration(cal)
	count_th = 0
	sys.stdout.write("Progress Scurve: ")
	sys.stdout.flush()
	for th in range(start, stop, step): # Temoporary: need to add clear counter fast command
		set_threshold(th)
		sys.stdout.write(str(count_th*100/((stop-start)/step+2)) + "% | ")
		sys.stdout.flush()
		for r in row:
			for p in range(1,120):
				disable_pixel(0, 0)
				enable_pix_counter(r, p)
				send_pulses(n_pulse)
		temp = ReadoutCounters()
		data_array [:, count_th]= temp
		clear_counters()
		clear_counters()
		count_th += 1
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if plot:
		for r in row:
			for p in range(1,120):
				plt.plot(range(0,nstep), data_array[p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()

	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + ".csv")

	return data_array
