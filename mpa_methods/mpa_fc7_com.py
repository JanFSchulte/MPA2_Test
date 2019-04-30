import numpy as np
import time
import sys
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm
from scipy.interpolate import spline as interpspline
from multiprocessing import Process
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from datetime import datetime

class ssa_fc7_com():
	def __init__(self, fc7_if):
		self.fc7 = fc7_if

	def compose_fast_command(self, duration = 0, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 0):
		encode_resync = fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(resync_en)
		encode_l1a = fc7AddrTable.getItem("ctrl_fast_signal_trigger").shiftDataToMask(l1a_en)
		encode_cal_pulse = fc7AddrTable.getItem("ctrl_fast_signal_test_pulse").shiftDataToMask(cal_pulse_en)
		encode_bc0 = fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(bc0_en)
		encode_duration = fc7AddrTable.getItem("ctrl_fast_signal_duration").shiftDataToMask(duration)
		self.write("ctrl_fast", encode_resync + encode_l1a + encode_cal_pulse + encode_bc0 + encode_duration)

	def start_counters_read(self, duration = 0):
		self.compose_fast_command(duration, resync_en = 1, l1a_en = 0, cal_pulse_en = 0, bc0_en = 1)

	def send_resync(self):
		self.SendCommand_CTRL("fast_fast_reset")

	def send_trigger(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 0)

	def open_shutter(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 0)

	def send_test(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 0, cal_pulse_en = 1, bc0_en = 0)

	def orbit_reset(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 1)

	def close_shutter(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 0, cal_pulse_en = 0, bc0_en = 1)

	def reset(self):
		self.SendCommand_CTRL("global_reset")

	def clear_counters(self,duration = 0):
		self.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 1)

	def write(self, p1, p2, p3 = 0):
		cnt = 0
		while cnt < 4:
			try:
				return self.fc7.write(p1, p2, p3)
				break
			except:
				print '=>  \tTB Communication error - fc7_write'
				time.sleep(0.1)
				cnt += 1

	def read(self, p1, p2 = 0):
		cnt = 0
		while cnt < 4:
			try:
				return self.fc7.read(p1, p2)
				break
			except:
				print '=>  \tTB Communication error - fc7_read'
				time.sleep(0.1)
				cnt += 1

	def blockRead(self, p1, p2, p3 = 0):
		cnt = 0
		while cnt < 4:
			try:
				return self.fc7.blockRead(p1, p2, p3)
				break
			except:
				print '=>  \tTB Communication error - fc7_read_block'
				time.sleep(0.1)
				cnt += 1

	def fifoRead(self, p1, p2, p3 = 0):
		cnt = 0
		while cnt < 4:
			try:
				return self.fc7.fifoRead(p1, p2, p3)
				break
			except:
				print '=>  \tTB Communication error - fc7_read_fifo'
				time.sleep(0.1)
				cnt += 1

	def SendCommand_CTRL(self, p1):
		cnt = 0
		while cnt < 4:
			try:
				return SendCommand_CTRL(p1)
				break
			except:
				print '=>  \tTB Communication error - SendCommand_CTRL'
				time.sleep(0.1)
				cnt += 1
