from d19cScriptsfc7_daq_methods import *

## readout is still connected, and the counters (BX, L1, TDC, ..) will fill up the FIFO's quickly, if we don't disable the backpressure
fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)

## now we can set the desired parameters for the test pulse
# in 40MHz clock cycles
delay_after_fast_reset = 50
delay_after_test_pulse = 200
delay_before_next_pulse = 400
# 0 - infinite number of sequencies, otherwise as specified
number_of_test_pulses = 0

## now configure the test pulse machine
Configure_TestPulse(delay_after_fast_reset, delay_after_test_pulse, delay_before_next_pulse, number_of_test_pulses)

## now start
print "Starting Triggers: "
SendCommand_CTRL("start_trigger")

## read status, should tell you that the triggering is running
ReadStatus()

## stop is necessary only if you sent and infinite number of sequencies
SendCommand_CTRL("stop_trigger")

print "Stopped Triggers: "
ReadStatus()
