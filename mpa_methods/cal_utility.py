#from mpa_methods.set_calibration import *
#send_cal_pulse(127, 150, range(1,2), range(1,5))
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
from mpa_methods.bias_calibration import *
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm

def errorf(x, *p):
	a, mu, sigma = p
#    print x
	return 0.5*a*(1.0+erf((x-mu)/sigma))

def line(x, *p):
	g, offset = p
	return  numpy.array(x) *g + offset

def gauss(x, *p):
	A, mu, sigma = p
	return A*numpy.exp(-(x-mu)**2/(2.*sigma**2))


def errorfc(x, *p):
	a, mu, sigma = p
	return a*0.5*erfc((x-mu)/sigma)

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

def inject():
	sleep(0.005)
	open_shutter()
	if (cal != 0):
		sleep(0.005)
		SendCommand_CTRL("start_trigger")
		test = 1
		while (test):
			test = fc7.read("stat_fast_fsm_state")
			sleep(0.001)
	else:
		sleep(0.000001*n_pulse)
		close_shutter()

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

def enable_pix_sync(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x53)

def enable_pix_EdgeBRcal(r,p, polarity = "rise"):
	I2C.pixel_write('ModeSel', r, p, 0b00)
	if (polarity == "rise"):
		I2C.pixel_write('ENFLAGS', r, p, 0x57) # with pixel counter for debugging
	elif (polarity == "fall"):
		I2C.pixel_write('ENFLAGS', r, p, 0x55) # with pixel counter for debugging
	else:
		print "Polarity not recognized"
		return
	#sleep(0.001)
	#return bin(I2C.pixel_read('ENFLAGS', r, p))

def enable_pix_LevelBRcal(r,p, polarity = "rise"):

	I2C.pixel_write('ModeSel', r, p, 0b01)
	if (polarity == "rise"):
		I2C.pixel_write('ENFLAGS', r, p, 0x5b) # with pixel counter for debugging
	elif (polarity == "fall"):
		I2C.pixel_write('ENFLAGS', r, p, 0x59) # with pixel counter for debugging
	else:
		print "Polarity not recognized"
		return
	return bin(I2C.pixel_read('ENFLAGS', r, p))

def disable_pixel(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x00)
	#I2C.pixel_write('ModeSel', r, p, 0x00)

def activate_shift():
	I2C.peri_write('ReadoutMode',0b10)

def activate_pp():
	I2C.peri_write('ECM',0b10000001)

def activate_ss():
	I2C.peri_write('ECM',0b01000001)

def activate_ps():
	I2C.peri_write('ECM',0b00001000)

def enable_dig_cal(r,p, pattern = 0b00000001):
	I2C.pixel_write('ENFLAGS', r, p, 0x20)
	I2C.pixel_write('DigPattern', r, p, pattern)

def send_pulses(n_pulse):
	open_shutter()
	sleep(0.01)
	for i in range(0, n_pulse):
		send_test()
	sleep(0.001)
	close_shutter()
def send_pulses_fast(number_of_test_pulses = 100, delay_after_fast_reset = 200, delay_after_test_pulse = 200, delay_before_next_pulse = 200):
	## now we can set the desired parameters for the test pulse
	# in 40MHz clock cycles

	# 0 - infinite number of sequencies, otherwise as specified

	fc7.write("cnfg_fast_backpressure_enable", 0)
	## now configure the test pulse machine
	Configure_TestPulse_MPA(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses, enable_rst_L1 = 0)
	open_shutter()
	sleep(0.01)
	SendCommand_CTRL("start_trigger")
	sleep(0.01)
	close_shutter()

def send_pulse_trigger(number_of_test_pulses = 1, delay_after_fast_reset = 200, delay_after_test_pulse = 200, delay_before_next_pulse = 200):
	## now we can set the desired parameters for the test pulse
	# in 40MHz clock cycles

	# 0 - infinite number of sequencies, otherwise as specified

	fc7.write("cnfg_fast_backpressure_enable", 0)
	## now configure the test pulse machine
	Configure_TestPulse_MPA(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses, enable_rst_L1 = 1)
	SendCommand_CTRL("start_trigger")

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

# Readout Counters current method
def ReadoutCounters(raw_mode_en = 0):
	# set the raw mode to the firmware
	fc7.write("cnfg_phy_slvs_raw_mode_en", raw_mode_en)
	t0 = time.time()
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	#print "---> Sending Start and Waiting for Data"
	#StartCountersRead()
	start_counters_read()
	timeout = 0
	while ((mpa_counters_ready == 0) & (timeout < 50)):
		sleep(0.01)
		mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
		timeout += 1
	if (timeout >= 50):
		print "Fail: "
		print fc7.read("stat_slvs_debug_mpa_counters_store_fsm_state")
		failed = True;
		return failed, 0
	#print "---> MPA Counters Ready(should be one): ", mpa_counters_ready
	if raw_mode_en == 1:
		count = np.zeros((2040, ), dtype = np.uint16)
		cycle = 0
		for i in range(0,20000):
			fifo1_word = fc7.read("ctrl_slvs_debug_fifo1_data")
			fifo2_word = fc7.read("ctrl_slvs_debug_fifo2_data")
			line1 = to_number(fifo1_word,8,0)
			line2 = to_number(fifo1_word,16,8)
			line3 = to_number(fifo1_word,24,16)
			line4 = to_number(fifo2_word,8,0)
			line5 = to_number(fifo2_word,16,8)
			if (((line1 & 0b10000000) == 128) & ((line4 & 0b10000000) == 128)):
				temp = ((line2 & 0b00100000) << 9) | ((line3 & 0b00100000) << 8) | ((line4 & 0b00100000) << 7) | ((line5 & 0b00100000) << 6) | ((line1 & 0b00010000) << 6) | ((line2 & 0b00010000) << 5) | ((line3 & 0b00010000) << 4) | ((line4 & 0b00010000) << 3) | ((line5 & 0b10000000) >> 1) | ((line1 & 0b01000000) >> 1) | ((line2 & 0b01000000) >> 2) | ((line3 & 0b01000000) >> 3) | ((line4 & 0b01000000) >> 4) | ((line5 & 0b01000000) >> 5) | ((line1 & 0b00100000) >> 5)
				if (temp != 0):
					count[cycle] = temp - 1
					cycle += 1
	else:
		# here is the parsed mode, when the fpga parses all the counters
		count = fc7.fifoRead("ctrl_slvs_debug_fifo2_data", 2040)
		for i in range(2040):
			count[i] = count[i] - 1

	sleep(0.001)
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	failed = False
	return failed, count
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

def s_curve_rbr(n_pulse, cal, row, step = 1, start = 0, stop = 256, plot = 1, print_file =1, filename = "../cernbox/MPA_Results/scurve"):
	t0 = time.time()
	clear_counters()
	clear_counters()
	activate_I2C_chip()
	row = np.array(row)
	nrow = int(row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((nstep, nrow*118), dtype = np.int )
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

	if plot:
		for r in row:
			for p in range(1,120):
				plt.plot(range(0,nstep), data_array[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return data_array

# s_curve_rbr_fr(n_pulse = 300, cal = 0, row = range(1,17), step = 1, start = 0, stop = 256, plot = 1, print_file =0)

def s_curve_rbr_fr(n_pulse = 1000, cal = 50, row = range(1,17), step = 1, start = 0, stop = 256, pulse_delay = 50, plot = 1, print_file =1, filename = "../cernbox/MPA_Results/scurve_fr_"):
	t0 = time.time()
	clear_counters(8)
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
	fc7.write("cnfg_fast_backpressure_enable", 0)
	Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_rst_L1 = 0)
	count_th = 0
	th = start
	while (th < stop): # Temoporary: need to add clear counter fast command
		set_threshold(th)
		sys.stdout.write(str(count_th*100/((stop-start)/step+2)) + "% | ")
		sys.stdout.flush()
		for r in row:
			disable_pixel(0, 0)
			enable_pix_counter(r, 0)

			sleep(0.0025)
			open_shutter(8)
			if (cal != 0):
				#sleep(0.005)
				SendCommand_CTRL("start_trigger")
				test = 1
				while (test):
					test = fc7.read("stat_fast_fsm_state")
					sleep(0.001)
			else:
				sleep(0.000001*n_pulse)
			close_shutter(8)
		tB = time.time()
		sleep(0.005)
		fail, temp = ReadoutCounters()
		tC = time.time()
		#print "Elapsed Time: " + str(tC - tB) + " " + str(tB - tA)
		#sleep(0.005)
		if fail:
			print "FailedPoint, repeat!"
		else:
			data_array [:, count_th]= temp
			count_th += 1
			th += step
		clear_counters(8)
		clear_counters(8)
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + ".csv")
	if plot:
		for r in row:
			for p in range(1,120):
				plt.plot(range(0,nstep), data_array[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()

	return data_array

def check_clear_counters(change = 1, points = 168, iterations = 10, duration = 8):
	count = 0
	for i in range(0,points):
		for j in range(0,iterations):
			hit_map(10, 250, 200, [1], [7])
			sleep(0.001)
			value = read_pixel_counter(1,7)
			if (value != 10):
				print str(i) + " " + str(j) + " " + str(value)
				count += 1
			clear_counters(duration)
			sleep(0.001)
			value = read_pixel_counter(1,7)
			if (value != 0):
				print str(i) + " " + str(j) + " " + str(value)
				count += 1
		if change: fc7.write("ctrl_phy_fast_cmd_phase",1)
	return count

# s_curve_pbp_fr(n_pulse = 1000, cal = 100, row = range(1,17), pixel = range(1,120), step = 1, start = 0, stop = 256, pulse_delay = 50,  plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/scurve_fr_"):

def s_curve_pbp_fr(n_pulse = 1000, cal = 100, row = range(1,17), pixel = range(1,120), step = 1, start = 0, stop = 256, pulse_delay = 50,  plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/scurve_fr_"):
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
	sleep(1)
	sys.stdout.write("Progress Scurve: ")
	sys.stdout.flush()
	fc7.write("cnfg_fast_backpressure_enable", 0)
	## now configure the test pulse machine
	Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_rst_L1 = 0)
	count_th = 0
	th = start
	while (th < stop): # Temoporary: need to add clear counter fast command
		set_threshold(th)
		sys.stdout.write(str(count_th*100/((stop-start)/step+2)) + "% | ")
		sys.stdout.flush()
		for r in row:
			for p in pixel:
				disable_pixel(0, 0)
				enable_pix_counter(r, p)
				testI2C = I2C.pixel_read('ENFLAGS', r, p)
				if (testI2C != 83):
					print "Failed I2C"
				sleep(0.0025)
				open_shutter(8)
				if (cal != 0):
					#sleep(0.005)
					SendCommand_CTRL("start_trigger")
					test = 1
					while (test):
						test = fc7.read("stat_fast_fsm_state")
						sleep(0.001)
					else:
						sleep(0.000001*n_pulse)
				close_shutter(8)
		tB = time.time()
		sleep(0.005)
		fail, temp = ReadoutCounters()
		tC = time.time()
		#print "Elapsed Time: " + str(tC - tB) + " " + str(tB - tA)
		if fail:
			print "FailedPoint, repeat!"
		else:
			data_array [:, count_th]= temp
			count_th += 1
			th += step
		clear_counters(8)
		clear_counters(8)
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + ".csv")
	if plot:
		for r in row:
			for p in pixel:
				plt.plot(range(0,nstep), data_array[(r-1)*120+p,:],'-', label = str(r) + " " + str(p))
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.legend()
		plt.show()
	return data_array

def reset_trim(value = 15):
	I2C.pixel_write("TrimDAC",0,0,value)
# trimming_noise(nominal_DAC = 70, plot = 1, start = 0, stop = 150, ratio = 3.32, row = [1], pixel = range(1,120))
def trimming_noise(iteration = 1, nominal_DAC = 41, data_array = np.zeros(2040, dtype = np.int ), plot = 1, start = 0, stop = 150, ratio = 3.90, row = range(1,17), pixel = range(1,120)):
	t0 = time.time()
	for r in row:
		I2C.pixel_write("TrimDAC",r,0,15)
	scurve_init = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row, step = 1, start = start, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
	scurve = scurve_init
	for i in range(0,iteration):
		for r in row:
			for p in pixel:
				init_DAC = np.argmax(scurve[(r-1)*120+p,:])
				trim_DAC = int(round((nominal_DAC - init_DAC)/ratio))
				curr_dac = I2C.pixel_read("TrimDAC",r,p)
				new_DAC = curr_dac + trim_DAC
				if (new_DAC > 31):
					new_DAC = 31
					print "High TrimDAC limit for pixel: ", p, " Row: ", r
				if (new_DAC < 0):
					new_DAC = 0
					print "Low TrimDAC limit for pixel: ", p, " Row: ", r
				I2C.pixel_write("TrimDAC",r,p,new_DAC)
				#sleep(0.01)
				check = I2C.pixel_read("TrimDAC",r,p)
				#sleep(0.01)
				data_array[(r-1)*120+p] = new_DAC
				if (check != new_DAC): print "Trim not written at: ", p, " Row: ", r
		if (i != iteration - 1):
			scurve = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row , step = 1, start = start, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
	t1 = time.time()
	print "END"
	print "Trimming Elapsed Time: " + str(t1 - t0)

	if plot:
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
		scurve_final = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row , step = 1, start = start, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
		plt.figure(1)
		for r in row:
			for p in pixel:
				plt.plot(range(start,stop+1), scurve_init[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.figure(2)
		for r in row:
			for p in pixel:
				plt.plot(range(start,stop+1), scurve_final[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()
	return data_array

def trimming_chip_noise(nominal_DAC = 75, nstep = 4, data_array = np.zeros(2040, dtype = np.int ), plot = 1, start = 0, stop = 150, ratio = 3.68, print_file = 0, filename = "../cernbox/MPA_Results/Test"):
	activate_I2C_chip()
	for i in range(1,nstep+1):
		I2C.pixel_write("TrimDAC",0,0,0)
		row = range(i, 17, nstep)
		print "Doing Rows: ", row
		data_array = trimming_noise(nominal_DAC = nominal_DAC, data_array = data_array, plot = 0, start = start, stop = stop, ratio = ratio, row = row, pixel = range(1,120))
	for r in range(1,17):
		for p in range(1,120):
			I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])

	if plot:
		scurve = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row , step = 1, start = start, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
		plt.figure(1)
		for r in range(0,17):
			for p in range(0,120):
				plt.plot(range(start,stop+1), scurve[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_noiseTrimming" + str(nominal_DAC) + ".csv")
	return data_array

def trimming_cal(n_pulse = 300, cal = 10, iteration = 1, nominal_DAC = 110, data_array = np.zeros(2040, dtype = np.int ), plot = 1,  stop = 150, ratio = 3.90, row = range(1,17), pixel = range(1,120)):
	t0 = time.time()
	for r in row:
		for p in pixel:
			I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
	scurve_init = s_curve_rbr_fr(n_pulse = n_pulse, cal = cal, row = row, step = 1, start = 0, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
	scurve = scurve_init
	for i in range(0,iteration):
		for r in row:
			for p in pixel:
				start_DAC = np.argmax(scurve[(r-1)*120+p,:]) + 10
				try:
					par, cov = curve_fit(errorfc, range(start_DAC, stop), scurve[(r-1)*120+p,start_DAC + 1 :stop + 1], p0= [n_pulse, nominal_DAC, 2])
					init_DAC = int(round(par[1]))
					trim_DAC = int(round((nominal_DAC - init_DAC)/ratio))
					curr_dac = I2C.pixel_read("TrimDAC",r,p)
					new_DAC = curr_dac + trim_DAC
					if (new_DAC > 31):
						new_DAC = 31
						print "High TrimDAC limit for pixel: ", p, " Row: ", r
					if (new_DAC < 0):
						new_DAC = 0
						print "Low TrimDAC limit for pixel: ", p, " Row: ", r
					I2C.pixel_write("TrimDAC", r, p, new_DAC)
					#sleep(0.01)
					check = I2C.pixel_read("TrimDAC", r, p)
					#sleep(0.01)
					data_array[(r-1)*120+p] = new_DAC
					if (check != new_DAC): print "Trim not written at: ", p, " Row: ", r
				except RuntimeError or TypeError:
					print "Fitting failed on pixel ", p , " row: " ,r

		if (i != iteration - 1):
			scurve = s_curve_rbr_fr(n_pulse = n_pulse, cal = cal, row = row , step = 1, start = 0, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
	t1 = time.time()
	print "END"
	print "Trimming Elapsed Time: " + str(t1 - t0)

	if plot:
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
		scurve_final = s_curve_rbr_fr(n_pulse = n_pulse, cal = cal, row = row , step = 1, start = 0, stop = stop, pulse_delay = 50, plot = 0, print_file =0)
		plt.figure(1)
		for r in row:
			for p in pixel:
				plt.plot(range(0,stop+1), scurve_init[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.figure(2)
		for r in row:
			for p in pixel:
				plt.plot(range(0,stop+1), scurve_final[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()
	return data_array

def trimming_chip_cal(nominal_DAC = 110, nstep = 4, data_array = np.zeros(2040, dtype = np.int ), n_pulse = 300, cal = 20, iteration = 2, plot = 1, stop = 256, ratio = 3.68, print_file = 0, filename = "../cernbox/MPA_Results/Test"):
	activate_I2C_chip()
	for i in range(1,nstep+1):
		I2C.pixel_write("TrimDAC",0,0,0)
		row = range(i, 17, nstep)
		print "Doing Rows: ", row
		data_array = trimming_cal(n_pulse = n_pulse, cal = cal, iteration = iteration, nominal_DAC = nominal_DAC, data_array = data_array, plot = 0, stop = stop, ratio = ratio, row = row)
	for r in range(1,17):
		for p in range(1,120):
			I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])

	if plot:
		scurve = s_curve_rbr_fr(n_pulse = 100, cal = cal, row = row , step = 1, start = 0, stop = stop, pulse_delay = 100, plot = 0, print_file =0)
		plt.figure(1)
		for r in range(0,17):
			for p in range(0,120):
				plt.plot(range(0,stop+1), scurve[(r-1)*120+p,:],'-')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_noiseCal" + str(nominal_DAC) + ".csv")
	return data_array

def trimDAC_linearity_rbr(row, pixel = range(1,120), plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/TrimDAC"):
	t0 = time.time()
	activate_I2C_chip()
	data = np.zeros((2040, 32), dtype = np.int16 )
	I2C.pixel_write("TrimDAC",0,0,31)
	for i in range(0,32):
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,i)
		scurve = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row,  step = 1, start = 0, stop = 150, pulse_delay = 50, plot = 0, print_file =0)
		for r in row:
			for p in pixel:
				data[(r-1)*120+p,i] = np.argmax(scurve[(r-1)*120+p,:])
		if (i == 15):	I2C.pixel_write("TrimDAC",0,0,0)
	t1 = time.time()
	print "END"
	print "Trimming Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data, str(filename) + ".csv")
	if plot:
		plt.figure(1)
		for r in row:
			for p in pixel:
				plt.plot(range(0,32), data[(r-1)*120+p,:],'o', label = (r-1)*120+p)
		plt.xlabel('Trimming DAC value [#]')
		plt.ylabel('Trimming Voltage [V]')
		plt.legend()
		plt.show()

def trimDAC_linearity_pbp(row, pixel, plot = 1,  print_file = 0, filename = "../cernbox/MPA_Results/TrimDAC"):
	t0 = time.time()
	activate_I2C_chip()
	data = np.zeros((2040, 32), dtype = np.int16 )
	I2C.pixel_write("TrimDAC",0,0,31)
	for i in range(0,32):
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,i)
		scurve = s_curve_pbp_fr(n_pulse = 300, cal = 0, row = row, pixel = pixel, step = 1, start = 0, stop = 150, pulse_delay = 50, plot = 0, print_file =0)
		for r in row:
			for p in pixel:
				data[(r-1)*120+p,i] = np.argmax(scurve[(r-1)*120+p,:] )
		if (i == 15):	I2C.pixel_write("TrimDAC",0,0,0)
	t1 = time.time()
	print "END"
	print "Trimming Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data, str(filename) + ".csv")
	if plot:
		plt.figure(1)
		for r in row:
			for p in pixel:
				plt.plot(range(0,32), data[(r-1)*120+p,:],'o', label = (r-1)*120+p)
		plt.xlabel('Trimming DAC value [#]')
		plt.ylabel('Trimming Voltage [V]')
		plt.legend()
		plt.show()

def Configure_TestPulse_DLL_MPA(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses):
	fc7.write("cnfg_fast_initial_fast_reset_enable", 0)
	fc7.write("cnfg_fast_delay_after_fast_reset", delay_after_fast_reset)
	fc7.write("cnfg_fast_delay_after_test_pulse", delay_after_test_pulse)
	fc7.write("cnfg_fast_delay_before_next_pulse", delay_before_next_pulse)
	fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
	fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
	fc7.write("cnfg_fast_tp_fsm_l1a_en", 0)
	fc7.write("cnfg_fast_triggers_to_accept", number_of_test_pulses)
	fc7.write("cnfg_fast_source", 6)
	sleep(0.1)
	SendCommand_CTRL("load_trigger_config")
	sleep(0.1)


def test_DLL(row, pixel, delay_reset, iteration = 10):
	#enable_pix_EdgeBRcal(row, pixel)
	latency_map = np.zeros((64, iteration), dtype = np.float16 )
	latency = np.zeros((64, ), dtype = np.float16 )
	Configure_TestPulse_DLL_MPA(delay_reset, 10, 10, 1)
	for delay in range(0,64):
		I2C.peri_write('DL_ctrl0', delay)
		sleep(0.001)
		for i in range(0, iteration):
			cnt = 0
			while (cnt < 20):
				SendCommand_CTRL("start_trigger")
				sleep(0.001)
				nst, pos, row, cur = read_stubs()
				tmp = np.where(pos == pixel*2)
				try:
					latency_map[delay, i] = tmp[0][0]*2 - nst[tmp[0][0]]
					cnt = 20
				except IndexError:
					cnt += 1
		latency[delay] = np.average(latency_map[delay])
	return 	latency

def char_DLL(row, pixel, delay_reset, curr = range(0,32), plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/DLL_char"):
	activate_pp()
	activate_sync()
	disable_pixel(0,0)
	enable_pix_LevelBRcal(row, pixel)
	I2C.pixel_write('ModeSel', row, pixel, 0b01)
	I2C.pixel_write('HipCut', row, pixel, 0b001)
	I2C.peri_write('DL_en', 0b11111111)
	latency = np.zeros((32, 64 ), dtype = np.int )
	for i in curr:
		I2C.peri_write('F0',i)
		latency[i] = test_DLL(row, pixel, delay_reset)
	if print_file:
		CSV.ArrayToCSV (latency, str(filename) + ".csv")
	if plot:
		for i in curr:
			plt.plot(range(0,64),latency[i],'o-', label = i)
		plt.xlabel('Delay value [#]')
		plt.ylabel('Cycle [#]')
		plt.legend()
		plt.show()
	return latency

def shaper_rise(row, pixel, delay_reset, BX, th = range(90,170,10), cal = 50, iteration = 10, plot = 1, print_file = 1, filename = "../cernbox/MPA_Results/shaper_rise", sampling = "edge"):
	activate_I2C_chip()
	activate_pp()
	activate_sync()
	disable_pixel(0,0)
	if (sampling == "level"):
		enable_pix_LevelBRcal(row, pixel)
	elif (sampling == "edge"):
		enable_pix_EdgeBRcal(row, pixel)
	else:
		print "Sampling Mode not recognized"
		return
	I2C.peri_write('DL_en', 0b11111111)
	set_calibration(cal)
	th = np.array(th)
	nth = int(th.shape[0])
	latency_r = np.zeros((nth, 32 ), dtype = np.float16 )
	latency_f = np.zeros((nth, 32 ), dtype = np.float16 )
	delta_r =  np.zeros((nth, ), dtype = np.float16 )
	delta_f =  np.zeros((nth, ), dtype = np.float16 )
	delta0 = 0
	set_threshold(th[0])
	latency_r[0] = np.around(test_DLL(row, pixel, delay_reset))
	for i in range(0,32):
		if (latency_r[0,i] == BX):
			delta0 += 1
	count_tot0 = 0
	index = 0
	for t in th:
		set_threshold(t)
		if (sampling == "level"):
			enable_pix_LevelBRcal(row, pixel)
		elif (sampling == "edge"):
			enable_pix_EdgeBRcal(row, pixel)
		latency_r[index] = np.around(test_DLL(row, pixel, delay_reset))
		count_r = 0
		count_f = 0
		if (latency_r[index,0] == BX):
			for i in range(0,32):
				if (latency_r[index,i] == BX):
					count_r += 1
			delta_r[index] =  (delta0 - count_r)
			delta1 = (delta0 - count_r)
		elif (latency_r[index,0] == BX +1 ):
			for i in range(0,32):
				if (latency_r[index,i] == BX + 1):
					count_r += 1
			delta_r[index] = delta1 + (21 - count_r) # 21 is the number of DLL LSB/BX
		else:
			print "ERROR for: ", t
# Falling part
		if (sampling == "level"):
			enable_pix_LevelBRcal(row, pixel, "fall")
		elif (sampling == "edge"):
			enable_pix_EdgeBRcal(row, pixel, "fall")
		latency_f[index] = np.around(test_DLL(row, pixel, delay_reset))
		for i in range(0,32):
			if (latency_f[index,i] == latency_f[index,0]):
				count_f += 1
		delta_f[index] = (latency_f[index,0] - latency_r[index,0] - 1) * 21 + (21- count_f) + count_r + delta_r[index]
		index += 1
	data_array = np.array([delta_r, delta_f, th])
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + "_" + sampling + ".csv")
	if plot:
		for t in th:
			plt.plot(delta_r*1.2, (th - 75)*1.456,'o')
			plt.plot(delta_f*1.2, (th - 75)*1.456,'o')
		plt.xlabel('Delay value [#]')
		plt.ylabel('threshold DAC [mV]')
		plt.show()

	return latency_r, latency_f, data_array

def shaper_fall(row, pixel, delay_reset, BX, th = range(160,90,-10), cal = 50, iteration = 10, plot = 1, print_file = 1, filename = "../cernbox/MPA_Results/shaper_fall", sampling = "edge"):
	activate_I2C_chip()
	activate_pp()
	activate_sync()
	disable_pixel(0,0)
	if (sampling == "level"):
		enable_pix_LevelBRcal(row, pixel, "fall")
	elif (sampling == "edge"):
		enable_pix_EdgeBRcal(row, pixel, "fall")
	else:
		print "Sampling Mode not recognized"
		return
	set_calibration(cal)
	th = np.array(th)
	nth = int(th.shape[0])
	latency = np.zeros((nth, 64 ), dtype = np.float16 )
	delta =  np.zeros((nth, ), dtype = np.float16 )
	delta0 = 0
	set_threshold(th[0])
	latency[0] = np.around(test_DLL(row, pixel, delay_reset))
	for i in range(0,64):
		if (latency[0,i] == BX):
			delta0 += 1
	count_tot0 = 0
	index = 0
	for t in th:
		set_threshold(t)
		latency[index] = np.around(test_DLL(row, pixel, delay_reset))
		count0 = 0
		count1 = 0
		count2 = 0
		count3 = 0
		if (latency[index,0] == BX):
			for i in range(0,64):
				if (latency[index,i] == BX):
					count0 += 1
			delta[index] =  (delta0 - count0)*1.25
			count_tot0 = (delta0 - count0)*1.25
		else: #if (latency[index,0] > BX):
			for i in range(0,64):
				if (latency[index,i] == BX + 1):
					count1 += 1
				if (latency[index,i] == BX + 2):
					count2 += 1
				if (latency[index,i] == BX + 3):
					count3 += 1
			delta[index] = (delta0 - count0)*1.25 + 25-(count1*1.25) + 25-(count2*1.25) + 25-(count3*1.25)
		index += 1
	data_array = np.array([delta, th])
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(cal) + "_"+  sampling + ".csv")
	if plot:
		for t in th:
			plt.plot(delta, (th - 75)*1.456,'o')
		plt.xlabel('Delay value [#]')
		plt.ylabel('threshold DAC [mV]')
		plt.show()

	return latency, data_array

def timewalk(row, pixel, delay_reset, BX, cal = range(15,255,10), th = 100, iteration = 10, plot = 1, print_file = 1, filename = "../cernbox/MPA_Results/timewalk"):
	activate_I2C_chip()
	activate_pp()
	activate_sync()
	disable_pixel(0,0)
	enable_pix_LevelBRcal(row, pixel)
	set_threshold(th)
	cal = np.array(cal)
	ncal = int(cal.shape[0])
	latency = np.zeros((ncal, 64 ), dtype = np.float16 )
	delta =  np.zeros((ncal, ), dtype = np.float16 )
	index = 0
	for c in cal:
		set_calibration(c)
		latency[index] = test_DLL(row, pixel, delay_reset)
		tmp = np.where(latency[index] == BX)
		delta[index] = tmp[0][0]
		index += 1
	data_array = np.array([delta, cal])
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_th_" + str(th) + ".csv")
	if plot:
		plt.plot(delta, cal,'o')
		plt.xlabel('Delay value [#]')
		plt.ylabel('threshold DAC [mV]')
		plt.show()

	return latency, data_array

def download_trimming(filename = "trimming_value"):
		data_array = np.zeros((118,16), dtype = np.int )
		for r in range(0,16):
			for p in range(0,118):
				data_array[p,r] = I2C.pixel_read("TrimDAC",r+1,p+2)
				sleep(0.001)
		CSV.ArrayToCSV (data_array, str(filename) + ".csv")

def upload_trimming(filename = "trimming_value.csv"):
		array = CSV.csv_to_array(filename)
		for r in range(0,16):
			for p in range(0,118):
				I2C.pixel_write("TrimDAC",r+1,p+2,array[p, r+1])
				sleep(0.001)
