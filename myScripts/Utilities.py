import numpy as np
import time
import sys

class cl_clustdispl(float):
    def __repr__(self):
        return "{:6.1f}".format(self)

def cl2str(clist = [0]):
	if isinstance(clist, list):
		if len(clist) > 0: 
			rstr = str(map(cl_clustdispl, clist))
		else: 
			rstr = "[      ]"
	else:
		rstr = "[{:6.1f}]".format(clist)
	return rstr
	
class Utilities: 
	
	def ShowPercent(self, val , max = 100, message = ""): 
		i = int( (float(val)/max) * 100.0) - 1
		#row = ""*i + message
		row = "\t" + message 
		sys.stdout.write("%s\r%d%%" %(row, i + 1))
		sys.stdout.flush()
		time.sleep(0.001)
		if (i == 99): 
			sys.stdout.write('\n')

utils = Utilities()




