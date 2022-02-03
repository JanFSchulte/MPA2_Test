from fc7_daq_methods import *
SendCommand_CTRL("global_reset")
sleep(1)

#configure the IDELAY setting
IDELAY_tap_value = 1
data_taking_done = 1 #after every datataking this bit flips, so the next data is ready when this bit is different then the previous one

for i in range(0,30):
	print("---------------------------------------")
	fc7.write("cnfg_phy_EYE_SCAN_CNTVALUEIN_idelay_eye",i) #configure the delay and then wait a bit
	sleep(0.5)
	fc7.write("ctrl_phy_EYE_SCAN_load_idelay_eye",1)

	fc7_data_taking_done = fc7.read("stat_phy_eye_scan_idelay_data_taking_done")
	#print("fc7_data_taking_done: ", fc7_data_taking_done, " expecting: ", data_taking_done)

	#read the register bit that says the data is ready:
	while fc7_data_taking_done != data_taking_done:
	#	print "Waiting for the data at point ", i
	        fc7_data_taking_done = fc7.read("stat_phy_eye_scan_idelay_data_taking_done")
	#	print("fc7_data_taking_done: ", fc7_data_taking_done, " expecting: ", data_taking_done)
		sleep(0.5)

	#print("data_taking_done: ", data_taking_done)
	data_taking_done = 1 - data_taking_done #toggle between 1 and 0
	#read the data
	data_single_tap_setting = bin(fc7.read("stat_phy_eye_scan_idelay_data_one_sampling_point"))
#	print data_single_tap_setting
	print "number of 1's at point ", i, ": ", data_single_tap_setting.count("1")

