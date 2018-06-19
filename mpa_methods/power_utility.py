#from mpa_methods.set_calibration import *
#send_cal_pulse(127, 150, range(1,2), range(1,5))
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.cal_utility import *
from mpa_methods.fast_readout_utility import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
#from mpa_methods.bias_calibration import *
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm

def power_occupancy(th = range(77,100), plot = 1, print_file =1, filename = "../cernbox/MPA_Results/PowerVsOccupancy"):
	read = 1
	write = 0
	cbc3 = 15
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1
	th = np.array(th)
	nth = int(th.shape[0])
	data_array = np.zeros((nth, 2), dtype = np.float16 )
	for i in range(0, nth):
		activate_I2C_chip(verbose = 0)
		set_threshold(th[i])
		send_test()
		nst, pos, bend, Z = read_stubs()
		data_array[i, 0] = np.average(nst[0:19])
		sleep(5)
		SetSlaveMap()
		Configure_MPA_SSA_I2C_Master(1, SLOW)
		Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
		sleep(1)
		ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt

		print ret
		data_array[i, 1] = (Vcshunt * ret)/Rshunt

	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) +  ".csv")
	if plot:
		plt.plot(data_array[:,0], data_array[:,1],'o')
		plt.xlabel('Threshold DAC value')
		plt.ylabel('Counter Value')
		plt.show()
def power_memory(row = range(1,17), plot = 1, print_file =1, filename = "../cernbox/MPA_Results/PowerVsMemory"):
	read = 1
	write = 0
	cbc3 = 15
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1
	row = np.array(row)
	nrow = int(row.shape[0])
	data_array = np.zeros((nrow+1, ), dtype = np.float16 )
	activate_I2C_chip(verbose = 0)
	I2C.row_write('MemGatEn', 0 , 0b1)
	sleep(5)
	SetSlaveMap()
	Configure_MPA_SSA_I2C_Master(1, SLOW)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
	sleep(1)
	ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt
	print ret
	data_array[0] = (Vcshunt * ret)/Rshunt
	for i in row:
		activate_I2C_chip(verbose = 0)
		I2C.row_write('MemGatEn', i , 0b0)
		sleep(5)
		SetSlaveMap()
		Configure_MPA_SSA_I2C_Master(1, SLOW)
		Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
		sleep(1)
		ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt

		print ret
		data_array[i] = (Vcshunt * ret)/Rshunt

	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) +  ".csv")
	if plot:
		plt.plot(data_array,'o')
		plt.xlabel('# of active memory')
		plt.ylabel('Power consumption [mW]')
		plt.show()

def mpa_reset():
	read = 1
	write = 0
	cbc3 = 15
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1
	SetSlaveMap(verbose = 0)
	print "MPA reset"
	val = (mpaid << 5) + (ssaid << 1)
	val2 = (mpaid << 5) + (ssaid << 1) + 16 # reset bit for MPA
	Configure_MPA_SSA_I2C_Master(1, SLOW)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02, verbose = 0)  # route to 2nd PCF8574
	Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val, verbose = 0)  # drop reset bit
	Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2, verbose = 0)  # set reset bit

def set_power(address, V):
	read = 1
	write = 0
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1
	SetSlaveMap(verbose = 0)
	Vlimit = 1.32
	if (V > Vlimit):
		V = Vlimit
	diffvoltage = 1.5 - V
	setvoltage = int(round(diffvoltage / Vc))
	if (setvoltage > 4095):
		setvoltage = 4095
	setvoltage = setvoltage << 4
	Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01, verbose = 0)  # to SCO on PCA9646
	Send_MPA_SSA_I2C_Command(dac7678, 0, write, address, setvoltage, verbose = 0)  # tx to DAC C

# mpavddDwrite():
def set_DVDD(V = 1.0):
	set_power( address = 0x30, V = V)
	print "DVDD --> ", V	, " V"

def set_AVDD(V = 1.25):
	set_power( address = 0x32, V = V)
	print "AVDD --> ", V	, " V"

def set_VDDPST(V = 1.25):
	set_power( address = 0x34, V = V)
	print "VDDPST --> ", V	, " V"

def power_on(VDDPST = 1.25, DVDD = 1.2, AVDD = 1.25, VBG = 0.3):
	read = 1
	write = 0
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1

	SetSlaveMap(verbose = 0)
# mpavddwrite():
	set_VDDPST(V = VDDPST)
	sleep(2)
	set_DVDD(V = DVDD)
	sleep(2)
	set_AVDD(V = AVDD)

# bgtestwrite():
	Vlimit = 0.5
	if (VBG > Vlimit):
		VBG = Vlimit
	Vc2 = 4095/1.5
	setvoltage = int(round(VBG * Vc2))
	setvoltage = setvoltage << 4
	Configure_MPA_SSA_I2C_Master(1, SLOW)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01, verbose = 0)  # to SCO on PCA9646
	Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x36, setvoltage, verbose = 0)  # tx to DAC C
	sleep(2)
# mpaenable():
	val2 = (mpaid << 5) + 16 # reset bit for MPA
	Configure_MPA_SSA_I2C_Master(1, SLOW)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02, verbose = 0)  # route to 2nd PCF8574
	Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2, verbose = 0)  # set reset bit



def measure_current(print_file = 1, filename =  "../cernbox/MPA_Results/digital_pixel_test.log"):

	if print_file:
		f = open(filename, 'w')
	read = 1
	write = 0
	cbc3 = 15
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1

	SetSlaveMap()
# readVDDPST
	Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
	sleep(1)
	ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x01, 0, verbose = 0)  #read VR on shunt
	message = "VDDPST current: " + str((Vcshunt * ret)/Rshunt) + " mA"
	print message
	f.write(message)
# readDVDD
	Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
	sleep(1)
	ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
	message = "DVDD current: " + str((Vcshunt * ret)/Rshunt) + " mA"
	print message
	f.write(message)
# readAVDD
	Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
	sleep(1)
	ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
	message = "AVDD current: " + str((Vcshunt * ret)/Rshunt) + " mA"
	print message
	f.write(message)
	f.close()

def power_off():
	read = 1
	write = 0
	cbc3 = 15
	FAST = 4
	SLOW = 2
	mpaid = 0 # default MPa address (0-7)
	ssaid = 0 # default SSa address (0-7)
	i2cmux = 0
	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
	powerenable = 2    # i2c ID 0x44
	dac7678 = 4
	ina226_5 = 5
	ina226_6 = 6
	ina226_7 = 7
	ina226_8 = 8
	ina226_9 = 9
	ina226_10 = 10
	ltc2487 = 3
	Vc = 0.0003632813 # V/Dac step
	#Vcshunt = 5.0/4000
	Vcshunt = 0.00250
	Rshunt = 0.1

	SetSlaveMap(verbose = 0)

# mpadisable():
	val = (mpaid << 5) + (ssaid << 1) # reset bit for MPA
	Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02, verbose = 0)  # route to 2nd PCF8574
	Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val, verbose = 0)  # set reset bit
	sleep(2)

# bgtestwrite():
	setvoltage = 0
	setvoltage = setvoltage << 4
	Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
	Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01, verbose = 0)  # to SCO on PCA9646
	Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x36, setvoltage, verbose = 0)  # tx to DAC C
	sleep(2)
	set_AVDD(V = 0)
	sleep(2)
	set_DVDD(V = 0)
	sleep(2)
	set_VDDPST(V = 0)


def set_nominal():
	set_VDDPST(V = 1.25)
	sleep(1)
	set_DVDD(V = 1.25)
	sleep(1)
	set_AVDD(V = 1.25)
	mpa_reset()
	activate_I2C_chip(verbose = 0)
	activate_sync()
	activate_ps()
	I2C.row_write('MemGatEn',0,0)
	I2C.peri_write('ConfSLVS', 0b00111111)
	set_threshold(110)
	set_calibration(0)
