### Ported to python 3.5 on April 2020 - acaratel

#try:
from PyChipsUser import *
#except:
#    print("Impossible to import PyChipsUser.")
#    print("The communication with the test system is unavailable. ")
#    print("You will be able to run in analysis-mode only.\n\n")

import sys
import os
from d19cScripts.ErrorHandler import *
import time
import numpy as np

# sometimes you may want to run the script from the sw directory
isInD19CScripts = True
if os.path.isdir("./d19cScripts"):
    isInD19CScripts = False


if isInD19CScripts:
    fc7AddrTable = AddressTable("./fc7AddrTable.dat")
else:
    fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
fc7ErrorHandler = ErrorHandler()
########################################
# IP address
########################################
if isInD19CScripts:
    f = open('./ipaddr.dat', 'r')
else:
    f = open('./d19cScripts/ipaddr.dat', 'r')
ipaddr = f.readline()
ipaddr = ipaddr.replace('\n', '')
ipaddr = ipaddr.replace('\t', '')
ipaddr = ipaddr.replace(' ' , '')
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
#############

def SendCommand_I2C(command, hybrid_id, chip_id, page, read, register_address, data, ReadBack):
    """Compose and send I2C Commands."""

    # shift data to respective mask position
    raw_command = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.command_type").shiftDataToMask(command)
    raw_word0 = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word_id").shiftDataToMask(0)
    raw_word1 = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word_id").shiftDataToMask(1)
    raw_chip_id = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_slave_id").shiftDataToMask(chip_id)
    raw_hybrid_id = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_board_id").shiftDataToMask(hybrid_id)
    #raw_readback = fc7AddrTable.getItem("ctrl_command_i2c_command_page_readback").shiftDataToMask(ReadBack)
    #raw_page = fc7AddrTable.getItem("ctrl_command_i2c_command_page").shiftDataToMask(page)
    raw_read = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_read").shiftDataToMask(read)
    raw_register = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_register").shiftDataToMask(register_address)
    raw_data = fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word1_data").shiftDataToMask(data)

    raw_readback = 0
    raw_page = 0

    # compose command words
    cmd0 = raw_command + raw_word0 + raw_hybrid_id + raw_chip_id + raw_readback + raw_read + raw_page + raw_register;
    cmd1 = raw_command + raw_word1 + raw_data
    description = "Command: type = " + str(command) + ", hybrid = " + str(hybrid_id) + ", chip = " + str(chip_id)
    #print(hex(cmd))
    if(read == 1):
        fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", cmd0)
    else:
        fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", cmd0)
        #time.sleep(0.01)
        fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", cmd1)
    
    return description

def DataFromMask(data, mask_name):
    return fc7AddrTable.getItem(mask_name).shiftDataFromMask(data)

# Send command ctrl
def SendCommand_CTRL(name = "none", profile=0):
    if(profile): pr_start=time.time()
    if name == "none":
        print("Sending nothing")
    elif name == "global_reset":
        fc7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1)
        time.sleep(0.5)
    elif name == "reset_trigger":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.reset", 1)
    elif name == "start_trigger":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.start_trigger", 1)
    elif name == "stop_trigger":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.stop_trigger", 1)
    elif name == "load_trigger_config":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.load_config", 1)
    elif name == "reset_i2c":
        fc7.write("fc7_daq_ctrl.command_processor_block.i2c.control.reset", 1)
    elif name == "reset_i2c_fifos":
        fc7.write("fc7_daq_ctrl.command_processor_block.i2c.control.reset_fifos", 1)
    elif name == "fast_orbit_reset":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.fast_orbit_reset", 1)
    elif name == "fast_fast_reset":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.fast_reset", 1)
    elif name == "fast_trigger":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.fast_trigger", 1)
    elif name == "fast_test_pulse":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.fast_test_pulse", 1)
    elif name == "fast_i2c_refresh":
        fc7.write("fc7_daq_ctrl.fast_command_block.control.fast_i2c_refresh", 1)
    elif name == "load_dio5_config":
        fc7.write("fc7_daq_ctrl.dio5_block.control.load_config", 1)
    elif name == "reset_readout":
        fc7.write("fc7_daq_ctrl.readout_block.control.readout_reset", 1)
    else:
        print("Unknown Command" + str(name))
    if(profile): print('->  FC7 SendCommand_CTRL -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))

# Data Readout
def to_str(i):
    return "{0:#0{1}x}".format(i,10)
def to_number(i, msb, lsb):
    return int(format(i,'032b')[32-msb:32-lsb],2)

def print_data(chip_type, package_size, num_chips, packet_nbr, data):
    header_size = 6
    #if(chip_type == "SSA_emulator"):
    #    package_size = (header_size+(num_chips*7))
    #elif(chip_type == "CBC_emulator" or chip_type == "CBC_real"):
    #    package_size = (header_size+(num_chips*11))

    if packet_nbr*package_size != len(data):
        print("Wrong data length")
        return

    for pkg in range(0, packet_nbr):
        print("--==========================--")
        print("-- Header Info:             --")
        print("--==========================--")
        print("\t FE_NBR: " + str(to_number(data[0+pkg*package_size],23,16)) + "BLOCK_SIZE: "  + str(to_number(data[0+pkg*package_size],15,0)))
        print("\t L1 Counter: " + str(to_number(data[2+pkg*package_size],23,0)))
        print("\t BX Counter: " + str(to_number(data[3+pkg*package_size],31,0)))
        print("\t TLU Trigger ID: " + str(to_number(data[4+pkg*package_size],23,8)))

        #  '%8s\\t' % (.+?),  -> '{:8s}\\t'.format( $1 ),
        print( "\t\t" +
            '{:8s}\t'.format( "Chip 0" ) +
            '{:8s}\t'.format( "Chip 1" ) +
            '{:8s}\t'.format( "Chip 2" ) +
            '{:8s}\t'.format( "Chip 3" ) +
            '{:8s}\t'.format( "Chip 4" ) +
            '{:8s}\t'.format( "Chip 5" ) +
            '{:8s}\t'.format( "Chip 6" ) +
            '{:8s}\t'.format( "Chip 7" ) )

        if(chip_type == "SSA_emulator"):
            for j in range (0, 7):
                if j == 0:
                    print("\t --==========================--")
                    print("\t -- Trigger Data:            --")
                    print("\t --==========================--")
                if j == 5:
                    print("\t --==========================--")
                    print("\t -- Centoid Data:            --")
                    print("\t --==========================--")

                if num_chips > 1:
                    print("\t\t" + to_str(data[header_size+j+pkg*package_size]) + "\t")
                    for i in range (1,num_chips-1):
                        print(to_str(data[header_size+i*7+j+pkg*package_size]) + "\t")
                    print(to_str(data[header_size+(num_chips-1)*7+j+pkg*package_size]))
                else:
                    print("\t\t", to_str(data[header_size+j+pkg*package_size]))



        elif(chip_type == "CBC_emulator" or chip_type == "CBC_real"):
            for j in range (0, 11):
                if j == 0:
                    print("\t --==========================--")
                    print("\t -- Trigger Data:            --")
                    print("\t --==========================--")
                if j == 9:
                    print("\t --==========================--")
                    print("\t -- Stub Data:               --")
                    print("\t --==========================--")

                if num_chips > 1:
                    print("\t\t" + to_str(data[header_size+j+pkg*package_size]) + "\t")
                    for i in range (1,num_chips-1):
                        print(to_str(data[header_size+i*11+j+pkg*package_size]) + "\t")
                    print(to_str(data[header_size+(num_chips-1)*11+j+pkg*package_size]))
                else:
                    print("\t\t" + to_str(data[header_size+j+pkg*package_size]))



# Power initialization for FMC's
def InitFMCPower(fmc_id):
  fc7.write("system_fmc_pg_c2m",1)

  if (fmc_id == "fmc_l12"):
    fc7.write("system_fmc_l12_pwr_en",0)
    os.system("python fc7_i2c_voltage_set.py L12 p2v5");
    time.sleep(0.5)
    fc7.write("system_fmc_l12_pwr_en",1)

  if (fmc_id == "fmc_l8"):
    fc7.write("system_fmc_l8_pwr_en",0)
    os.system("python fc7_i2c_voltage_set.py L8 p2v5");
    time.sleep(0.5)
    fc7.write("system_fmc_l8_pwr_en",1)

  os.system("python fc7_i2c_voltage_get_all.py");

# Set manual delay of the line
def SetLineDelayManual(hybrid_id, chip_id, line_id, delay, bitslip):
    # we use only one register to set everything (more convenient for lots of chips)
    # bits: 31-28 - hybrid id, 27-24 - chip id, 23-20 - line id, 16 - enable manual delays, 12-8 - manual tap delay, 2-0 - bitslip
    word = ((hybrid_id & 0xF) << 28) + ((chip_id & 0xF) << 24) + ((line_id & 0xF) << 20) + (1 << 16) + ((delay & 0x1F) << 8) + ((bitslip & 0x07) << 0)
    # write word
    fc7.write("cnfg_phy_manual_delays", word)
    time.sleep(0.01)
    # do tuning
    fc7.write("ctrl_phy_phase_tune_again", 1)
    # time.sleep
    time.sleep(0.1)

# Configure Fast Block
def Configure_Fast(triggers_to_accept, user_frequency, source, stubs_mask, stubs_latency):
  fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", triggers_to_accept)
  fc7.write("cnfg_fast_user_frequency", user_frequency)
  fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", source)
  fc7.write("cnfg_fast_stub_mask", stubs_mask)
  fc7.write("cnfg_fast_stub_trigger_delay", stubs_latency)
  #time.sleep(1)
  SendCommand_CTRL("reset_trigger")
  time.sleep(0.001)
  SendCommand_CTRL("load_trigger_config")
  time.sleep(0.001)

def Configure_TestPulse_MPA_SSA(delay_before_next_pulse, number_of_test_pulses):
  # fast commands within the test pulse fsm
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset", 0)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse", 1)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a", 0)
  # disable the l1 backpressure
  fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
  # now write
  Configure_TestPulse(50, 50, delay_before_next_pulse, number_of_test_pulses)

'''Fast Command Block
   fc7_daq_cnfg.fast_command_block.triggers_to_accept                  *number of triggers to accepted (0 - continuous triggering)
   cnfg_fast_user_frequency                      *frequency of the trigger\_source=3 (1...1000 kHz range).
   fc7_daq_cnfg.fast_command_block.trigger_source                              *trigger source: 1 - TTC, 2 - Stubs, 3 - User Trigger, 4 - TLU, 5 - External trigger, 6 - test pulse FSM, 7 - UIB antenna FSM, 8 - Consecutive triggers FSM
   cnfg_fast_stub_mask                           *mask of the hybrids to trigger stubs (useful for coincidence)
   cnfg_fast_stub_veto_length                    *on stubs self-triggering: number of 40MHz clock cycles to raise VETO and ignore the coming triggers
   fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset              *trigger source 6: delay after the fast reset command
   fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse              *trigger source 6: delay after the test pulse
   fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse             *trigger source 6: delay after the l1a before the next fast reset (if enabled)
   cnfg_fast_stub_trigger_delay                  *setting the delay of the stub trigger (trigger source 2)
   cnfg_fast_ext_trigger_delay_value             *delay of the external trigger (trigger source 4,5)
   cnfg_fast_delay_after_antenna_trigger         *antenna FSM: delay after antenna trigger
   cnfg_fast_delay_between_consecutive_trigeers  *consecutive FSM: delay between two consecutive L1A signals
   fc7_daq_cnfg.fast_command_block.misc.backpressure_enable                 *enable internal backpressure handling. should be enabled by default, and disabled only if triggering system knows howto handle d19c backpressure
   cnfg_fast_stubor_enable                       *trigger source 2: 1 - trigger on StubOR, 0 - trigger on HitOR
   fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable           *enable initial fast reset after sending start\_trigger command
   fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset                *trigger source 6: enable fast reset signal
   fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse                *trigger source 6: enable cal pulse signal
   fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a                       *trigger source 6: enable l1a signal
   cnfg_fast_seu_ntriggers_to_skip               *trigger source 6: number of l1a to skip
'''

def Configure_TestPulse_SSA(
    delay_after_fast_reset = 0,
    delay_after_test_pulse = 0,
    delay_before_next_pulse = 0,
    number_of_test_pulses = 0,
    enable_rst_L1 = 0,
    enable_initial_reset = 0,
    enable_L1 = 0,
    backpressure = 0):
    fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", backpressure)
    fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", (enable_rst_L1 or enable_initial_reset))
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset", delay_after_fast_reset)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse", delay_after_test_pulse)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", delay_before_next_pulse)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset", (enable_rst_L1 or enable_initial_reset))
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse", 1)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a", enable_L1)
    fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", number_of_test_pulses)
    fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 6)
    #fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", (enable_rst_L1 or enable_initial_reset))
    #### fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", delay_before_next_pulse)
    time.sleep(0.1)
    SendCommand_CTRL("load_trigger_config")
    time.sleep(0.1)

def Configure_TestPulse(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses):
  fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", 0)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset", delay_after_fast_reset)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse", delay_after_test_pulse)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", delay_before_next_pulse)
  fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", number_of_test_pulses)
  fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 6)
  time.sleep(0.01)
  SendCommand_CTRL("load_trigger_config")
  time.sleep(0.01)

def Configure_TestPulse_MPA(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses, enable_rst, enable_init_rst, enable_L1):
  fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", enable_init_rst) #enable_rst_L1
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset", delay_after_fast_reset)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse", delay_after_test_pulse)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", delay_before_next_pulse)
  #fc7.write("cnfg_fast_tp_fsm_shutter_en", enable_shut)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset", enable_rst) #enable_rst_L1
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse", 1)
  fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a", enable_L1)
  fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", number_of_test_pulses)
  fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 6)
  time.sleep(0.1)
  SendCommand_CTRL("load_trigger_config")
  time.sleep(0.1)

def Configure_SEU(cal_pulse_period, l1a_period, number_of_cal_pulses, initial_reset = 0):
  fc7.write('fc7_daq_ctrl.fast_command_block.control.reset', 1)
  time.sleep(0.10); fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", initial_reset)
  time.sleep(0.01); fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", cal_pulse_period)
  time.sleep(0.01); fc7.write("cnfg_fast_seu_ntriggers_to_skip", l1a_period)
  time.sleep(0.01); fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", number_of_cal_pulses)
  time.sleep(0.01); fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 9)
  time.sleep(0.1)
  SendCommand_CTRL("load_trigger_config")
  time.sleep(0.1)

# Configure I2C
def Configure_I2C(mask):
  fc7.write("cnfg_command_i2c", fc7AddrTable.getItem("cnfg_command_i2c_mask").shiftDataToMask(mask))
  SendCommand_CTRL("reset_i2c")
  SendCommand_CTRL("reset_i2c_fifos")

###################################################################################################
# CBC Related Methods                                         #
###################################################################################################
# data needs to be shifted if the mask is not from zero
def ShiftDataToMask(mask, data):
    shiftingMask = mask
    bitShiftRequired = 0
    while (shiftingMask & 0x1) == 0:
        shiftingMask >>= 1
        bitShiftRequired += 1
    return (data & 0xff) << bitShiftRequired

# class used for setting the map of different CBC parameters
class Parameter():
    def __init__(self, page_i, reg_address_str, mask_str):
        self.page = page_i-1
        self.reg_address = int(reg_address_str,0)
        self.mask = int(mask_str,16)

# writing parameter to all cbc
def SetParameterI2C(parameter_name, data):
    # 0 - write, 1 - read
    write = 0
    read = 1
    cbc2_map = {}

    # map of needed parameters
    cbc2_map["trigger_latency"] = Parameter(1, "0x01", "FF")
    cbc2_map["hit_detect"] = Parameter(1, "0x02", "60")
    cbc2_map["vcth"] = Parameter(1,"0x0C", "FF")
    cbc2_map["test_pulse_potentiometer"] = Parameter(1,"0x0D", "FF")
    cbc2_map["test_pulse_delay_select"] = Parameter(1,"0x0E", "F8") # LSB00000MSB - minimal, LSB11001MSB - maximal
    cbc2_map["select_channel_group"] = Parameter(1,"0x0E", "07") # LSB 000 MSB
    cbc2_map["test_pulse_control"] = Parameter(1,"0x0F", "C0") # 7 - polarity (1 = positive edge); 6 - enable test pulse
    cbc2_map["mask_channels_8_1"] = Parameter(1,"0x20", "FF")

    write_data = data
    # FIXME no mask anymore
    if cbc2_map[parameter_name].mask != 255:
        fc7.write("cnfg_command_i2c_mask", cbc2_map[parameter_name].mask)
        write_data = ShiftDataToMask(cbc2_map[parameter_name].mask, data)

    SendCommand_I2C(2, 0, 0, cbc2_map[parameter_name].page, write, cbc2_map[parameter_name].reg_address, write_data, 0)
    time.sleep(0.5)

def CBC_Config():
    SetParameterI2C("trigger_latency", 195)
    SetParameterI2C("hit_detect", 1) # mode = single, enable = on
    SetParameterI2C("vcth", 127) #default
    SetParameterI2C("test_pulse_potentiometer", 0) # default 1.1V
    SetParameterI2C("test_pulse_delay_select", 24) # 11000
    SetParameterI2C("select_channel_group", 0)
    SetParameterI2C("test_pulse_control", 1) # polarity negative, test pulse enabled

    # unmask all channels
    i_start = 32    # 32
    i_finish = 64    # 64
    for i in range(i_start, i_finish):
        SendCommand_I2C(2, 0, 0, 0, 0, 0, i, 255, 0)
    time.sleep(2)

def CBC_ConfigTXT():
    # 0 - write, 1 - read
    write = 0
    read = 1

    cbc_config = np.genfromtxt('Cbc2_default_hole.txt', skip_header=2, dtype='str')

    for i in range(0, cbc_config.shape[0]): # including offset
    #for i in range(0, 52): # excluding offset
        SendCommand_I2C(2, 0, 0, int(cbc_config[i][1],0), write, int(cbc_config[i][2],0), int(cbc_config[i][4],0), 0)
    time.sleep(2)

###################################################################################################

# Configure DIO5
def Configure_DIO5(out_en, term_en, thresholds):
  fc7.write("cnfg_dio5_en", 1)
  for i in range (1,6):
    combined_config = fc7AddrTable.getItem("cnfg_dio5_ch1_out_en").shiftDataToMask(out_en[i-1]) + fc7AddrTable.getItem("cnfg_dio5_ch1_term_en").shiftDataToMask(term_en[i-1]) + fc7AddrTable.getItem("cnfg_dio5_ch1_threshold").shiftDataToMask(thresholds[i-1])
    fc7.write(("cnfg_dio5_ch"+str(i)+"_sel"), combined_config)

  time.sleep(0.5)
  SendCommand_CTRL("load_dio5_config")
  time.sleep(0.5)


def ReadStatus(name = "Current Status"):
  print("============================")
  print(name + ":")

  error_counter = fc7.read("stat_error_counter")
  print("   -> Error Counter: " + str(error_counter))
  if error_counter > 0:
        for i in range (0,error_counter):
          error_full = fc7.read("stat_error_full")
          error_block_id = DataFromMask(error_full,"stat_error_block_id");
          error_code = DataFromMask(error_full,"stat_error_code");
          print("   -> ")
          fc7ErrorHandler.getErrorDescription(error_block_id,error_code)
  else:
    print("   -> No Errors")
  temp_source = fc7.read("stat_fast_fsm_source")
  temp_source_name = "Unknown"
  if temp_source == 1:
    temp_source_name = "L1-Trigger"
  elif temp_source == 2:
    temp_source_name = "Stubs"
  elif temp_source == 3:
    temp_source_name = "User Frequency"
  elif temp_source == 4:
    temp_source_name = "TLU"
  elif temp_source == 5:
    temp_source_name = "EXT DIO5"
  elif temp_source == 6:
    temp_source_name = "Test Pulse Trigger"
  elif temp_source == 7:
    temp_source_name = "Antenna Trigger"
  print("   -> trigger source:" + str(temp_source_name))
  temp_state = fc7.read("stat_fast_fsm_state")
  temp_state_name = "Unknown"
  if temp_state == 0:
    temp_state_name = "Idle"
  elif temp_state == 1:
    temp_state_name = "Running"
  elif temp_state == 2:
    temp_state_name = "Paused. Waiting for readout"
  print("   -> trigger state:" + str(temp_state_name))
  print("   -> trigger configured:"  + str(fc7.read("fc7_daq_stat.fast_command_block.general.configured")))
  print(   "   -> --------------------------------")
  print("   -> i2c commands fifo empty:" + str( fc7.read("fc7_daq_stat.command_processor_block.i2c.command_fifo.empty")))
  print("   -> i2c replies fifo empty:" + str( fc7.read("fc7_daq_stat.command_processor_block.i2c.reply_fifo.empty")))
  print("   -> i2c nreplies available:" + str( fc7.read("fc7_daq_stat.command_processor_block.i2c.nreplies")))
  print("   -> i2c fsm state:" + str( fc7.read("fc7_daq_stat.command_processor_block.i2c.master_status_fsm") ))
  print(   "   -> --------------------------------")
  print(   "   -> dio5 not ready:" + str(fc7.read("fc7_daq_stat.dio5_block.status.not_ready")))
  print(   "   -> dio5 error:" + str( fc7.read("fc7_daq_stat.dio5_block.status.error")))
  print("============================")

def ReadChipData(checking, expected_value):
  numberOfReads = 0
  print("Reading Out Data:")
  print("   ==========================================================================================")
  print("   | Hybrid ID             || Chip ID             || Register                || DATA         |")
  print("   ==========================================================================================")

  while fc7.read("fc7_daq_stat.command_processor_block.i2c.reply_fifo.empty") == 0:
      numberOfReads = numberOfReads + 1
      reply = fc7.read("fc7_daq_ctrl.command_processor_block.i2c.reply_fifo")
      hybrid_id = DataFromMask(reply, "ctrl_command_i2c_reply_hybrid_id")
      chip_id = DataFromMask(reply, "ctrl_command_i2c_reply_chip_id")
      data = DataFromMask(reply, "ctrl_command_i2c_reply_data")
      register = DataFromMask(reply, "ctrl_command_i2c_reply_register")
      #print(bin(fc7.read("ctrl_i2c_command_fifo")))
      #print(bin(reply)[4:12])
      print('   | {:s} %-12i || {:s} %-12i || {:s} %-12s || %-12s |'.format("Hybrid #", hybrid_id, "Chip #", chip_id, "Register #", hex(register)[:4], hex(data)[:4]))
      if(checking and data != expected_value and register != 0):
         print('!!!!!!!!!!!!!!!!!!!!!!! problem on write-read sequence. Expected value is: ' + str(expected_value))
         sys.exit()
      print("    -----------------------------------------------------------------------------------------")
  print("   ==========================================================================================")
  print("the number of reads is = " + str(numberOfReads))

# tests i2c master
def I2CTester():
    ###############
    ## i2c config #
    ###############
    # command_i2c: 0 - send command to certain hybrid/chip, 1 - send command to all chips on hybrid, 2 - send command to all chips on all hybrids
    #command_i2c = 0
    #hybrid_id = 0
    #chip_id = 0
    #page = 0
    # 0 - write, 1 - read
    write = 0
    read = 1
    #register = 2
    #data = 7
    ReadBack = 0
    ################

    ReadStatus("Before I2C Configuration")
    Configure_I2C(255)
    ReadStatus("After I2C Configuration")

    num_i2c_registersPage1 = 35
    num_i2c_registersPage2 = 2
       #                       i2c_command , hybrid_id ,  chip_id, page , read , register_address , data;

    for i in range(0, num_i2c_registersPage1):
        SendCommand_I2C(          2,         0,       0,    0, read,        1,    10, ReadBack)
    for i in range(0, num_i2c_registersPage2):
        SendCommand_I2C(          2,         0,       0,    1, read,        i,    10, ReadBack)
    for i in range(1, num_i2c_registersPage1):
        SendCommand_I2C(          2,         0,       0,    0, write,       i,    5, ReadBack)
    for i in range(1, num_i2c_registersPage2):
        SendCommand_I2C(          2,         0,       15,    1, write,       i,    7, ReadBack)
    for i in range(0, num_i2c_registersPage1):
        SendCommand_I2C(          2,         0,       0,    0, read,        i,    10, ReadBack)
    for i in range(0, num_i2c_registersPage2):
        SendCommand_I2C(          2,         0,       0,    1, read,        i,    10, ReadBack)

    time.sleep(1)

    ReadStatus("After Send Command")
    ReadChipData()
    ReadStatus("After Read Reply")

# dio5 testing
def DIO5Tester(fmc_id):
    InitFMCPower(fmc_id)
    ################
    ## dio5 config #
    ################
    # enabled outputs
    out_en = [1,0,1,0,0]
    # 50ohm termination
    term_en = [0, 1, 0, 1, 1]
    # thresholds
    thresholds = [0,50,0,50,50]
    ################

    Configure_DIO5(out_en, term_en, thresholds)
    ReadStatus("After DIO5 Config")

def SetLineDelayManual(hybrid_id, chip_id, line_id, delay, bitslip):
    # we use only one register to set everything (more convenient for lots of chips)
    # bits: 31-28 - hybrid id, 27-24 - chip id, 23-20 - line id, 16 - enable manual delays, 12-8 - manual tap delay, 2-0 - bitslip
    word = ((hybrid_id & 0xF) << 28) + ((chip_id & 0xF) << 24) + ((line_id & 0xF) << 20) + (1 << 16) + ((delay & 0x1F) << 8) + ((bitslip & 0x07) << 0)
    # write word
    fc7.write("cnfg_phy_manual_delays", word)
    time.sleep(0.01)
    # do tuning
    fc7.write("ctrl_phy_phase_tune_again", 1)
    # time.sleep
    time.sleep(0.1)
