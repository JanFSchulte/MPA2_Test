import numpy as np
import time
import sys

class Utilities: 

	def ShowPercent(self, val , max = 100): 
		i = int( (float(val)/max) * 100.0) - 1
		row = ""*i + "   "
		sys.stdout.write("%s\r%d%%" %(row, i + 1))
		sys.stdout.flush()
		time.sleep(0.01)


utils = Utilities()