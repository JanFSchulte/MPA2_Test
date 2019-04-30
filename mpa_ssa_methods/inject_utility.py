from mpa_methods import *


class inject_utility():

	def __init__(self, SSA, MPA, FC7, i2c_mpa, i2c_ssa):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.i2c_mpa = i2c_mpa; self.i2c_ssa = i2c_ssa;
		self.mpadigpattent = False


	def stub(self, strips = [], pixels = []):
		self.strip_dig(strips)
		sleep(0.001)
		self.pixel_dig(pixels)
		sleep(0.001)


	def strip_dig(self, hit_list = [], hip_list = [], sequence = 0x1):
		self.SSA.inject.digital_pulse(
			hit_list = hit_list, hip_list = hip_list,
			sequence = sequence, initialise = False)


	def strip_anl(self, hit_list = [], mode = 'edge', threshold = [50, 100], cal_pulse_amplitude = 255, initialise = True, trigger = False):
		#fast method, it avoids any configuration that is already set
		self.SSA.inject.analog_pulse(
			hit_list = hit_list, mode = 'mode', threshold = threshold,
			cal_pulse_amplitude = cal_pulse_amplitude, trigger = trigger,
			initialise = initialise)


	def pixel_dig(self, hit_list = [], read_back = True):
		if(len(hit_list)>0):
			if(not isinstance(hit_list[0], list)):
				hit_list = [hit_list]
		disable_pixel(0,0) # Disable all pixel
		time.sleep(0.001)
		for [pixel, row] in hit_list:
			I2C.pixel_write('ENFLAGS', row, pixel, 0x20)
			time.sleep(0.001)
			if(read_back):
				tmp = I2C.pixel_read('ENFLAGS', row, pixel)
				if(tmp!=0x20):
					print("\n\n-> MPA-I2C error")
					print("\n\n-> MPA-I2C error {r:0d}-{p:0d} found: 0x{v:0x} - expected 0x20".format(r=row, p=pixel, v=tmp))
		if(not self.mpadigpattent):
			I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
			self.mpadigpattent = True


	def pixel_anl(self):
		pass

	def ssa_shiftreg(self, pattern = [128]*8):
		self.SSA.ctrl.activate_readout_shift()
		self.SSA.ctrl.set_shift_pattern(pattern[0], pattern[1],pattern[2],pattern[3],pattern[4],pattern[5],pattern[6],pattern[7])
		self.i2c_mpa.peri_write('ECM', 0b01000001)
