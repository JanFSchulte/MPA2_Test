from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt

class mpa_ctrl_pix:
	def __init__(self, I2C, FC7, pwr, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map):
		self.mpa_peri_reg_map = mpa_peri_reg_map;
		self.mpa_row_reg_map = mpa_row_reg_map;
		self.mpa_pixel_reg_map = mpa_pixel_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
	def disable_pixel(self, r, p):
		self.I2C.pixel_write('PixelEnables', r, p, 0x00)
		#self.I2C.pixel_write('ModeSel', r, p, 0x00)
# Pixel mode selection
	def enable_pix_counter(self, r, p):
		self.I2C.pixel_write('PixelEnables', r, p, 0x53)
	def enable_pix_disable_ancal(self, r,p):
		self.I2C.pixel_write('PixelEnables', r, p, 0x13)
	def enable_pix_sync(self, r,p):
		self.I2C.pixel_write('PixelEnables', r, p, 0x53)

	def enable_pix_EdgeBRcal(self, r,p, polarity = "rise"):
		self.I2C.row_write('PixelControl', r, 0x14)
		if (polarity == "rise"):
			self.I2C.pixel_write('PixelEnables', r, p, 0x57) # with pixel counter for debugging
		elif (polarity == "fall"):
			self.I2C.pixel_write('PixelEnables', r, p, 0x55) # with pixel counter for debugging
		else:
			print("Polarity not recognized")
			return
	def enable_pix_LevelBRcal(self, r,p, polarity = "rise"):
		self.I2C.pixel_write('ModeSel', r, p, 0b01)
		if (polarity == "rise"):
			self.I2C.pixel_write('PixelEnables', r, p, 0x5b) # with pixel counter for debugging
		elif (polarity == "fall"):
			self.I2C.pixel_write('PixelEnables', r, p, 0x59) # with pixel counter for debugging
		else:
			print("Polarity not recognized")
			return
	def enable_dig_cal(self, r,p, pattern = 0b00000001):
		self.I2C.pixel_write('PixelEnables', r, p, 0x20)
		self.I2C.pixel_write('DigPattern', r, p, pattern)
	def load_trim(self, trim_array):
		count = 0
		for r in range(0,16):
			for p in range(0,118):
				trim_val = trim_array[r*118+p]
				if trim_val > -1 and trim_val < 32: self.I2C.pixel_write("TrimDAC",r+1,p+2, trim_val)
				elif trim_val < 0: self.I2C.pixel_write("TrimDAC",r+1,p+2, 0); count += 1#print "Low Trim Row", r, "Pixel", p, "Value", trim_val
				elif trim_val > 31: self.I2C.pixel_write("TrimDAC",r+1,p+2, 31); count += 1#print "High Trim Row", r, "Pixel", p, "Value", trim_val - 31
				else: print(r, p)
		return count

	def reset_trim(self, value = 15):
		self.I2C.pixel_write("TrimDAC",0,0,value)
	def read_pixel_counter(self, row, pixel):
		data1 = self.I2C.pixel_read('ReadCounter_LSB',row, pixel)
		data2 = self.I2C.pixel_read('ReadCounter_MSB',row, pixel)
		if ((data1 == None) or (data2 == None)):
			data1 = self.I2C.pixel_read('ReadCounter_LSB',row, pixel, 0.01) # Repeat with higher timeout time
			data2 = self.I2C.pixel_read('ReadCounter_MSB',row, pixel, 0.01) # Repeat with higher timeout time
		if ((data1 == None) or (data2 == None)):
			time.sleep(1)
			activate_I2C_chip(verbose = 0)
			time.sleep(1)
			data1 = self.I2C.pixel_read('ReadCounter_LSB',row, pixel, 0.01) # Repeat with higher timeout time
			data2 = self.I2C.pixel_read('ReadCounter_MSB',row, pixel, 0.01) # Repeat with higher timeout time
		if ((data1 == None) or (data2 == None)):
			print("Error Reading I2C")
			data = 0
		else:
			data = ((data2 & 0x0ffffff) << 8) | (data1 & 0x0fffffff)
		return data
