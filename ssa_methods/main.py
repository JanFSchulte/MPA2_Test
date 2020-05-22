#from utilities.tbsettings import *
from ssa_methods.ssa import *
from ssa_methods.ssa_power_utility import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.main_ssa_test_1 import *
from ssa_methods.ssa_test_xray import *
from ssa_methods.ssa_analise_utility import *
from ssa_methods.ssa_fc7_com import *
from ssa_methods.ssa_calibration import *
from ssa_methods.ssa_seu_utility import *
from ssa_methods.ssa_test_seu import *
from myScripts.BasicADC import *
from ssa_methods.ssa_wp_analyze import *

#print("--------------------------------------")
#print(tbconfig.VERSION)
#print("--------------------------------------")

try:
	from myScripts.BasicMultimeter import *
	multimeter = keithley_multimeter()
except ImportError:
	multimeter = False
	print("- Impossible to access GPIB instruments")

FC7         = ssa_fc7_com(fc7)
ssa_i2c     = ssa_i2c_conf()
ssa_pwr     = ssa_power_utility(ssa_i2c, FC7)
ssa         = SSA_ASIC(ssa_i2c, FC7, ssa_pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
ssa_cal     = SSA_cal_utility(ssa, ssa_i2c, FC7)
pcbadc      = onboard_adc()
ssa_biascal = ssa_calibration(ssa, ssa_i2c, FC7, multimeter, pcbadc, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
ssa_measure = SSA_measurements(ssa, ssa_i2c, FC7, ssa_cal, analog_mux_map, ssa_pwr, ssa_biascal)
ssa_seuutil = SSA_SEU_utilities(ssa, ssa_i2c, FC7, ssa_pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
ssa_test    = SSA_test_utility(ssa, ssa_i2c, FC7, ssa_cal, ssa_pwr, ssa_seuutil)
ssa_toptest = SSA_test_top(ssa, ssa_i2c, FC7, ssa_cal, ssa_biascal, ssa_pwr, ssa_test, ssa_measure)
ssa_xray    = SSA_test_xray(ssa_toptest, ssa, ssa_i2c, FC7, ssa_cal, ssa_biascal, ssa_pwr, ssa_test, ssa_measure)
ssa_anl     = SSA_Analise_Test_results(ssa_toptest, ssa_test, ssa_measure, ssa_biascal)  ## TOP FUNCTION TO CARACTERISE THE SSA
ssa_seu     = SSA_SEU(ssa, ssa_seuutil, ssa_i2c, FC7, ssa_cal, ssa_biascal, ssa_pwr, ssa_test, ssa_measure)
SSA         = ssa

def ssa_on():
	utils.activate_I2C_chip()
	sleep(0.1);  ssa_pwr.set_supply('on', display=False)
	sleep(0.1);  ssa_pwr.set_clock_source('internal')
	sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)

def ssa_off():
	utils.activate_I2C_chip()
	ssa_pwr.set_supply('off')

def ssa_init():
	ssa.init(reset_board = True, reset_chip = False, display = True)

def reset_fc7():
	FC7.write("ctrl_command_global_reset", 1);

def reset_ssa():
	ssa.reset()

def set_clock(val = 'internal'):
	ssa_pwr.set_clock_source(val)
	sleep(0.1);  ssa.init(reset_board = False, reset_chip = False, display = True)

#utils.activate_I2C_chip()
