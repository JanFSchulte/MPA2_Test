# OBSOLETE - Start Counter readout old method
def StartCountersRead():
    encode_fast_reset = fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(1)
    encode_orbit_reset = fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(1)
    fc7.write("ctrl_fast", encode_fast_reset + encode_orbit_reset)

### Old alignment method - Keep as BackUp
def alignment_slvs(align_word = 128, step = 10):
	t0 = time.time()
	activate_I2C_chip()
	I2C.peri_write('LFSR_data', align_word)
	activate_shift()
	phase = 0
	fc7.write("ctrl_phy_fast_cmd_phase",phase)
	aligned = 0
	count = 0
	while ((not aligned) or (count <= (168/step))):
		send_test()
		send_trigger()
		array_stubs = read_stubs(1)
		array_l1 = read_L1()
		aligned = 1
		for word in array_stubs[:,0]: # CHheck stub lines alignment
			if (word != align_word):
				aligned = 0
		if (array_l1[0,0] != align_word): # CHheck L1 lines alignment
			aligned = 0
		if (not aligned): # if not alignment change phase with T1
			phase += step
			fc7.write("ctrl_phy_fast_cmd_phase",phase)
		count += 1
	if (not aligned):
		print("Try with finer step")
	else:
		print("All stubs line aligned!")
	t1 = time.time()
	print("Elapsed Time: " + str(t1 - t0))


## Test method. Problem solved in Firmware
def check_clear_counters(change = 1, points = 168, iterations = 10, duration = 8):
	count = 0
	for i in range(0,points):
		for j in range(0,iterations):
			hit_map(10, 250, 200, [1], [7])
			sleep(0.001)
			value = read_pixel_counter(1,7)
			if (value != 10):
				print(str(i) + " " + str(j) + " " + str(value))
				count += 1
			clear_counters(duration)
			sleep(0.001)
			value = read_pixel_counter(1,7)
			if (value != 0):
				print(str(i) + " " + str(j) + " " + str(value))
				count += 1
		if change: fc7.write("ctrl_phy_fast_cmd_phase",1)
	return count
#### NOT USED TRIM OR SCURVE:
def analyze_chip(wafer_name = "Wafer_N6T903-05C7"):
	thsd = np.zeros(90)
	noise_avg = np.zeros(90)
	#bad_pixels = np.zeros(shape = (1,2))
	bad_array = ['Bad Pixels']
	for n in range(1,89):
		try:
			thsd[n], noise_avg[n], bad_pixels = sensor_extract(row = list(range(1,17)), pixel = list(range(1,120)), s_type = "CAL", n_pulse = 200, data_start = 0, extract_start = 0, stop = 50, nominal_DAC = 25, filename = "../cernbox/AutoProbeResults/"+wafer_name+"/ChipN_"+str(n)+"_v0/Scurve15_CAL.csv")
			bad_array.append(bad_pixels)
		except IOError:
			print("Chip", n, "had an accident")
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

def trim_DAC_noise(row = list(range(1,17)), pixel = list(range(1,120))):
	par_array = np.zeros(shape=(2040, 3))
	data_array = np.zeros(shape = (2040, 251), dtype = np.int)
	n = 0
	for r in row:
		print("\nStarting row ", r, "\n")
		for p in pixel:
			I2C.pixel_write("TrimDAC", 0, 0, 0)
			sleep(0.1)
			I2C.pixel_write("TrimDAC", r, p, 31)
			sleep(0.1)
			data = s_curve_pbp_all(n_pulse = 200, s_type = "THR", ref_val = 0, row = [r], pixel = [p], step = 1, start = 0, stop = 250, pulse_delay = 200,  extract_val = 200, plot = 0, print_file = 0)
			sleep(0.1)
			try:
				par, cov = curve_fit(gauss, list(range(0, 200)), data[(r-1)*120 + p, 1: 201], p0= [np.max(data[(r-1)*120 + p]), np.argmax(data[(r-1)*120 + p]), 2])
				par_array[n] = par
				data_array[n] = data[(r-1)*120 + p]
			except RuntimeError or TypeError:
				print("Fitting failed on pixel ", p , " row: " ,r)
				par_array[n] = [0,0,0]
			n += 1
	CSV.ArrayToCSV(par_array, filename = "NoisePeak_Par.csv")
	CSV.ArrayToCSV(data_array, filename = "NoisePeak_Data.csv")
	return par_array, data_array

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
				plt.plot(list(range(0,50)),data_array[(r-1)*120+p,start + 1:stop + 1],'-')
		plt.show()
	#return sum_array

def sensor_extract(row = list(range(1,17)), pixel = list(range(1,120)), filter = 1, s_type = "CAL", n_pulse = 200, data_start = 0, extract_start = 0, stop = 50, nominal_DAC = 25, filename = "../cernbox/AutoProbeResults/Wafer_N6T903-05C7/ChipN_2_v0/Scurve15_CAL.csv", bad_file = "../cernbox/AutoProbeResults/Wafer_N6T903-05C7/ChipN_2_v0/Trim15_pix_out.csv"):
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
					par, cov = curve_fit(errorfc, list(range(extract_start - data_start, stop - data_start)), data[(r-1)*120+p, (extract_start - data_start) + 1 :(stop - data_start) + 1], p0= [n_pulse, (nominal_DAC - data_start), 2])
				elif s_type == "CAL":
					par, cov = curve_fit(errorf, list(range(extract_start - data_start, stop - data_start)), data[(r-1)*120+p, (extract_start - data_start) + 1 :(stop - data_start) + 1], p0= [n_pulse, (nominal_DAC - data_start), 2])
			except RuntimeError or TypeError:
				badpix = np.append(badpix, [[r, p]], axis = 0)
				flag = 1
			try:
				plt.figure(1)
				plt.plot(list(range(0,50)),data[(r-1)*120+p,data_start + 1:stop + 1],'-')
				if cov[0,2] > 1.0 or cov[0,2] < 0 or np.max(data[(r-1)*120+p, 1 : stop]) > n_pulse:
					badpix = np.append(badpix, [[r, p]], axis = 0)
				elif flag != 1:
					th_array[(r-1)*120+p] = int(round(par[1])) + data_start
					noise_array[(r-1)*120+p] = par[2]
					plt.figure(1)
					plt.plot(list(range(0,50)),data[(r-1)*120+p,data_start + 1:stop + 1],'-')
			except TypeError:
				if np.isinf(cov):
					badpix = np.append(badpix, [[r, p]], axis = 0)
				else:
					print("Check pixel ", p, "in row ", r, ". Something bad happened. Error: TypeError")
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
