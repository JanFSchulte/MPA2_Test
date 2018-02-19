from ssa_methods.ssa import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_i2c_conf import *
from ssa_methods.ssa_base import *
from ssa_methods.ssa_readout_utility import *

ssa             = SSA_ASIC(I2C, fc7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map) 
ssa_measure     = SSA_cal_utility(ssa, I2C, fc7)
ssa_test        = SSA_test_utility(ssa, I2C, fc7) 

try:
    from ssa_methods.ssa_calibration import *
    ssa_calibration = ssa_calibration(ssa, I2C, fc7, multimeter, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
except ImportError:
    print "- Impossible to access GPIB instruments"

def init():	ssa.init_all()

print "_____________________________________________________\n\n"

