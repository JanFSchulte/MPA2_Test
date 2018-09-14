#from mpa_methods.set_calibration import *
#send_cal_pulse(127, 150, range(1,2), range(1,5))
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from mpa_methods.mpa_i2c_conf import *
from myScripts.Utilities import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm
import seaborn as sns

def errorf(x, *p):
	a, mu, sigma = p
	return 0.5*a*(1.0+erf((x-mu)/sigma))

def line(x, *p):
	g, offset = p
	return  np.array(x) *g + offset

def gauss(x, *p):
	A, mu, sigma = p
	return A*np.exp(-(x-mu)**2/(2.*sigma**2))


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
	activate_I2C_chip(verbose = 0)
	disable_test()
	test = "TEST" + str(block)
	I2C.peri_write('TESTMUX',0b00000001 << block)
	I2C.peri_write(test, 0b00000001 << point)

def set_DAC(block, point, value):
	activate_I2C_chip(verbose = 0)
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

def enable_pix_disable_ancal(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x13)

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

	#return bin(I2C.pixel_read('ENFLAGS', r, p))

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
##### plot_extract_scurve function take scurve data and extract threhsold and noise data. If plot = 1, it also plot scurves and histograms
def plot_extract_scurve(row, pixel, s_type, scurve, n_pulse, nominal_DAC, start, stop, extract, plot):
	th_array = np.zeros(2040, dtype = np.int )
	noise_array = np.zeros(2040, dtype = np.float )
	for r in row:
		for p in pixel:
			if plot:
				plt.plot(range(start,stop), scurve[(r-1)*120+p,0:(stop-start)],'-')
			# Noise and Spread study
			if extract:
				try:
					if s_type == "THR":
						start_DAC = np.argmax(scurve[(r-1)*120+p,:]) + 10
						par, cov = curve_fit(errorfc, range(start_DAC, (stop-start)), scurve[(r-1)*120+p,start_DAC + 1 :(stop-start) + 1], p0= [n_pulse, nominal_DAC, 2])
					elif s_type == "CAL":
						start_DAC = 0
						par, cov = curve_fit(errorf, range(start_DAC, (stop-start)), scurve[(r-1)*120+p,start_DAC + 1 :(stop-start) + 1], p0= [n_pulse, nominal_DAC, 2])
					th_array[(r-1)*120+p] = int(round(par[1]))
					noise_array[(r-1)*120+p] = par[2]
				except RuntimeError or TypeError:
					print "Fitting failed on pixel ", p , " row: " ,r
	if plot:
		if s_type == "THR":	plt.xlabel('Threshold DAC value')
		if s_type == "CAL":	plt.xlabel('Calibration DAC value')
		plt.ylabel('Counter Value')
		if extract:
			th_array = [a for a in th_array if a != 0]
			noise_array = [b for b in noise_array if b != 0]
			plt.figure(2)
			if len(th_array) == 1:
				plt.title("Threshold")
				plt.plot(pixel, th_array, 'o')
			else:
				plt.hist(th_array[1:1920], bins=range(min(th_array), max(th_array) + 1, 1))
			plt.figure(3)
			if len(noise_array) == 1:
				plt.title("Noise")
				plt.plot(pixel, noise_array, 'o')
			else:
				plt.hist(noise_array, bins=np.arange(min(noise_array), max(noise_array) + 1 , 0.1))

			print "Threshold Average: ", np.mean(th_array[1:1920]), " Spread SD: ", np.std(th_array[1:1920])
			print "Noise Average: ", np.mean(noise_array[1:1920]), " Spread SD: ", np.std(noise_array[1:1920])
	if extract:
		return 	th_array, noise_array

##### send_pulses
def send_pulses(n_pulse):
	open_shutter()
	sleep(0.01)
	for i in range(0, n_pulse):
		send_test()
		sleep(0.1)
	sleep(0.001)
	close_shutter()

def send_pulses_fast(n_pulse, row, pixel, cal):
	disable_pixel(0, 0)
	enable_pix_counter(row, pixel)
	#enable_pix_disable_ancal(row, pixel)
	sleep(0.0025)
	try:
		open_shutter(8)
	except ChipsException:
		print "Error ChipsException, repeat command"
		sleep (0.001)
		open_shutter(8)
	if (cal != 0):
		SendCommand_CTRL("start_trigger")
		test = 1
		while (test):
			test = fc7.read("stat_fast_fsm_state")
			sleep(0.001)
	else:
		sleep(0.000001*n_pulse)
	try:
		close_shutter(8)
	except ChipsException:
		print "Error ChipsException, repeat ccommand"
		sleep (0.001)
		close_shutter(8)

def send_pulses_fast_all(n_pulse, row, pixel, cal):
	disable_pixel(0, 0)
	for r in row:
		for p in pixel:
			enable_pix_disable_ancal(r, p)
			#enable_pix_counter(r,p)
	sleep(0.0025)
	try:
		open_shutter(8)
	except ChipsException:
		print "Error ChipsException, repeat ccommand"
		sleep (0.001)
		open_shutter(8)
	if (cal != 0):
		SendCommand_CTRL("start_trigger")
		test = 1
		while (test):
			test = fc7.read("stat_fast_fsm_state")
			sleep(0.001)
	else:
		sleep(1*n_pulse)
	try:
		close_shutter(8)
	except ChipsException:
		print "Error ChipsException, repeat ccommand"
		sleep (0.001)
		close_shutter(8)


def read_pixel_counter(row, pixel):
	data1 = I2C.pixel_read('ReadCounter_LSB',row, pixel)
	data2 = I2C.pixel_read('ReadCounter_MSB',row, pixel)
	if ((data1 == None) or (data2 == None)):
		data1 = I2C.pixel_read('ReadCounter_LSB',row, pixel, 0.01) # Repeat with higher timeout time
		data2 = I2C.pixel_read('ReadCounter_MSB',row, pixel, 0.01) # Repeat with higher timeout time
	if ((data1 == None) or (data2 == None)):
		sleep(1)
		activate_I2C_chip(verbose = 0)
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
	#sleep(0.1)
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
	activate_I2C_chip(verbose = 0)
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
def hit_map(n_pulse, cal, th, row = range(1,17), pixel = range (2,120) , print_file =0, filename = "../cernbox/MPA_Results/hitmap"):
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

def hit_map_plot(n_pulse = 1000, cal = 40, th = 100, row = range(1,17), pixel = range (1,120)):
	clear_counters()
	t0 = time.time()
	pixel = np.array(pixel)
	row = np.array(row)
	nrow = int(row.shape[0])
	npix = int(pixel.shape[0])
	data_array = np.zeros((nrow,npix), dtype = np.int )
	activate_async()
	set_calibration(cal)
	set_threshold(th)
	#count_r = 0
	repeat = 0
	#while repeat < 15:
	count_r = 0
	fcount_r = 0
	disable_pixel(0,0)
	clear_counters(8)
	clear_counters(8)
	for r in row:
		enable_pix_disable_ancal(r,0)
	sleep(0.1)
	activate_I2C_chip()
	# Disable Noisy Pixels
	#disable_pixel(2,16)
	#disable_pixel(3,11)
	#disable_pixel(10,76)
	send_pulses_(n_pulse)
	count_r = 0
	for r in row:
		count_p = 0
		for p in pixel:
			data = read_pixel_counter(r, p)
			data_array[count_r, count_p] =  data
			count_p += 1
		count_r += 1
	#data_array[9,75]=0
	t1 = time.time()
		#return data_array
	#plt.imshow(data_array, cmap='hot', interpolation='nearest')
	#plt.show()
	ax = sns.heatmap(data_array, vmin = 0, xticklabels = 5, yticklabels = row)
	plt.show()
	return data_array

def heat_map(row = range(1,17), start_data = 150, start_th = 160, end_th = 180, file_name = "Am-241_tin_long_cal_0.csv"):
	data = CSV.csv_to_array(file_name)
	data_array = np.zeros((16, 119), dtype = np.int)
	for r in row:
		for p in range(1,120):
			data_array[(r - 1), (p - 1)] = np.sum(data[(r-1)*120 + p, (start_th - start_data):(end_th - start_data)])
	ax = sns.heatmap(data_array, vmin = 0, xticklabels = 5, yticklabels = row)
	plt.show()
	return data_array


def s_curve_rbr(n_pulse, cal, row, step = 1, start = 0, stop = 256, plot = 1, print_file =1, filename = "../cernbox/MPA_Results/scurve"):
	t0 = time.time()
	clear_counters()
	clear_counters()
	activate_I2C_chip(verbose = 0)
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

def s_curve_rbr_fr(n_pulse = 1000, s_type = "THR", ref_val = 50, row = range(1,17), step = 1, start = 0, stop = 256, pulse_delay = 200, extract_val = 0, extract = 1, plot = 1, print_file =1, filename = "../cernbox/MPA_Results/scurve_fr_"):
	t0 = time.time()
	try:
		clear_counters(8)
	except ChipsException:
		print "Error ChipsException, repeat ccommand"
		sleep (0.001)
		clear_counters(8)

	row = np.array(row)
	nrow = int(row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((2040, nstep), dtype = np.int16 )
	activate_async()
	if s_type == "THR":	set_calibration(ref_val)
	elif s_type == "CAL":	set_threshold(ref_val)
	else: return "S-Curve type not recognized"
	count = 0
	fc7.write("cnfg_fast_backpressure_enable", 0)
	Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_rst_L1 = 0)
	count = 0
	cur_val = start
	count_err = 0
	failed = 0
	while (cur_val < stop): # Temoporary: need to add clear counter fast command
		if s_type == "CAL":	set_calibration(cur_val)
		elif s_type == "THR":	set_threshold(cur_val)
		utils.ShowPercent(count, (stop-start)/step, "")
		for r in row:
			send_pulses_fast(n_pulse, r, 0, cur_val)
		sleep(0.005)
		fail, temp = ReadoutCounters()
		sleep(0.005)
		if fail and (count_err < 10): # LOOK HERE (exit condition)
			print "FailedPoint, repeat!"
			activate_I2C_chip(verbose = 0)
			count_err += 1
		else:
			data_array [:, count]= temp
			count += 1
			cur_val += step
		if (count_err == 10):
			cur_val = stop
			failed = 1
		try:
			clear_counters(8)
			clear_counters(8)
		except ChipsException:
			print "Error ChipsException, repeat ccommand"
			sleep (0.001)
			clear_counters(8)

	if failed == 1:
		print ("S-Curve extraction failed")
		return "exit at scurve"
	if print_file:
		#CSV.ArrayToCSV (data_array, str(filename) + "_" + s_type + str(ref_val) + ".csv")
		CSV.ArrayToCSV (data_array, str(filename) + "_" + s_type + ".csv")
	if extract:
		if extract_val == 0:
			if s_type == "THR":	extract_val = ref_val*1.66+70
			elif s_type == "CAL":	extract_val = ref_val/1.66-40
		th_array, noise_array = plot_extract_scurve(row = row, pixel = range(1,120), s_type = s_type, scurve = data_array , n_pulse = n_pulse, nominal_DAC = extract_val, start = start, stop = stop, plot = plot, extract = extract)
		t1 = time.time()
		print "END"
		print "Elapsed Time: " + str(t1 - t0)
		plt.show()
		return data_array, th_array, noise_array
	elif plot:
		plot_extract_scurve(row = row, pixel = range(1,120), s_type = s_type, scurve = data_array , n_pulse = n_pulse, nominal_DAC = extract_val, start = start, stop = stop, extract = 0, plot = plot)
	return data_array

# s_curve_pbp_fr(n_pulse = 1000, cal = 100, row = range(1,17), pixel = range(1,120), step = 1, start = 0, stop = 256, pulse_delay = 200,  plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/scurve_fr_"):

def s_curve_pbp_fr(n_pulse = 1000, s_type = "THR", ref_val = 100, row = range(1,17), pixel = range(1,120), step = 1, start = 0, stop = 256, pulse_delay = 200,  extract_val = 110, extract = 0, plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/scurve_fr_"):
	t0 = time.time()
	clear_counters(8)
	clear_counters(8)
	activate_I2C_chip(verbose = 0)
	row = np.array(row)
	nrow = int(row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((2040, nstep), dtype = np.int16 )
	activate_async()
	if s_type == "THR":	set_calibration(ref_val)
	elif s_type == "CAL":	set_threshold(ref_val)
	else: return "S-Curve type not recognized"
	sleep(1)
	fc7.write("cnfg_fast_backpressure_enable", 0)
	Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_rst_L1 = 0)
	count = 0
	cur_val = start
	while (cur_val < stop): # Temoporary: need to add clear counter fast command
		if s_type == "CAL":	set_calibration(cur_val)
		elif s_type == "THR":	set_threshold(cur_val)
		utils.ShowPercent(count, (stop-start)/step, "")
		for r in row:
			for p in pixel:
				send_pulses_fast(n_pulse, r, p, cur_val)
		sleep(0.005)
		fail, temp = ReadoutCounters()
		sleep(0.005)
		if fail:
			print "FailedPoint, repeat!"
		else:
			data_array [:, count]= temp
			count += 1
			cur_val += step
		clear_counters(8)
		clear_counters(8)

	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(ref_val) + ".csv")
	if plot:
		th_array, noise_array = plot_extract_scurve(row = row, pixel = pixel, s_type = s_type, scurve = data_array , n_pulse = n_pulse, nominal_DAC = extract_val, start = start, stop = stop, plot = plot, extract = extract)
		t1 = time.time()
		print "END"
		print "Elapsed Time: " + str(t1 - t0)
		plt.show()
		return data_array, th_array, noise_array
	return data_array

def s_curve_pbp_all(n_pulse = 1000, s_type = "CAL", ref_val = 100, row = range(1,17), pixel = range(1,120), step = 1, start = 0, stop = 256, pulse_delay = 200,  extract_val = 50, plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/scurve_fr_"):
	t0 = time.time()
	clear_counters(8)
	clear_counters(8)
	activate_I2C_chip(verbose = 0)
	row = np.array(row)
	nrow = int(row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((2040, nstep), dtype = np.float16 )
	activate_async()
	if s_type == "THR":	set_calibration(ref_val)
	elif s_type == "CAL":	set_threshold(ref_val)
	else: return "S-Curve type not recognized"
	sleep(1)
	fc7.write("cnfg_fast_backpressure_enable", 0)
	Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_rst_L1 = 0)
	count = 0
	cur_val = start
	while (cur_val < stop): # Temoporary: need to add clear counter fast command
		if s_type == "CAL":	set_calibration(cur_val)
		elif s_type == "THR":	set_threshold(cur_val)
		utils.ShowPercent(count, (stop-start)/step, "")
		#for r in row:
		#	for p in pixel:
		if s_type == "CAL": send_pulses_fast_all(n_pulse, row, pixel, ref_val)
		elif s_type == "THR": #send_pulses_fast_all(n_pulse, row, pixel, cur_val)
			for r in row:
				for p in pixel:
					enable_pix_counter(r,p)
					#enable_pix_disable_ancal(r, p)
			open_shutter()
			sleep(0.01)
			for i in range(0, n_pulse):
				sleep(1)
			sleep(0.001)
			close_shutter()
		sleep(0.005)
		try:
			fail, temp = ReadoutCounters()
			sleep(0.005)
			if fail:
				print "FailedPoint, repeat!"
			else:
				data_array [:, count]= temp
				count += 1
				cur_val += step
		except ChipsException:
			print "Error: Chips Exception"
			sleep(0.01)
		clear_counters(8)
		clear_counters(8)
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_cal_" + str(ref_val) + ".csv")
	if plot:
		th_array, noise_array = plot_extract_scurve(row = row, pixel = pixel, s_type = s_type, scurve = data_array , n_pulse = n_pulse, nominal_DAC = extract_val, start = start, stop = stop, plot = 1, extract = 1)
		#for r in row:
		#	for p in pixel:
		#		plt.plot(range(start,stop), data_array[(r-1)*120+p, 0:(stop-start)],'-')
		#plt.show()
		t1 = time.time()
		print "END"
		print "Elapsed Time: " + str(t1 - t0)
	#	plt.show()
	#	return data_array, th_array, noise_array
	return data_array

def s_curve_pbp_test(n_pulse = 1000, s_type = "CAL", ref_val = 100, primary_row = range(1,17), secondary_row = range(1,17), primary_pixel = range(1,120), secondary_pixel = range(1,120), step = 1, start = 0, stop = 256, pulse_delay = 200,  extract_val = 50, plot = 1):
	t0 = time.time()
	clear_counters(8)
	clear_counters(8)
	activate_I2C_chip(verbose = 0)
	primary_row = np.array(primary_row)
	nrow = int(primary_row.shape[0])
	nstep = (stop-start)/step+1
	data_array = np.zeros((2040, nstep), dtype = np.int16 )
	th_array = np.zeros(2040, dtype = np.int )
	activate_async()
	if s_type == "THR":	set_calibration(ref_val)
	elif s_type == "CAL":	set_threshold(ref_val)
	else: return "S-Curve type not recognized"
	sleep(1)
	fc7.write("cnfg_fast_backpressure_enable", 0)
	Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_rst_L1 = 0)

	# Find Gain
	thDAC = measure_DAC_testblocks(point = 5, bit = 8, step = 32, plot = 0, print_file = 0)
	calDAC = measure_DAC_testblocks(point = 6, bit = 8, step = 32, plot = 0, print_file = 0)
	thLSB = np.mean((thDAC[:,160] - thDAC[:,0])/160)*1000 #LSB Threshold DAC in mV
	calLSB = np.mean((calDAC[:,160] - calDAC[:,0])/160)*0.035/1.768*1000 #LSB Calibration DAC in fC
	th1 = np.zeros(2040, dtype = np.int)
	th2 = np.zeros(2040, dtype = np.int)
	gain = 0
	d1, th1, noise1 = s_curve_pbp_fr(n_pulse = 1000, s_type = "THR", ref_val = 15, row = secondary_row, pixel = secondary_pixel, step = 1, start = 0, stop = 256, pulse_delay = 200,  extract_val = 60, plot = 1, print_file = 0)
	d2, th2, noise2 = s_curve_pbp_fr(n_pulse = 1000, s_type = "THR", ref_val = 40, row = secondary_row, pixel = secondary_pixel, step = 1, start = 0, stop = 256, pulse_delay = 200,  extract_val = 100, plot = 1, print_file = 0)
	Q1 = calLSB * 15
	Q2 = calLSB * 25
	delta_Q = Q2 - Q1
	th1 = [a for a in th1 if a != 0]
	th2 = [a for a in th2 if a != 0]
	gain = thLSB * ((th2[0] - th1[0])/delta_Q)
	print "Gain is ", gain
	count = 0
	cur_val = start
	disable_pixel(0,0)
	for r in primary_row:
		for p in primary_pixel:
			enable_pix_counter(r, p)
	for r in secondary_row:
		for p in secondary_pixel:
			enable_pix_disable_ancal(r,p)
	while (cur_val < stop): # Temoporary: need to add clear counter fast command
		if s_type == "CAL":	set_calibration(cur_val)
		elif s_type == "THR":	set_threshold(cur_val)
		utils.ShowPercent(count, (stop-start)/step, "")
		sleep(0.0025)
		try:
			open_shutter(8)
		except ChipsException:
			print "Error ChipsException, repeat ccommand"
			sleep (0.001)
			open_shutter(8)
		SendCommand_CTRL("start_trigger")
		test = 1
		while (test):
			test = fc7.read("stat_fast_fsm_state")
			sleep(0.001)
		try:
			close_shutter(8)
		except ChipsException:
			print "Error ChipsException, repeat ccommand"
			sleep (0.001)
			close_shutter(8)
		sleep(0.005)
		fail, temp = ReadoutCounters()
		sleep(0.005)
		if fail:
			print "FailedPoint, repeat!"
		else:
			data_array [:, count]= temp
			count += 1
			cur_val += step
		clear_counters(8)
		clear_counters(8)

	t1 = time.time()
	if len(primary_row) == len(secondary_row):
		if primary_row == secondary_row:
			row = primary_row
	else:
		row = np.append(primary_row, secondary_row)
	if len(primary_pixel) == len(secondary_pixel):
		if primary_pixel == secondary_pixel:
			pixel == primary_pixel
	else:
		pixel = np.append(primary_pixel, secondary_pixel)
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	if plot:
		for r in secondary_row:
			for p in secondary_pixel:
				start_DAC = np.argmax(data_array[(r-1)*120+p,:]) + 10
				th_zero = np.argmax(data_array[(r-1)*120+p,:])
				par, cov = curve_fit(errorfc, range(start_DAC, stop), data_array[(r-1)*120+p,start_DAC + 1 :stop + 1], p0= [n_pulse, extract_val, 2])
				th_array[(r-1)*120+p] = int(round(par[1]))
				th_array = [a for a in th_array if a != 0]
				plt.plot(range(0,stop), data_array[(r-1)*120+p,0:stop],'-')
				plt.show()
	charge = (th_array[0] - th_zero)/gain
	print "Injected Charge:", charge, "fC"
	return data_array, th_array

def noise_occupancy(row, pixel, th, time):
	clear_counters(8)
	disable_pixel(0,0)
	enable_pix_disable_ancal(row, pixel)
	n = 0
	data = np.zeros(len(th)+1, dtype = np.int)
	for t in th:
		set_threshold(t)
		open_shutter()
		sleep(time)
		close_shutter()
		data[n] = read_pixel_counter(row, pixel)
		n += 1
		clear_counters(8)
	print data
	ax = sns.heatmap(data, vmin = 0, xticklabels = 5, yticklabels = row)
	plt.show()
	clear_counters(8)
	return data

def reset_trim(value = 15):
	I2C.pixel_write("TrimDAC",0,0,value)
# trimming_noise(nominal_DAC = 70, plot = 1, start = 0, stop = 150, ratio = 3.32, row = [1], pixel = range(1,120))
def trimming_noise(iteration = 1, nominal_DAC = 41, data_array = np.zeros(2040, dtype = np.int ), plot = 1, start = 0, stop = 150, ratio = 3.90, row = range(1,17), pixel = range(1,120)):
	t0 = time.time()
	for r in row:
		I2C.pixel_write("TrimDAC",r,0,15)
	scurve_init = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row, step = 1, start = start, stop = stop, pulse_delay = 200, extract =0, plot = 0, print_file =0)
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
			scurve = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row , step = 1, start = start, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
	t1 = time.time()
	print "END"
	print "Trimming Elapsed Time: " + str(t1 - t0)

	if plot:
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
		scurve_final = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row , step = 1, start = start, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
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
	activate_I2C_chip(verbose = 0)
	for i in range(1,nstep+1):
		I2C.pixel_write("TrimDAC",0,0,0)
		row = range(i, 17, nstep)
		print "Doing Rows: ", row
		data_array = trimming_noise(nominal_DAC = nominal_DAC, data_array = data_array, plot = 0, start = start, stop = stop, ratio = ratio, row = row, pixel = range(1,120))
	for r in range(1,17):
		for p in range(1,120):
			I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])

	if plot:
		scurve = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row , step = 1, start = start, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
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

def trimming_step(pix_out = [["Row", "Pixel", "DAC"]], n_pulse = 1000, s_type = "THR", ref_val = 10, iteration = 1, nominal_DAC = 110, data_array = np.zeros(2040, dtype = np.int ), plot = 1,  stop = 150, ratio = 3.90, row = range(1,17), pixel = range(1,120)):
	t0 = time.time()
	for r in row:
		for p in pixel:
			I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
	try: scurve_init = s_curve_rbr_fr(n_pulse = n_pulse,  s_type = s_type, ref_val = ref_val, row = row, step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
	except TypeError: return
	scurve = scurve_init
	for i in range(0,iteration):
		print ""
		print "Parameter Extraction ", i+1, ":"
		for r in row:
			for p in pixel:
				try:
					if s_type == "THR":
						start_DAC = np.argmax(scurve[(r-1)*120+p,:]) + 10
						par, cov = curve_fit(errorfc, range(start_DAC, stop), scurve[(r-1)*120+p,start_DAC + 1 :stop + 1], p0= [n_pulse, nominal_DAC, 2])
					elif s_type == "CAL":
						start_DAC = 0
						par, cov = curve_fit(errorf, range(start_DAC, stop), scurve[(r-1)*120+p,start_DAC + 1 :stop + 1], p0= [n_pulse, nominal_DAC, 2])
					init_DAC = int(round(par[1]))
					trim_DAC = int(round((nominal_DAC - init_DAC)/ratio))
					curr_dac = I2C.pixel_read("TrimDAC",r,p)
					if s_type == "THR": new_DAC = curr_dac + trim_DAC
					elif s_type == "CAL": new_DAC = curr_dac - trim_DAC
					if (new_DAC > 31):
						if (i == iteration - 1): pix_out.append([r, p , new_DAC])
						new_DAC = 31
						print "High TrimDAC limit for pixel: ", p, " Row: ", r
					if (new_DAC < 0):
						if (i == iteration - 1): pix_out.append([r, p , new_DAC])
						new_DAC = 0
						print "Low TrimDAC limit for pixel: ", p, " Row: ", r
					I2C.pixel_write("TrimDAC", r, p, new_DAC)
					data_array[(r-1)*120+p] = new_DAC
				except RuntimeError or TypeError:
					print "Fitting failed on pixel ", p , " row: " ,r
		if (i != iteration - 1):
			try: scurve = s_curve_rbr_fr(n_pulse = n_pulse, s_type = s_type, ref_val = ref_val, row = row, step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
			except TypeError: return
	if plot:
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])

		try: scurve_final = s_curve_rbr_fr(n_pulse = n_pulse,  s_type = s_type, ref_val = ref_val, row = row, step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
		except TypeError: return
		plt.figure(1)
		th_array, noise_array = plot_extract_scurve(s_type = s_type, scurve = scurve , n_pulse = n_pulse, nominal_DAC = nominal_DAC, start = start, stop = stop, plot = 1, extract = 1)
		t1 = time.time()
		print "END"
		print "Trimming Elapsed Time: " + str(t1 - t0)
		plt.show()
		return data_array, th_array, noise_array, pix_out
	return data_array, pix_out

def trimming_chip(s_type = "THR", ref_val = 10, nominal_DAC = 110, nstep = 4, data_array = np.zeros(2040, dtype = np.int ), n_pulse = 300, iteration = 2, extract = 1, plot = 1, stop = 256, ratio = 3.68, print_file = 0, filename = "../cernbox/MPA_Results/Test"):
	t0 = time.time()
	activate_I2C_chip(verbose = 0)
	pix_out = [["Row", "Pixel", "DAC"]]
	for i in range(1,nstep+1):
		I2C.pixel_write("TrimDAC",0,0,0)
		row = range(i, 17, nstep)
		print "Doing Rows: ", row
		try:
			data_array, pix_out = trimming_step(pix_out = pix_out, n_pulse = n_pulse, s_type = s_type, ref_val = ref_val, iteration = iteration, nominal_DAC = nominal_DAC, data_array = data_array, plot = 0, stop = stop, ratio = ratio, row = row)
		except:
			return
	for r in range(1,17):
		for p in range(1,120):
			I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
	if print_file:
		#CSV.ArrayToCSV (data_array, str(filename) + "_ScCal" + str(nominal_DAC) + ".csv")
		CSV.ArrayToCSV (data_array, str(filename) + "_ScCal" + ".csv")
	if extract:
		scurve = s_curve_rbr_fr(n_pulse = n_pulse,  s_type = s_type, ref_val = ref_val, row = range(1,17), step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
		th_array, noise_array = plot_extract_scurve(row = range(1,17), pixel = range(1,120), s_type = s_type, scurve = scurve , n_pulse = n_pulse, nominal_DAC = nominal_DAC, start = 0, stop = stop, plot = plot, extract = 1)
		print "Pixel not trimmerable: " ,np.size(pix_out)/3-1
		t1 = time.time()
		print "END"
		print "Trimming Elapsed Time: " + str(t1 - t0)
		plt.show()
		if print_file:
			#CSV.ArrayToCSV (data_array, str(filename) + "_trimVal" + str(nominal_DAC) + ".csv")
			#CSV.ArrayToCSV (scurve, str(filename) + "_scurve" + str(nominal_DAC) + ".csv")
			#CSV.ArrayToCSV (th_array, str(filename) + "_th_array" + str(nominal_DAC) + ".csv")
			#CSV.ArrayToCSV (noise_array, str(filename) + "_noise_array" + str(nominal_DAC) + ".csv")
			#CSV.ArrayToCSV (pix_out, str(filename) + "_pix_out" + str(nominal_DAC) + ".csv")
			CSV.ArrayToCSV (data_array, str(filename) + "_trimVal" + ".csv")
			CSV.ArrayToCSV (scurve, str(filename) + "_scurve" + ".csv")
			CSV.ArrayToCSV (th_array, str(filename) + "_th_array" + ".csv")
			CSV.ArrayToCSV (noise_array, str(filename) + "_noise_array" + ".csv")
			CSV.ArrayToCSV (pix_out, str(filename) + "_pix_out" + ".csv")
		return data_array, th_array, noise_array, pix_out

	t1 = time.time()
	print "END"
	print "Trimming Elapsed Time: " + str(t1 - t0)
	return data_array, pix_out

def trimDAC_linearity_rbr(row, pixel = range(1,120), plot = 1, print_file = 0, filename = "../cernbox/MPA_Results/TrimDAC"):
	t0 = time.time()
	activate_I2C_chip(verbose = 0)
	data = np.zeros((2040, 32), dtype = np.int16 )
	I2C.pixel_write("TrimDAC",0,0,31)
	for i in range(0,32):
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,i)
		scurve = s_curve_rbr_fr(n_pulse = 300, cal = 0, row = row,  step = 1, start = 0, stop = 150, pulse_delay = 200, plot = 0, extract = 0, print_file =0)
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
	activate_I2C_chip(verbose = 0)
	data = np.zeros((2040, 32), dtype = np.int16 )
	I2C.pixel_write("TrimDAC",0,0,31)
	for i in range(0,32):
		for r in row:
			for p in pixel:
				I2C.pixel_write("TrimDAC",r,p,i)
		scurve = s_curve_pbp_fr(n_pulse = 300, cal = 0, row = row, pixel = pixel, step = 1, start = 0, stop = 150, pulse_delay = 200, plot = 0, print_file =0)
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
	activate_I2C_chip(verbose = 0)
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
	activate_I2C_chip(verbose = 0)
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
	activate_I2C_chip(verbose = 0)
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

def analyze_scurve(start = 0, stop = 50, plot = 1, filename = "Am-241_tin_long_cal_0.csv"):
	data_array = np.array(CSV.csv_to_array(filename), dtype = np.uint64)
	data_array2 = np.delete(data_array, 0, 0)
	data_array2 = np.delete(data_array2, 0, 1)
	sum_array = np.sum(data_array2, axis = 0)
	if plot:
		#plt.figure(1)
		#plt.plot(range(start,stop), sum_array[0:stop],'-')
		#plt.figure(2)
		for r in range(1,17):
			for p in range(1,120):
				plt.plot(range(0,50),data_array[(r-1)*120+p,start + 1:stop + 1],'-')
		plt.show()
	#return sum_array

def sensor_extract(row = range(1,17), pixel = range(1,120), filter = 1, s_type = "CAL", n_pulse = 200, data_start = 0, extract_start = 0, stop = 50, nominal_DAC = 25, filename = "../cernbox/AutoProbeResults/Wafer_N6T903-05C7/ChipN_2_v0/Scurve15_CAL.csv", bad_file = "../cernbox/AutoProbeResults/Wafer_N6T903-05C7/ChipN_2_v0/Trim15_pix_out.csv"):
	th_array = np.zeros(2160, dtype = np.int)
	noise_array = np.zeros(2160, dtype = np.float)
	badpix = np.zeros(shape=(0,2))
	n = 0
	data = CSV.csv_to_array(filename)
	badpixels = CSV.csv_to_array(bad_file)
	badpixels = np.delete(badpixels, 0, 0)
	badpixels = badpixels.astype('int')
	data = data.astype('int')
	for r in row:
		for p in pixel:
			flag = 0
				#if filter == 1:
				#	for a in badpixels[0:badpixlength, 0]:
				#		if r == badpixels[(a-1), 1]:
				#			if p == badpixels[(a-1), 2]:
				#				flag = 1
				#if flag != 1:
			try:
				if s_type == "THR":
					par, cov = curve_fit(errorfc, range(extract_start - data_start, stop - data_start), data[(r-1)*120+p, (extract_start - data_start) + 1 :(stop - data_start) + 1], p0= [n_pulse, (nominal_DAC - data_start), 2])
				elif s_type == "CAL":
					par, cov = curve_fit(errorf, range(extract_start - data_start, stop - data_start), data[(r-1)*120+p, (extract_start - data_start) + 1 :(stop - data_start) + 1], p0= [n_pulse, (nominal_DAC - data_start), 2])
			except RuntimeError or TypeError:
				badpix = np.append(badpix, [[r, p]], axis = 0)
				flag = 1
			try:
				plt.figure(1)
				plt.plot(range(0,50),data[(r-1)*120+p,data_start + 1:stop + 1],'-')
				if cov[0,2] > 1.0 or cov[0,2] < 0 or np.max(data[(r-1)*120+p, 1 : stop]) > n_pulse:
					badpix = np.append(badpix, [[r, p]], axis = 0)
				elif flag != 1:
					th_array[(r-1)*120+p] = int(round(par[1])) + data_start
					noise_array[(r-1)*120+p] = par[2]
					plt.figure(1)
					plt.plot(range(0,50),data[(r-1)*120+p,data_start + 1:stop + 1],'-')
			except TypeError:
				if np.isinf(cov):
					badpix = np.append(badpix, [[r, p]], axis = 0)
				else:
					print "Check pixel ", p, "in row ", r, ". Something bad happened. Error: TypeError"
				#if r == 10 and p == 50:
					#print data[(r-1)*120+p]
				#	plt.figure(3)
				#	plt.plot(range(data_start, stop), (data[((r-1)*120+p), 1:(stop - data_start + 1)]), 'o', label = "Data")
				#	plt.plot(range(extract_start, stop), errorfc(range(extract_start - data_start, stop - data_start), *par), 'o', label ='Fit')
				#	plt.legend()
	#sumarray = analyze_scurve(start = 0, stop = (stop - extract_start), plot = 0, filename = filename)
	#print sumarray
	#print len(sumarray)
	#print len(range(extract_start - data_start, stop - data_start))
	#par, cov = curve_fit(errorfc, range(extract_start - data_start, stop - data_start), sumarray[(extract_start - data_start):(stop - data_start)], p0= [900000 , (nominal_DAC - data_start), 2])
	#print "par = ", par
	#print "cov = ", cov
	th_sum = int(round(par[1])) + data_start
	th_array = [a for a in th_array if a != 0]
	noise_array = [b for b in noise_array if b != 0]
	badpix.astype('int')
	#print "Threshold Average: ", np.mean(th_array)
	#print "Threshold Spread: ", np.std(th_array)
	#print "Noise Average: ", np.mean(noise_array)
	#print "Noise Spread: ", np.std(noise_array)
	#print "Sum Threshold: ", th_sum
	#plt.figure(2)
	#plt.title("Threshold")
	#plt.hist(th_array[1:1920], bins=range(min(th_array), max(th_array) + 1, 1))
	#plt.figure(3)
	#plt.title("Noise")
	#plt.hist(noise_array, bins=np.arange(min(noise_array), max(noise_array) + 1 , 0.1))
	#plt.figure(4)
	#plt.title("Sum")
	#plt.plot(range(data_start, stop), sumarray[0: (stop - data_start)])
	#plt.plot(range(extract_start, stop), errorfc(range(extract_start - data_start, stop - data_start), *par))
	#plt.show()
	return np.std(th_array), np.mean(noise_array), badpix

def analyze_chip(wafer_name = "Wafer_N6T903-05C7"):
	thsd = np.zeros(90)
	noise_avg = np.zeros(90)
	#bad_pixels = np.zeros(shape = (1,2))
	bad_array = ['Bad Pixels']
	for n in range(1,89):
		try:
			thsd[n], noise_avg[n], bad_pixels = sensor_extract(row = range(1,17), pixel = range(1,120), s_type = "CAL", n_pulse = 200, data_start = 0, extract_start = 0, stop = 50, nominal_DAC = 25, filename = "../cernbox/AutoProbeResults/"+wafer_name+"/ChipN_"+str(n)+"_v0/Scurve15_CAL.csv")
			bad_array.append(bad_pixels)
		except IOError:
			print "Chip", n, "had an accident"
			bad_array.append([['Chip Failure'], [n]])
	thsd = [a for a in thsd if a != 0]
	noise_avg = [b for b in noise_avg if b != 0]
	plt.figure(1)
	plt.title("Threshold Spread")
	plt.hist(thsd, bins=np.arange(min(thsd), max(thsd) + 1, 0.1))
	plt.figure(2)
	plt.title("Noise Average")
	plt.hist(noise_avg, bins=np.arange(min(noise_avg), max(noise_avg) + 0.2 , 0.01))
	plt.show()
	return bad_array

def trim_DAC_noise(row = range(1,17), pixel = range(1,120)):
	par_array = np.zeros(shape=(2040, 3))
	data_array = np.zeros(shape = (2040, 251), dtype = np.int)
	n = 0
	for r in row:
		print "\nStarting row ", r, "\n"
		for p in pixel:
			I2C.pixel_write("TrimDAC", 0, 0, 0)
			sleep(0.1)
			I2C.pixel_write("TrimDAC", r, p, 31)
			sleep(0.1)
			data = s_curve_pbp_all(n_pulse = 200, s_type = "THR", ref_val = 0, row = [r], pixel = [p], step = 1, start = 0, stop = 250, pulse_delay = 200,  extract_val = 200, plot = 0, print_file = 0)
			sleep(0.1)
			try:
				par, cov = curve_fit(gauss, range(0, 200), data[(r-1)*120 + p, 1: 201], p0= [np.max(data[(r-1)*120 + p]), np.argmax(data[(r-1)*120 + p]), 2])
				par_array[n] = par
				data_array[n] = data[(r-1)*120 + p]
			except RuntimeError or TypeError:
				print "Fitting failed on pixel ", p , " row: " ,r
				par_array[n] = [0,0,0]
			n += 1
	CSV.ArrayToCSV(par_array, filename = "NoisePeak_Par.csv")
	CSV.ArrayToCSV(data_array, filename = "NoisePeak_Data.csv")
	return par_array, data_array
