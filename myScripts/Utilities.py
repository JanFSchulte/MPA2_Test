import numpy as np
import time
import sys
import os

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

def print_method(name):
	lines = inspect.getsourcelines(name)
	print("".join(lines[0]))


utils = Utilities()




