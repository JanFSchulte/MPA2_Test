
from ssa_methods.ssa_measurements_fe  import *
from ssa_methods.ssa_measurements_adc import *
from ssa_methods.ssa_measurements_pwr import *

class SSA_measurements():

	def __init__(self, ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal = False):
		self.fe  = SSA_measurements_fe( ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal)
		self.adc = SSA_measurements_adc(ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal)
		self.pwr = SSA_measurements_pwr(ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal)
		
	###### back-compatibility methods:
	def dac_linearity(self, *args, **kwargs):
		return self.fe.dac_linearity(*args, **kwargs)

	def scurve_trim_gain_noise(self, *args, **kwargs):
		return self.fe.scurve_trim_gain_noise(*args, **kwargs)
