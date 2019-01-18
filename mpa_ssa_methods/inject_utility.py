

class inject_utility():

	def __init__(self, SSA, MPA):
		self.SSA = SSA


	def strip_dig(self, hit_list = [], hip_list = [], duration = 1, sequence = 0x1, initialise = True):
		self.SSA.inject.digital_pulse(
			hit_list = hit_list, hip_list = hip_list,
			times = duration, sequence = sequence,
			initialise = initialise)


	def strip_anl(self, hit_list = [], mode = 'edge', threshold = [50, 100], cal_pulse_amplitude = 255, initialise = True, trigger = False):
		self.SSA.inject.analog_pulse(
			hit_list = hit_list, mode = 'mode', threshold = threshold,
			cal_pulse_amplitude = cal_pulse_amplitude, trigger = trigger,
			initialise = initialise)

	def pixel_dig(self):
		pass

	def pixel_anl(self):
		pass
