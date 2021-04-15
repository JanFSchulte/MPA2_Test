from .utilities.tbsettings import *
from .utilities.configure_communication import *
from .utilities.fc7_com import *

#from d19cScripts import *
from myScripts import *
from ssa_methods import *
from mpa_methods import *
from myScripts.BasicADC import *

from mpa_ssa_methods.inject_utility import *
from mpa_ssa_methods.readout_utility import *
from mpa_ssa_methods.power_utility import *
from mpa_ssa_methods.ps_utility import *
from mpa_ssa_methods.test import *

try:
	multimeter = keithley_multimeter()
except ImportError:
	multimeter = False

MPA = False

ipaddr, fc7AddrTable, fc7_if = configure_communication()
FC7 = fc7_com(fc7_if, fc7AddrTable)
FC7.activate_I2C_chip(verbose=0)


pwr  = mpassa_power_utility(ssa_i2c, FC7, MPA, SSA)
PS   = ps_utility(SSA, MPA, FC7, I2C, ssa_i2c)
test = test_utility(SSA, MPA, FC7, pwr, PS)
