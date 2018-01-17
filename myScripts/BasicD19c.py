from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
#####################
# START HERE
#####################
#SendCommand_CTRL("global_reset")
#sleep(1)

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


def reverse_mask(x):
    x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
    x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
    x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
    x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
    x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
    return x

##----- begin main

def read_regs():
    status = fc7.read("stat_slvs_debug_general")
    mpa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
    mpa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)

    print "--> Status: "
    print "---> MPA L1 Data Ready: ", ((status & 0x00000001) >> 0)
    print "---> MPA Stub Data Ready: ", ((status & 0x00000002) >> 1)
    print "---> MPA Counters Ready: ", ((status & 0x00000004) >> 2)

    print "\n--> L1 Data: "
    for word in mpa_l1_data:
        print "--->", '%10s' % bin(to_number(reverse_mask(word),32,24)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),8,0)).lstrip('-0b').zfill(8)

    print "\n--> Stub Data: "
    for word in mpa_stub_data:
        print "--->", '%10s' % bin(to_number(reverse_mask(word),32,24)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),8,0)).lstrip('-0b').zfill(8)

def send_trigger():
    SendCommand_CTRL("fast_trigger")

def send_test():
    SendCommand_CTRL("fast_test_pulse")

def reset():
    SendCommand_CTRL("global_reset")

def write_I2C (chip, address, data, frequency = 4):
    i2cmux = 0
    MPA = 11
    SSA = 12
    write = 0
    read = 1
    SetSlaveMap()
    Configure_MPA_SSA_I2C_Master(1, frequency)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x04) #enable only MPA-SSA chip I2C
    if (chip == 'MPA'):
        Send_MPA_SSA_I2C_Command(MPA, 0, write, address, data) #enable only MPA-SSA chip I2C
    elif (chip == 'SSA'):
        Send_MPA_SSA_I2C_Command(SSA, 0, write, address, data)
    Configure_MPA_SSA_I2C_Master(0, 4)
