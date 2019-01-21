from mpa_methods import *
from mpa_ssa_methods.inject_utility import *
from mpa_ssa_methods.readout_utility import *


class ps_utility():

	def __init__(self, SSA, MPA, FC7, i2c_mpa, i2c_ssa):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.i2c_mpa = i2c_mpa; self.i2c_ssa = i2c_ssa;
		self.inj = inject_utility( SSA, MPA, FC7, i2c_mpa, i2c_ssa)
		self.rdo = readout_utility(SSA, MPA, FC7, i2c_mpa, i2c_ssa)


	def initialise(self, retimepix = 5):
		try:
			self.SSA.ctrl.init_slvs(0b110)
			time.sleep(0.001)
			activate_sync() # activate synchronous mode
			self.SSA.ctrl.activate_readout_normal()
			#activate_pp() # activate pixel-pixel mode, useful to check good MPA configuration
			activate_ps() # activate pixel-strip standard mode
			self.i2c_ssa.peri_write("CalPulse_duration", 1)
			self.i2c_mpa.peri_write('RetimePix', retimepix) # Set the number of cycle which pixel data wait
			self.i2c_mpa.peri_write("ConfSLVS", 0b00111111)
			self.FC7.reset()
			align_MPA()
			activate_I2C_chip(verbose = 0)
			return True
		except:
			return False


	def stubs(self, strips, pixels):
		#self.inj.initialise(retimepix = retimepix)
		r = self.inj.stub(strips, pixels)
		s = self.rdo.stubs(calpulse = 1)
		return s


	def stub_simple(self, strip, pixel, row, retimepix=5, calpulse=1):
		#self.inj.initialise(retimepix = retimepix)
		self.inj.stub([strip], [pixel, row])
		r = self.read_stubs(calpulse = calpulse)
		return r[1]
