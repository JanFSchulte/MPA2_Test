from fc7_daq_methods import *

#####################
# START HERE
#####################
SendCommand_CTRL("global_reset")
sleep(1)

################
#change the phase of the fast_cmd wrt the 320MHz clock going to the chip:
#fc7.write("ctrl_phy_fast_cmd_phase",x)

#change the phase of the fake L1 data going to the MPA wrt the 320MHz clock going to the chip:
#fc7.write("ctrl_phy_ssa_gen_trig_phase",x)

#change the phase of the fake stub data going to the MPA wrt the 320MHz clock going to the chip. All 8 lines are phase shifted with the same amount:
#fc7.write("ctrl_phy_ssa_gen_stub_phase",x)

#register to change the data content of the L1 data send by the SSA data generator. See tables in the manual on what to expect:
#fc7.write("cnfg_phy_SSA_gen_trig_data_format",x)

#register to change the data content of the stub data send by the SSA data generator. See tables in the manual on what to expect:
#fc7.write("cnfg_phy_SSA_gen_stub_data_format",x)

#register to change the delay (expressed in 25ns) imposed on sending the generated SSA L1 data wrt to the trigger signal:
#fc7.write("cnfg_phy_SSA_gen_delay_trig_data",x)

#register to change the delay (expressed in 25ns) imposed on sending the generated SSA stub data wrt to the Cal_strobe signal:
#fc7.write("cnfg_phy_SSA_gen_delay_stub_data",x)

################


i = 0
while True:
	#SSA like stub data sending is
	#SendCommand_CTRL("fast_trigger")
	SendCommand_CTRL("fast_test_pulse")
	#fc7.write("ctrl_phy_ssa_gen_stub_phase",1)
	if(i%1000  == 0 and i != 0):
		fc7.write("cnfg_phy_SSA_gen_delay_stub_data", i/1000)
		print("shifted")
	sleep(0.001)
	i = i +1
	print(i)
