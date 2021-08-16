from utilities.tbsettings import *
from utilities.configure_communication import *
from utilities.fc7_com import *

from mpa_methods.mpa_i2c_conf import *
from mpa_methods.mpa import *
from mpa_methods.mpa_power_utility import *
from mpa_methods.mpa_cal_utility import *
from mpa_methods.mpa_test_utility import *
#from mpa_methods.mpa_fc7_com import *
#from mpa_methods.mpa_probe_test import *

from myScripts.Instruments_Keithley_Multimeter_2000_GPIB import *
from myScripts.Instruments_Keithley_Multimeter_7510_LAN import *
from myScripts.Instruments_Keithley_Sourcemeter_2410_GPIB import *

# old import
# from myScripts.Multimeter_GPIB_Keithley import *

ipaddr, fc7AddrTable, fc7_if = configure_communication()
FC7 = fc7_com(fc7_if, fc7AddrTable)
#FC7.activate_I2C_chip(verbose=0)

I2C   = mpa_i2c_conf()
pwr   = mpa_power_utility(I2C, FC7)
mpa   = MPA_ASIC(I2C, FC7, pwr, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map)
cal   = mpa_cal_utility(mpa, I2C, FC7)
test  = mpa_test_utility(mpa, I2C, FC7)

try:
	from mpa_methods.mpa_bias_utility import *
	multimeter = keithley_multimeter()
	bias = mpa_bias_utility(mpa, I2C, FC7, multimeter, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map)
except ImportError:
	bias = False
	print("- Impossible to access GPIB instruments")

#probe = mpa_probe_test("../MPA_Results/TEST", mpa, I2C, fc7, cal, test, bias)

#measure     = SSA_measurements(ssa, I2C, FC7, cal, analog_mux_map, pwr, biascal)
#toptest     = SSA_test_top(ssa, I2C, FC7, cal, biascal, pwr, test, measure)
#xray        = SSA_test_xray(toptest, ssa, I2C, FC7, cal, biascal, pwr, test, measure)
#anl         = SSA_Analise_Test_results(toptest, test, measure, biascal)

def on():
	utils.activate_I2C_chip(FC7)
	time.sleep(0.1);  pwr.set_supply('on', display=False)
	time.sleep(0.1);  pwr.set_clock_source('internal')
	time.sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)

def off():
	utils.activate_I2C_chip(FC7)
	pwr.set_supply('off')

def init():
	return mpa.init(reset_board = True, reset_chip = False, display = True)

def reset_fc7():
	FC7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1);

def reset_mpa():
	mpa.reset()

def set_clock(val = 'internal'):
	pwr.set_clock_source(val)
	time.sleep(0.1);  ssa.init(reset_board = False, reset_chip = False, display = True)

#utils.activate_I2C_chip(FC7)

print("_____________________________________________________\n\n")
