from fc7_daq_methods import *

SendCommand_CTRL("global_reset")
sleep(1)


ddr3_status = fc7.read("stat_ddr3_initial_calibration_done")
print "[info]: ddr3|init status        ->",ddr3_status

if ddr3_status==1:
	# start bist
	fc7.write("ctrl_ddr3_traffic_str", 0x01)
	#
	self_check_done = fc7.read("stat_ddr3_self_check_done")	
	while(not self_check_done):
		print "Waiting for self check to finish"
		self_check_done = fc7.read("stat_ddr3_self_check_done")	
		sleep(0.1)
	#
	nb_of_err = fc7.read("stat_ddr3_num_errors")
	print "[info]: ddr3|bist nbr of errors ->",nb_of_err
	#
	nb_of_wrd = fc7.read("stat_ddr3_num_words")
	print "[info]: ddr3|bist nbr of words  ->",nb_of_wrd

	if nb_of_err==0: 
		print "[TEST]: ddr3               -> /PASS/"
	else:
		print "[TEST]: ddr3               -> /FAIL/"

else:
	print "[TEST]: ddr3               -> /FAIL/"
