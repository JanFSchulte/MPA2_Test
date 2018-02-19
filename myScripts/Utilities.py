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

class Utilities: 

	class cl_clustdispl(float):
	    def __repr__(self):
	        return "{:6.1f}".format(self)

	def ShowPercent(self, val , max = 100, message = ""): 
		i = int( (float(val)/max) * 100.0) - 1
		#row = ""*i + message
		row = "\t" + message 
		sys.stdout.write("%s\r%d%%" %(row, i + 1))
		sys.stdout.flush()
		time.sleep(0.001)
		if (i == 99): 
			sys.stdout.write('\n')

	def print_enable(self, ctr = True):
		if(ctr):
			sys.stdout = sys.__stdout__
		else: 
			sys.stdout = open(os.devnull, "w")

	def cl2str(self, clist = [0]):
		if isinstance(clist, list):
			if len(clist) > 0: 
				rstr = str(map(self.cl_clustdispl, clist))
			else: 
				rstr = "[      ]"
		else:
			rstr = "[{:6.1f}]".format(clist)
		return rstr

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


def print_method(name):
	lines = inspect.getsourcelines(name)
	print("".join(lines[0]))

utils = Utilities()

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

def f_errorfc(x, *p):
    a, mu, sigma = p
    return a*0.5*erfc((x-mu)/sigma)





