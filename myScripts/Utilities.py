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

class curstate():
	def __init__(self, **kwds):
		self.__dict__.update(kwds)

class Utilities:

	def __init__(self):
		p = []

	class cl_clustdispl(float):
		def __repr__(self):
			return "{:6.1f}".format(self)

	def reverse_bit_order(self, n, width = 32):
		b = '{:0{width}b}'.format(n, width=width)
		r = int(b[::-1], 2)
		return r

	def ShowPercent(self, val , max = 100, message = ""):
		i = int( (float(val)/max) * 100.0) - 1
		row = "\t" + message
		sys.stdout.write("%s\r%d%%" %(row, i + 1))
		sys.stdout.flush()
		time.sleep(0.001)
		if (i == 99):
			sys.stdout.write('\n')

	def linear_fit(self, xdata, ydata):
		par, cov = curve_fit(
			f= f_line,
			xdata = np.array(xdata),
			ydata = np.array(ydata),
			p0 = [0, 0])
		gain = par[0]
		offset = par[1]
		sigma = np.sqrt(np.diag(cov))
		return gain, offset, sigma

	def smuth_plot(self, y, x, par = '', r=10):
		xnew = np.linspace(x[0],x[-1], (len(x)-1)*10+1)
		ynp  = np.transpose(np.array(y))
		dim  = len(ynp.shape)
		if(dim == 1):
			ynew = interpspline(x,y,xnew)
			plt.plot(xnew, ynew, par)
		elif(dim == 2):
			for i in ynp:
				ynew = interpspline(x,i,xnew)
				plt.plot(xnew, ynew, par)
		else:
			return False

	def cl2str(self, clist = [0]):
		if isinstance(clist, list):
			if len(clist) > 0:
				rstr = str(map(self.cl_clustdispl, clist))
			else:
				rstr = "[      ]"
		else:
			rstr = "[{:6.1f}]".format(clist)
		return rstr

	def __plot_graph(self, *args):
	    plt.show()

	def PltPlot(self, data, show = True):
		plt.plot(data)
		self.p.append( Process(target=self.__plot_graph, args='') )
		self.p[-1].start()

	def PltShow(self):
		self.p.append( Process(target=self.__plot_graph, args='') )
		self.p[-1].start()

	def PltClose(self):
		for i in p:
			i.join()

	def print_enable(self, ctr = True):
		if(ctr):
			sys.stdout = sys.__stdout__
		else:
			sys.stdout = open(os.devnull, "w")

	def activate_I2C_chip(self, pr = ''):
		if(not pr == 'debug'):
			self.print_enable(False)
		activate_I2C_chip()
		if(not pr == 'debug'):
			self.print_enable(True)
		if(pr == 'print'):
			print '->  \tEnabled I2C master for chips control'

	def date_time(self):
		st = datetime.now().strftime("%Y-%m-%d_%H:%M")
		return st

def print_method(name):
	lines = inspect.getsourcelines(name)
	print("".join(lines[0]))

utils = Utilities()

class fc7_com():
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





def f_errorf(x, *p):
	a, mu, sigma = p
	#    print x
	return 0.5*a*(1.0+erf((x-mu)/sigma))

def f_line(x, *p):
	g, offset = p
	return  np.array(x) *g + offset

def f_gauss(x, *p):
	A, mu, sigma = p
	return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def f_gauss1(x, A, mu, sigma):
	'''1-d gaussian: gaussian(x, A, mu, sigma)'''
	return A * np.exp(-(x-mu)**2 / (2.*sigma**2))

def f_errorfc(x, *p):
	a, mu, sigma = p
	return a*0.5*erfc((x-mu)/(sigma*np.sqrt(2)))
