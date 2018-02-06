from myScripts.BasicMultimeter import *
from cal_utility import *

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
		set_threshold(i)
		data[i] = measure(inst)
		if (i % 10 == 0):
			print "Done point ", i, " of ", 256

	return data
