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

#registers to change the data content of the L1 data send by the SSA data generator. 
#fc7.write("cnfg_phy_SSA_gen_l1_data_format_0",x) --channel data 119 until 96, so 8 MSBs are not used in this register
#fc7.write("cnfg_phy_SSA_gen_l1_data_format_1",x) --channel data 95 downto 64 
#fc7.write("cnfg_phy_SSA_gen_l1_data_format_2",x) --channel data 63 downto 32
#fc7.write("cnfg_phy_SSA_gen_l1_data_format_3",x) --channel data 31 downto 0
#fc7.write("cnfg_phy_SSA_gen_HIP_data_format",x)  --HIP flags

#register to change the offset value of the BX counter of the L1 data send by the SSA data generator. After a resync = fast reset this counter comes to the value defined below. After a reset of the FW the counter starts at 1. So in general this BX counter  starts counting at 1, increments by 1 when it receives a trigger, is set to the value specified below when it receives a resync.
#fc7.write(cnfg_phy_SSA_gen_offset_SSA_BX_cnt_format,x)

#register to change the data content of the stub data send by the SSA data generator. What you put here as x and y will be put on the stub data line. For every line (there are 8 in total) you can configure an event which is 64 bits long, so this is 8 25ns clock cycles. For the first stub line the interesting registers are (the MSB from reg0 will be outputted first): 
#fc7.write("cnfg_phy_SSA_gen_stub_data_format_0_0",x)
#fc7.write("cnfg_phy_SSA_gen_stub_data_format_0_1",y)
#if x = b1000000 &  0x000000 and y = = b1100000 & 0x000000 you should get the same on the line: b1000000 &  0x000000 & b1100000 & 0x000000 with the MSB the first bit in time

#register to change the delay (expressed in 25ns) imposed on sending the generated SSA L1 data wrt to the trigger signal:
#fc7.write("cnfg_phy_SSA_gen_delay_trig_data",x)

#register to change the delay (expressed in 25ns) imposed on sending the generated SSA stub data wrt to the Cal_strobe signal:
#fc7.write("cnfg_phy_SSA_gen_delay_stub_data",x)

#SSA only:
#register to change the content of the left SSA lateral data content. The left lateral data contents 8 bits will consist out of these values
#fc7.write("cnfg_phy_SSA_gen_left_lateral_data_format",x)
#register to change the content of the right SSA lateral data content. The right lateral data contents 8 bits will consist out of these values
#fc7.write("cnfg_phy_SSA_gen_right_lateral_data_format",x)
#register to change the delay (expressed in 25ns) imposed on sending the generated SSA lateral data wrt to the trigger signal:
#fc7.write("cnfg_phy_SSA_gen_delay_lateral_data",x)
#change the phase of the lateral data going to the SSA wrt the 320MHz clock going to the chip. Both lines are phase shifted with the same amount:
#fc7.write("ctrl_phy_ssa_gen_lateral_phase",x)
################


i = 0
while True:
	#SSA like stub data sending is 
	SendCommand_CTRL("fast_trigger")
	SendCommand_CTRL("fc7_daq_ctrl.fast_command_block.control.fast_test_pulse")
	fc7.write("cnfg_phy_SSA_gen_stub_data_format_0_0", 176) # d176 = b10110000
	#fc7.write("ctrl_phy_ssa_gen_stub_phase",1)
	#if(i%1000  == 0 and i != 0):
	#	fc7.write("cnfg_phy_SSA_gen_delay_stub_data", i/1000)
	#	print("shifted")
	sleep(0.001)
	i = i +1
	print(i)

