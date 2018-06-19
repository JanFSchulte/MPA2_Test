# to load: from mpa_methods.mpa_i2c_conf import *
from myScripts.BasicD19c import *
import numpy as np
import time
import sys
import math
execfile('mpa_methods/mpa_reg_map.py')

class mpa_i2c_conf:

	def __init__(self):
		self.mpa_peri_reg_map = mpa_peri_reg_map
		self.mpa_pixel_reg_map = mpa_pixel_reg_map
		self.mpa_row_reg_map = mpa_row_reg_map
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

	def peri_read(self, register, timeout = 0.001):

		if register not in self.mpa_peri_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			base = mpa_peri_reg_map[register]
			#adr  = (base & 0xfff) | 0b0001000000000000
			adr   = base
			rep  = read_I2C('MPA', adr, timeout)
		return rep



	def row_write(self, register, row, data):

		if register not in self.mpa_row_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			pixel_id = 0b1111001
			base = mpa_row_reg_map[register]
			adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | pixel_id
			#print bin(adr)
			rep  = write_I2C('MPA', adr, data, self.freq)

	def row_read(self, register, row, timeout = 0.001):

		if register not in self.mpa_row_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			pixel_id = 0b1111001
			base = mpa_row_reg_map[register]
			adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | pixel_id
			#print bin(adr)
			rep  = read_I2C('MPA', adr, timeout)
		return rep

	def pixel_write(self, register, row, pixel, data):

		if register not in self.mpa_pixel_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			pixel_id = pixel if (pixel is not 'all') else 0b00000000
			base = mpa_pixel_reg_map[register]
			adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | (pixel_id & 0xfffffff)
			#print bin(adr)
			rep  = write_I2C('MPA', adr, data, self.freq)

		#return rep

	def pixel_read(self, register, row, pixel, timeout = 0.001):

		if register not in self.mpa_pixel_reg_map.keys():
			print "Register name not found"
			rep = False

		else:
			pixel_id = pixel if (pixel is not 'all') else 0b00000000
			base = mpa_pixel_reg_map[register]
			adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | (pixel_id & 0xfffffff)
			#print bin(adr)
			rep  = read_I2C('MPA', adr, timeout)
			if rep == None:
				sleep(1)
				activate_I2C_chip(verbose = 0)
				sleep(1)
				rep  = read_I2C('MPA', adr, timeout)

		return rep

	def peri_test(self):
		t0 = time.time()
		activate_I2C_chip(verbose = 0)
		read_reg = ['SEUcntPeri', 'ErrorL1', 'OFcnt', 'EfuseValue0', 'EfuseValue1','EfuseValue2','EfuseValue3', 'test']
		cnt = 0
		for reg in self.mpa_peri_reg_map.keys():
			if all(reg_check != reg for reg_check in read_reg ):
				value = self.peri_read(reg)
				self.peri_write(reg, 255)
				max_value = self.peri_read(reg)
				if (max_value == 0):
					print "Error in register: ", reg, " --> Max Value = 0"
				else:
					for i in range(0,max_value+1):
						self.peri_write(reg, i)
						check = self.peri_read(reg)
						if (check != i):
							print "Error in register: ", reg, " for value: ", i, " obtained: ", check
							cnt += 1
				self.peri_write(reg, value)
		print "Error Counter: ", cnt
		t1 = time.time()
		print "END"
		print "Trimming Elapsed Time: " + str(t1 - t0)

	def row_test(self):
		t0 = time.time()
		activate_I2C_chip(verbose = 0)
		read_reg = ['SEUcntRow', 'test']
		cnt = 0
		for row in range(1,17):
			print "Testing Row: ", row
			for reg in self.mpa_row_reg_map.keys():
				if all(reg_check != reg for reg_check in read_reg ):
					value = self.row_read(reg, row)
					self.row_write(reg, row, 255)
					max_value = self.row_read(reg, row)
					if (max_value == 0):
						print "Error in register: ", reg, " --> Max Value = 0"
					else:
						for i in range(0,max_value+1):
							self.row_write(reg, row,  i)
							check = self.row_read(reg, row)
							if (check != i):
								print "Error in register: ", reg, " for value: ", i, " obtained: ", check
								cnt += 1
						self.row_write(reg, row, value)

						#print "Test finished: ", reg, " for row: ", row
		print "Error Counter: ", cnt
		t1 = time.time()
		print "END"
		print "Trimming Elapsed Time: " + str(t1 - t0)

	def pixel_test(self):
		t0 = time.time()
		activate_I2C_chip(verbose = 0)
		read_reg = ['ReadCounter_LSB', 'ReadCounter_MSB', 'test']
		cnt = 0
		for row in range(1,17):
			print "Testing Row: ", row
			for pixel in range(1,121):
				for reg in self.mpa_pixel_reg_map.keys():
					if all(reg_check != reg for reg_check in read_reg ):
						value = self.pixel_read(reg, row, pixel)
						self.pixel_write(reg, row, pixel, 255)
						max_value = self.pixel_read(reg, row, pixel)
						if (max_value == 0):
							print "Error in register: ", reg, " --> Max Value = 0"
						else:
							for i in range(0,max_value+1):
								self.pixel_write(reg, row, pixel,  i)
								check = self.pixel_read(reg, row, pixel)
								if (check != i):
									print "Error in register: ", reg, " for value: ", i, " obtained: ", check
									cnt += 1
						self.pixel_write(reg, row, pixel, value)

							#print "Test finished: ", reg, " for row: ", row, " for pixel: ", pixel
		print "Error Counter: ", cnt
		t1 = time.time()
		print "END"
		print "Trimming Elapsed Time: " + str(t1 - t0)

	def chip_test():
		print "This test will take around 35 minutes"
		print "Periphery test starting..."
		peri_test()
		print "Rows test starting..."
		row_test()
		print "Pixels test starting..."
		pixel_test()


I2C=mpa_i2c_conf()
