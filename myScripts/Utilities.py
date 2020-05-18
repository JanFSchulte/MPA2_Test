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
from scipy.interpolate import BSpline as interpspline
from multiprocessing import Process
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from datetime import datetime
import threading

class FuncThread(threading.Thread):
	def __init__(self, target, *args):
		self._target = target
		self._args = args
		threading.Thread.__init__(self)
	def run(self):
		self._target(*self._args)

class curstate():
	def __init__(self, **kwds):
		self.__dict__.update(kwds)

class Utilities:

	def __init__(self):
		self.logfile = False
		self.errorlog = False
		self.generic_parameters = {}
		p = []

	class cl_clustdispl(float):
		def __repr__(self):
			return "{:6.1f}".format(self)

	def set_log_files(self, logfile, errorlog):
		if(self.logfile): self.logfile.close()
		if(self.errorlog): self.errorlog.close()
		self.logfile = open(logfile, "w")
		self.errorlog = open(errorlog, "w")

	def close_log_files(self):
		if(self.logfile): self.logfile.close()
		if(self.errorlog): self.errorlog.close()
		self.logfile = False
		self.errorlog = False

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
			print('->  \tEnabled I2C master for chips control')

	def date_time(self, format='print'):
		if(format == 'print'):
			return datetime.now().strftime("%Y-%m-%d_%H-%M")
		elif(format == 'csv'):
			return datetime.now().strftime("%Y, %m, %d, %H, %M, %S")
		elif(format == 'array'):
			return (datetime.now().strftime("%Y, %m, %d, %H, %M, %S")).split(', ')
		else:
			return datetime.now().strftime("%Y-%m-%d_%H-%M")


	def print_error(self, text, logfile = False):
		sys.stdout.write("\033[1;31m")
		print(str(text))
		sys.stdout.write("\033[0;0m")
		if(self.logfile):
			self.logfile.write(str(text)+"\n")
		if(self.errorlog):
			self.errorlog.write(str(text)+"\n")


	def print_warning(self, text, logfile = False):
		sys.stdout.write("\033[1;33m")
		print(str(text))
		sys.stdout.write("\033[0;0m")
		if(self.logfile):
			self.logfile.write(str(text)+"\n")

	def print_info(self, text, logfile = False):
		sys.stdout.write("\033[1;34m")
		print(str(text))
		sys.stdout.write("\033[0;0m")
		if(self.logfile):
			self.logfile.write(str(text)+"\n")

	def print_good(self, text, logfile = False):
		sys.stdout.write("\033[1;32m")
		print(str(text))
		sys.stdout.write("\033[0;0m")
		if(self.logfile):
			self.logfile.write(str(text)+"\n")

	def print_log(self, text, logfile = False):
		print(str(text))
		if(self.logfile):
			self.logfile.write(str(text)+"\n")

def print_method(name):
	lines = inspect.getsourcelines(name)
	print("".join(lines[0]))

utils = Utilities()


def f_errorf(x, *p):
	a, mu, sigma = p
	#    print(x)
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
