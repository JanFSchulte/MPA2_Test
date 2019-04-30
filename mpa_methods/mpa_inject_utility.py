from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import random

class MPA_inject():
	def __init__(self, I2C, FC7, ctrl_base, ctrl_pix):
		self.I2C = I2C
		self.FC7 = FC7
		self.ctrl_base = ctrl_base
		self.ctrl_pix = ctrl_pix

	def send_pulses(self, n_pulse):
		self.FC7.open_shutter()
		sleep(0.01)
		for i in range(0, n_pulse):
			self.FC7.send_test()
			sleep(0.1)
		sleep(0.001)
		self.FC7.close_shutter()
	def send_pulses_fast(self, n_pulse, row, pixel, cal):
		self.ctrl_pix.disable_pixel(0, 0)
		self.ctrl_pix.enable_pix_counter(row, pixel)
		#self.ctrl_pix.enable_pix_disable_ancal(row, pixel)
		sleep(0.0025)
		try:
			self.FC7.open_shutter(8)
		except ChipsException:
			print "Error ChipsException, repeat command"
			sleep (0.001)
			self.FC7.open_shutter(8)
		if (cal != 0):
			self.FC7.SendCommand_CTRL("start_trigger")
			test = 1
			while (test):
				test = self.FC7.read("stat_fast_fsm_state")
				sleep(0.001)
		else:
			sleep(0.000001*n_pulse)
		try:
			self.FC7.close_shutter(8)
		except ChipsException:
			print "Error ChipsException, repeat ccommand"
			sleep (0.001)
			self.FC7.close_shutter(8)
	def send_pulses_fast_all(self, n_pulse, row, pixel, cal):
		self.ctrl_pix.disable_pixel(0, 0)
		for r in row:
			for p in pixel:
				self.ctrl_pix.enable_pix_disable_ancal(r, p)
				#enable_pix_counter(r,p)
		sleep(0.0025)
		try:
			self.FC7.open_shutter(8)
		except ChipsException:
			print "Error ChipsException, repeat ccommand"
			sleep (0.001)
			self.FC7.open_shutter(8)
		if (cal != 0):
			self.FC7.SendCommand_CTRL("start_trigger")
			test = 1
			while (test):
				test = self.FC7.read("stat_fast_fsm_state")
				sleep(0.001)
		else:
			sleep(1*n_pulse)
		try:
			self.FC7.close_shutter(8)
		except ChipsException:
			print "Error ChipsException, repeat ccommand"
			sleep (0.001)
			self.FC7.close_shutter(8)
	def inject(self):
		sleep(0.005)
		self.FC7.open_shutter(8)
		if (cal != 0):
			sleep(0.005)
			self.FC7.SendCommand_CTRL("start_trigger")
			test = 1
			while (test):
				test = self.FC7.read("stat_fast_fsm_state")
				sleep(0.001)
		else:
			sleep(0.000001*n_pulse)
			self.FC7.close_shutter(8)
