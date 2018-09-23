from ssa_methods.ssa import *
from ssa_methods.ssa_power_utility import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.ssa_test_top import *
from ssa_methods.ssa_test_xray import *
from ssa_methods.ssa_analise_utility import *
from ssa_methods.ssa_fc7_com import *
from ssa_methods.ssa_calibration import *
from ssa_methods.ssa_seu_utility import *
from myScripts.BasicADC import *


try:
	multimeter = keithley_multimeter()
except ImportError:
	multimeter = False
	print "- Impossible to access GPIB instruments"

FC7     = ssa_fc7_com(fc7)
I2C     = ssa_i2c_conf()
pwr     = ssa_power_utility(I2C, FC7)
ssa     = SSA_ASIC(I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
cal     = SSA_cal_utility(ssa, I2C, FC7)
test    = SSA_test_utility(ssa, I2C, FC7, cal, pwr)
pcbadc  = onboard_adc()
biascal = ssa_calibration(ssa, I2C, FC7, multimeter, pcbadc, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
measure = SSA_measurements(ssa, I2C, FC7, cal, analog_mux_map, pwr, biascal)
toptest = SSA_test_top(ssa, I2C, FC7, cal, biascal, pwr, test, measure)
xray    = SSA_test_xray(toptest, ssa, I2C, FC7, cal, biascal, pwr, test, measure)
anl     = SSA_Analise_Test_results(toptest, test, measure, biascal)  ## TOP FUNCTION TO CARACTERISE THE SSA
seu     = SSA_SEU(ssa, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)

def on():
	utils.activate_I2C_chip()
	sleep(0.1);  pwr.set_supply('on', display=False)
	sleep(0.1);  pwr.set_clock_source('internal')
	sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)

def off():
	utils.activate_I2C_chip()
	pwr.set_supply('off')

def init():
	ssa.init(reset_board = True, reset_chip = False, display = True)

def reset_fc7():
	FC7.write("ctrl_command_global_reset", 1);

def reset_ssa():
	ssa.reset()

def set_clock(val = 'internal'):
	pwr.set_clock_source(val)
	sleep(0.1);  ssa.init(reset_board = False, reset_chip = False, display = True)

#utils.activate_I2C_chip()

print "_____________________________________________________\n\n"
