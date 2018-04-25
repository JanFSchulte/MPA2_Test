from ssa_methods.ssa import *
from ssa_methods.ssa_power_utility import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.ssa_test_xray import *

I2C   = ssa_i2c_conf()
pwr   = ssa_power_utility(I2C, fc7)
ssa   = SSA_ASIC(I2C, fc7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
cal   = SSA_cal_utility(ssa, I2C, fc7)
test  = SSA_test_utility(ssa, I2C, fc7, cal, pwr)

try:
	from ssa_methods.ssa_calibration import *
	biascal = ssa_calibration(ssa, I2C, fc7, multimeter, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
except ImportError:
	biascal = False
	print "- Impossible to access GPIB instruments"

measure     = SSA_measurements(ssa, I2C, fc7, cal, analog_mux_map, biascal)
xray        = SSA_test_XRay(ssa, I2C, fc7, cal, biascal, pwr, test, measure)

def on():
	sleep(0.1);  pwr.set_supply('on', display=False)
	sleep(0.1);  pwr.set_clock_source('internal')
	sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)

def off():
	pwr.set_supply('off')

def init():
	ssa.init(reset_board = True, reset_chip = False, display = True)

def reset_fc7():
	fc7.write("ctrl_command_global_reset", 1);

def reset_ssa():
	ssa.reset()

def set_clock(val = 'internal'):
	pwr.set_clock_source(val)
	sleep(0.1);  ssa.init(reset_board = False, reset_chip = False, display = True)

#utils.activate_I2C_chip()

print "_____________________________________________________\n\n"
