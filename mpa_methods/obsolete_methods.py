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
		print "Try with finer step"
	else:
		print "All stubs line aligned!"
	t1 = time.time()
	print "Elapsed Time: " + str(t1 - t0)


## Test method. Problem solved in Firmware
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
