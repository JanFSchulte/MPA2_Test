
from myScripts.BasicD19c import * 
from ssa_reg_map import * 

class ssa_i2c_conf: 

	def __init__(self):
		self.ssa_peri_reg_map = ssa_peri_reg_map
		self.ssa_strip_reg_map = ssa_strip_reg_map
		self.freq = 0

	def set_freq(self, value):
		self.freq = value
		return True

	def get_freq(self, value):
		return self.freq
		
	def peri_write(self, register, data):
		
		if register not in self.ssa_peri_reg_map.keys():
			print "Register name not found"
			rep = False

		else: 
			base = ssa_peri_reg_map[register]
			adr  = (base & 0x0fff) | 0b0001000000000000
			rep  = write_I2C('SSA', adr, data, self.freq)

		return rep

	def peri_read(self, register, timeout = 0.001):
		
		if register not in self.ssa_peri_reg_map.keys():
			print "Register name not found"
			rep = False

		else: 
			base = ssa_peri_reg_map[register]
			adr  = (base & 0xfff) | 0b0001000000000000
			rep  = read_I2C('SSA', adr, timeout)

		return rep

	def strip_write(self, register, strip, data):

		if register not in self.ssa_strip_reg_map.keys():
			print "Register name not found"
			rep = False

		else: 
			strip_id = strip if (strip is not 'all') else 0b00000000
			base = ssa_strip_reg_map[register]
			adr  = ((base & 0x000f) << 8 ) & (strip_id & 0b01111111) 
			rep  = write_I2C('SSA', adr, data, self.freq)

		return rep

	def strip_read(self, register, strip, timeout = 0.001):

		if register not in self.ssa_strip_reg_map.keys():
			print "Register name not found"
			rep = False

		else: 
			strip_id = strip if (strip is not 'all') else 0b00000000
			base = ssa_strip_reg_map[register]
			adr  = ((base & 0x000f) << 8 ) & (strip_id & 0b01111111) 
			rep  = read_I2C('SSA', adr, timeout)

		return rep

I2C = ssa_i2c_conf()
