from d19cScripts.fc7_daq_methods import *
import time
#import matplotlib.pyplot as plt

def ConfigureL1ATuning():
    # fast commands within the test pulse fsm
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset", 1)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse", 0)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a", 1)
    # disable the l1 backpressure
    fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
    # basic settings
    fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", 1)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset", 50)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse", 50)
    fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", 50) # actually the only one important
    fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", 0)
    fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 6)
    time.sleep(0.01)
    SendCommand_CTRL("load_trigger_config")
    time.sleep(0.01)

def SendPhaseTuningCommand(value):
    fc7.write("fc7_daq_ctrl.physical_interface_block.phase_tuning_ctrl", value)

def GetPhaseTuningStatus(printStatus = True):
    # get data word
    data = fc7.read("fc7_daq_stat.physical_interface_block.phase_tuning_reply")

    # parse commands
    line_id = (data & 0xF0000000) >> 28
    output_type = (data & 0x0F000000) >> 24

    # line configuration
    if(output_type == 0):
        mode = (data & 0x00003000) >> 12
        master_line_id = (data & 0x00000F00) >> 8
        delay = (data & 0x000000F8) >> 3
        bitslip = (data & 0x00000007) >> 0
        if printStatus:
            print("Line Configuration: ")
            print("\tLine ID: "+ str(line_id) +",\tMode: "+ str(mode)+ ",\tMaster line ID: "+ str(master_line_id)+ ",\tIdelay: "+ str(delay)+ ",\tBitslip: "+ str(bitslip))
        return -1
    # tuning status
    elif(output_type == 1):
        delay = (data & 0x1F<<19) >> 19
        bitslip = (data & 0xF<<15) >> 15
        done = (data & 0x1<<14) >> 14
        wa_fsm_state = (data & 0xF<<7) >> 7
        pa_fsm_state = (data & 0xF<<0) >> 0
        if printStatus:
            print("Line Status: ")
            print("\tTuning done/applied: "+ str(done))
            print("\tLine ID: "+str(line_id)+ ",\tIdelay: " +str(delay)+ ",\tBitslip: " +str(bitslip)+ ",\tWA FSM State: " +str(wa_fsm_state)+ ",\tPA FSM State: "+str( pa_fsm_state))
        return done

    # tuning status
    elif output_type == 6:
        default_fsm_state = (data & 0x000000FF) >> 0
        if printStatus:
            print("Default tuning FSM state: "+ hex(default_fsm_state))
        return -1

    # unknown
    else:
        print("Error! Unknown status message!")
        return -2

def GetDefaultFSMState():
    # command 6
    command_type = 6
    command_raw = (command_type & 0xF) << 16
    # final command 6
    command_final = command_raw
    SendPhaseTuningCommand(command_final)
    time.sleep(0.01)
    GetPhaseTuningStatus()

def GetLineStatus(hybrid_id, chip_id, line_id):
    # shifting
    hybrid_raw = (hybrid_id & 0xF) << 28
    chip_raw = (chip_id & 0xF) << 24
    line_raw = (line_id & 0xF) << 20

    # command 0
    command_type = 0
    command_raw = (command_type & 0xF) << 16
    # final command 0
    command_final = hybrid_raw + chip_raw + line_raw + command_raw
    SendPhaseTuningCommand(command_final)
    time.sleep(0.01)
    GetPhaseTuningStatus()

    # command 1
    command_type = 1
    command_raw = (command_type & 0xF) << 16
    # final command 1
    command_final = hybrid_raw + chip_raw + line_raw + command_raw
    SendPhaseTuningCommand(command_final)
    time.sleep(0.01)
    done = GetPhaseTuningStatus()

    return done

def CheckLineDone(hybrid_id, chip_id, line_id):
    # shifting
    hybrid_raw = (hybrid_id & 0xF) << 28
    chip_raw = (chip_id & 0xF) << 24
    line_raw = (line_id & 0xF) << 20

    # command 1
    command_type = 1
    command_raw = (command_type & 0xF) << 16
    # final command 1
    command_final = hybrid_raw + chip_raw + line_raw + command_raw
    SendPhaseTuningCommand(command_final)
    time.sleep(0.01)

    line_done = GetPhaseTuningStatus(printStatus = True)
    if line_done >= 0:
        pass
    else:
        print("Tuning Failed or Wrong Status")
    return line_done

def SetLineMode(hybrid_id, chip_id, line_id, mode, delay = 0, bitslip = 0, l1_en = 0, master_line_id = 0):
    # shifting
    hybrid_raw = (hybrid_id & 0xF) << 28
    chip_raw = (chip_id & 0xF) << 24
    line_raw = (line_id & 0xF) << 20
    # command
    command_type = 2
    command_raw = (command_type & 0xF) << 16
    # shift payload
    mode_raw = (mode & 0x3) << 12
    # defautls
    l1a_en_raw = 0
    master_line_id_raw = 0
    delay_raw = 0
    bitslip_raw = 0
    # now assign proper values
    if mode == 0:
        l1a_en_raw = (l1_en & 0x1) << 11
    elif mode == 1:
        master_line_id_raw = (master_line_id & 0xF) << 8
    elif mode == 2:
        delay_raw = (delay & 0x1F) << 3
        bitslip_raw = (bitslip & 0x7) << 0
    # now combine the command itself
    command_final = hybrid_raw + chip_raw + line_raw + command_raw + mode_raw + l1a_en_raw + master_line_id_raw + delay_raw + bitslip_raw
    SendPhaseTuningCommand(command_final)

def SendControl(hybrid_id, chip_id, line_id, command):
    # shifting
    hybrid_raw = (hybrid_id & 0xF) << 28
    chip_raw = (chip_id & 0xF) << 24
    line_raw = (line_id & 0xF) << 20
    # command
    command_type = 5
    command_raw = (command_type & 0xF) << 16
    # final
    command_final = hybrid_raw + chip_raw + line_raw + command_raw
    #
    if command == "do_apply":
        command_final += 4
    elif command == "do_word":
        command_final += 2
    elif command == "do_phase":
        command_final += 1
    # send
    SendPhaseTuningCommand(command_final)

def SetLinePattern(hybrid_id, chip_id, line_id, pattern, pattern_period):
    # shifting
    hybrid_raw = (hybrid_id & 0xF) << 28
    chip_raw = (chip_id & 0xF) << 24
    line_raw = (line_id & 0xF) << 20

    # setting the size of the pattern
    command_type = 3
    command_raw = (command_type & 0xF) << 16
    len_raw = (0xFF & pattern_period) << 0
    command_final = hybrid_raw + chip_raw + line_raw + command_raw + len_raw
    SendPhaseTuningCommand(command_final)
    # setting the pattern itself
    command_type = 4
    command_raw = (command_type & 0xF) << 16
    byte_id_raw = (0xFF & 0) << 8
    pattern_raw = (0xFF & pattern) << 0
    command_final = hybrid_raw + chip_raw + line_raw + command_raw + byte_id_raw + pattern_raw
    SendPhaseTuningCommand(command_final)

def TuneLine(line_id, pattern, pattern_period, changePattern = True, printStatus = True):
    # in that case all set specified pattern (same for all lines)
    if changePattern:
        SetLineMode(0,0,line_id,mode = 0)
        SetLinePattern(0,0,line_id,pattern, pattern_period)
        time.sleep(0.1)
    # do phase alignment
    SendControl(0,0,line_id,"do_phase")
    time.sleep(0.1)
    # do word alignment
    SendControl(0,0,line_id,"do_word")
    time.sleep(0.1)

    if printStatus:
        GetLineStatus(0,0,line_id)
        print( "\n")

    return CheckLineDone(0,0,line_id)

def TuneMPA(pattern):
    # in case of MPA the pattern is following: stub lines (1-5) tune on patterns 0b10100000, l1a inherited from the line 1

    # set mpa
    #I2C.peri_write("ReadoutMode", 2)
    #I2C.peri_write("LFSR_data", 0b10100000)

    # tune all lines
    state = True

    for line in range(0,6):
        TuneLine(line, np.array(pattern), 8, True, False)
        if CheckLineDone(0,0,line) != 1:
            print(f"Failed tuning line {line}")
            state = False

    return state;
    # l1a
    #SetLineMode(0,0, line_id = 0, mode = 1, master_line_id = 1)
    #if CheckLineDone(0,0,0) == 1:
    #	print "Delay to l1a line was applied succesfully"
    #else:
    #    print "Failed applying l1a line"
	#return False
	# good
    return True


def TuneCBC3():
    # in case of CBC3 the pattern is following: stub line (5) tunes on pattern 0b10000000

    # send fast reset
    SendCommand_CTRL("fast_fast_reset")

    # tune our lines
    line = 5
    TuneLine(line, 0b10000000, 1, True, True)
    if CheckLineDone(0,0,line) == 1:
        print("Line " + str(line) + " was tuned succesfully")
    else:
        print("Failed tuning line " + str(line))

    # set stub lines as slaves
    for line in range(1,5):
        SetLineMode(0,0, line_id = line, mode = 1, master_line_id = 5)

    # set the l1 line
    l1_slave = 1
    if l1_slave > 0:
        SetLineMode(0,0, line_id = 0, mode = 1, master_line_id = 5, delay=7,bitslip=0)
    else:
        ConfigureL1ATuning()
        SendCommand_CTRL("start_trigger")
        TuneLine(0, 0b11000000, 38)
        time.sleep(1)
        SendCommand_CTRL("stop_trigger")
    if CheckLineDone(0,0,0) == 1:
        print( "line delay was applied succesfully")
    else:
        print( "Failed applying delay for line 0(L1)")
    # here it is

def GetDistribution(line_id, npoints = 100):
    line_raw = (line_id & 0xF) << 20
    command_type = 1
    command_raw = (command_type & 0xF) << 16
    command_final = line_raw + command_raw
    delay_data = np.zeros(npoints)
    print( "Progress:")
    for i in range(0,npoints):
        percentage = 100*i/npoints
        if percentage%10 == 0:
            print( "\t" +str(percentage)+ " %")
        SendControl(0,0,line_id,"do_phase")
        time.sleep(0.01)
        pa_fsm_state = 0
        while (pa_fsm_state != 14):
            SendPhaseTuningCommand(command_final)
            time.sleep(0.01)
            data = fc7.read("fc7_daq_ctrl.physical_interface_block.phase_tuning_ctrl")
            delay = (data & 0x00F80000) >> 19
            bitslip = (data & 0x00070000) >> 16
            done = (data & 0x00008000) >> 15
            wa_fsm_state = (data & 0x00000F00) >> 8
            pa_fsm_state = (data & 0x0000000F) >> 0
        delay_data[i] = delay
    #plt.hist(delay_data,np.arange(32))
    #plt.show()
