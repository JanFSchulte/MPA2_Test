from mpa_methods import *


class inject_utility():

	def __init__(self, SSA, MPA, FC7, i2c_mpa, i2c_ssa):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.i2c_mpa = i2c_mpa; self.i2c_ssa = i2c_ssa;

	def stub(self, strip, pixel, row = 5,  retimepix=1):
		self.strip_dig([strip])
		sleep(0.001)
		self.pixel_dig(pixel, row, retimepix)
		sleep(0.001)

		send_test(8)
		sleep(0.001)
		stubs = read_stubs()
		return stubs
		#print test_pp_digital(row, pixel) # send test pulse to defined row and pixel

	def initialise(self, calpulse = 1):
		self.SSA.ctrl.init_slvs(0b110)
		time.sleep(0.001)
		activate_sync() # activate synchronous mode
		self.SSA.ctrl.activate_readout_normal()
		#activate_pp() # activate pixel-pixel mode, useful to check good MPA configuration
		activate_ps() # activate pixel-strip standard mode


	def strip_dig(self, hit_list = [], hip_list = [], sequence = 0x1):
		self.SSA.inject.digital_pulse(
			hit_list = hit_list, hip_list = hip_list,
			sequence = sequence, initialise = False)


	def strip_anl(self, hit_list = [], mode = 'edge', threshold = [50, 100], cal_pulse_amplitude = 255, initialise = True, trigger = False):
		self.SSA.inject.analog_pulse(
			hit_list = hit_list, mode = 'mode', threshold = threshold,
			cal_pulse_amplitude = cal_pulse_amplitude, trigger = trigger,
			initialise = initialise)


	def pixel_dig(self, pixel, row = 5,  retimepix=1):
		I2C.peri_write('RetimePix', retimepix) # Set the number of cycle which pixel data wait
		disable_pixel(0,0) # Disable all pixel
		I2C.pixel_write('ENFLAGS', row, pixel, 0x20)
		I2C.pixel_write('DigPattern', 0, 0,  0xff)


	def pixel_anl(self):
		pass


	def ssa_shiftreg(self, pattern = [128]*8):
		self.SSA.ctrl.activate_readout_shift()
		self.SSA.ctrl.set_shift_pattern(pattern[0], pattern[1],pattern[2],pattern[3],pattern[4],pattern[5],pattern[6],pattern[7])
		self.i2c_mpa.peri_write('ECM', 0b01000001)
