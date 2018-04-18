
from ssa_methods.ssa import *
from ssa_methods.ssa_power_utility import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.main import *

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
