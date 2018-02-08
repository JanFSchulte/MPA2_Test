from myScripts.BasicMultimeter import *
from cal_utility import *

def set_measurement(name = "none"):
	# set all zeros now
	I2C.peri_write("Bias_TEST_LSB", 0)
        I2C.peri_write("Bias_TEST_MSB", 0)
	
	# now set whatever you want
	if name == "none":
		pass
	elif name == "D5BFEED":
		I2C.peri_write("Bias_TEST_LSB", 0b00000001)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "D5PREAMP":
		I2C.peri_write("Bias_TEST_LSB", 0b00000010)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "D5TDR":
		I2C.peri_write("Bias_TEST_LSB", 0b00000100)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "D5ALLV":
		I2C.peri_write("Bias_TEST_LSB", 0b00001000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "D5ALLI":
		I2C.peri_write("Bias_TEST_LSB", 0b00010000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "CALDAC":
		I2C.peri_write("Bias_TEST_LSB", 0b00100000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "BOOSTERBASELINE":
		I2C.peri_write("Bias_TEST_LSB", 0b01000000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "THDAC":
		I2C.peri_write("Bias_TEST_LSB", 0b10000000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000000)
	elif name == "THDACHIGH":
		I2C.peri_write("Bias_TEST_LSB", 0b00000000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000001)
	elif name == "D5DAC8":
		I2C.peri_write("Bias_TEST_LSB", 0b00000000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000010)
	elif name == "VBG":
		I2C.peri_write("Bias_TEST_LSB", 0b00000000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00000100)
	elif name == "GND":
		I2C.peri_write("Bias_TEST_LSB", 0b00000000)
        	I2C.peri_write("Bias_TEST_MSB", 0b00001000)
	else:
		print "Error. Wrong name"
	
def d5_value(name, mode = 'r', value = -1):
	# check the read value
	if ((mode == 'w') & (value == -1)):
		print "Error! Can not use default value for writing. Please set the value"
		exit(1)        

	# write now	
	if (mode == 'w'):
		I2C.peri_write(name, value)

	# read back
	read_value = I2C.peri_read(name)

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
		
def get_value_and_voltage(name, inst0 = -1):
	# get instrument
	if (inst0 == -1):
		inst = init_keithley()
	else:
		inst = inst0
	# demux the line
	set_measurement(name)
	# read value
	value = d5_value('Bias_'+str(name), 'r')
	measurement = measure(inst)
	# return	
	return value, measurement

def tune_parameter(inst, name, nominal):
	if (nominal == -1):
		return

	# check initials
	dac_value, voltage = get_value_and_voltage(name, inst)
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
		d5_value('Bias_'+str(name), 'w', dac_value)
		# measure
		voltage = 1E3*measure(inst)
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
	d5_value('Bias_'+str(name), 'w', best_dac_value)
	dac_value, voltage = get_value_and_voltage(name, inst)
	print "\t\tBest Set: ", dac_value, 1E3*voltage

	return best_dac_value

def check_nominals():
	# init keithley
	inst = init_keithley()
	# for simplicity define a par class
	class Parameter:
		def __init__(self, full_name, par_name, nominal = -1, best_dac = -1):
			self.full_name = full_name
			self.par_name = par_name
			self.nominal = nominal
			self.best_dac = best_dac
	# define the pars
	par_list = [Parameter("Booster Feedback Bias", "D5BFEED", 82.0), Parameter("Preamplifier Bias", "D5PREAMP", 82.0), Parameter("TRIM DAC range", "D5TDR", 115.0), Parameter("DAC for voltage biases","D5ALLV", 82.0), Parameter("DAC for current biases","D5ALLI", 82.0), Parameter("Threshold DAC", "THDAC", 622.0), Parameter("Threshold High DAC", "THDACHIGH", 622.0), Parameter("Calibration DAC", "CALDAC", 100.0), Parameter("DAC for threshold and calibration", "D5DAC8", 86.0)]

	# iterate and measure
	for par in par_list:
		value, voltage = get_value_and_voltage(par.par_name, inst)
		voltage = voltage*1E3
		print par.full_name, ": "
		print "\tCheck the initial value: "
		print ("\t\t DAC: %4d\t V: %8.3f mV") % (value, voltage)
		print "\tTune the value (", par.nominal, "):"
		best_dac = tune_parameter(inst, par.par_name, par.nominal)
		par.best_dac = best_dac

	print "\n\nSummary of tuning (tuned values):"
	for par in par_list:
		value, voltage = get_value_and_voltage(par.par_name, inst)
		voltage = voltage*1E3
		print par.full_name, ": "
		print ("\t Best DAC: %4d,\t V: %8.3f mV") % (value, voltage)
		

def measure_vth_linearity():
	inst = init_keithley(3)
	activate_I2C_chip()
	
	# demux the line
	I2C.peri_write("Bias_TEST_LSB", 0b10000000)
	I2C.peri_write("Bias_TEST_MSB", 0)	
	
	#array
	data = np.zeros(256, dtype=np.float);

	# do the measurement
	for i in range(0, 256):
		#set_threshold(i)
		I2C.peri_write("Bias_THDAC", i)
		sleep(0.1)
		data[i] = measure(inst)
		if (i % 10 == 0):
			print "Done point ", i, " of ", 256

	return data
