# to load: from mpa_methods.mpa_i2c_conf import *
from myScripts.BasicD19c import *
execfile('mpa_methods/mpa_reg_map.py')

class mpa_i2c_conf:

	def __init__(self):
		self.mpa_peri_reg_map = mpa_peri_reg_map
		self.mpa_pixel_reg_map = mpa_pixel_reg_map
		self.freq = 0

	def set_freq(self, value):
		self.freq = value
		return True

	def get_freq(self, value):
		return self.freq

	def peri_write(self, register, data):

		if register not in self.mpa_peri_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			base = mpa_peri_reg_map[register]
			#adr  = (base & 0x0fff) | 0b0001000000000000
			adr   = base
			rep  = write_I2C('MPA', adr, data, self.freq)

		#return rep

	def peri_read(self, register):

		if register not in self.mpa_peri_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			base = mpa_peri_reg_map[register]
			#adr  = (base & 0xfff) | 0b0001000000000000
			adr   = base
			rep  = read_I2C('MPA', adr, 0, self.freq)

	#	return rep

	def pixel_write(self, register, row, pixel, data):

		if register not in self.mpa_pixel_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			pixel_id = pixel if (pixel is not 'all') else 0b00000000
			base = mpa_pixel_reg_map[register]
			adr  = ((row & 0x0000f) << 11 ) | ((base & 0x000f) << 7 ) | (pixel_id & 0b01111111)
			print bin(adr)
			rep  = write_I2C('MPA', adr, data, self.freq)

		#return rep

	def pixel_read(self, register, row, pixel):

		if register not in self.mpa_pixel_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			pixel_id = pixel if (pixel is not 'all') else 0b00000000
			base = mpa_pixel_reg_map[register]
			adr  = ((row & 0x0000f) << 11 ) | ((base & 0x000f) << 7 ) | (pixel_id & 0b01111111)
			print bin(adr)
			rep  = read_I2C('MPA', adr, 0, self.freq)

		#return rep

I2C=mpa_i2c_conf()
