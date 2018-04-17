import csv
from d19cScripts import *
from myScripts import *
import time
ipaddr, fc7AddrTable, fc7 = SelectBoard('MPA') 
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.fast_readout_utility import *
from mpa_methods.bias_calibration import *
from mpa_methods.power_utility import *

def colprint(text):
	sys.stdout.write("\033[1;31m")
	print(str(text))
	sys.stdout.write("\033[0;0m")

class ProbeMeasurement:
	def __init__(self, tag):
		self.STATUS = [0,0,0,0]
		self.start = time.time()
		self.tag = tag # UNIQUE ID
		colprint("Creating new chip measurement: "+tag)
		self.DIR = "ProbeStationResults/"+tag
		if not os.path.exists(self.DIR):	os.makedirs(self.DIR)
		try:
			power_on()
			self.STATUS[0] = 1
		except:
			colprint("-= UNABLE TO POWER ON! =-")
	def CalibChip(self):
		if self.STATUS[0]:
			colprint("Calibrating")
			try:
				self.CV = calibrate_chip()
				print self.CV
				self.STATUS[1] = 1
			except:
				colprint("-= UNABLE TO CALIBRATE! =-")
	def Align(self):
		if self.STATUS[0]:
			colprint("Aligning")
			self.aligned = align_MPA()
			if self.aligned:
				colprint("... Aligned!")
				self.STATUS[2] = 1
			else:
				colprint("-= UNABLE TO ALIGN! =-")
	def TrimDACs(self):
		if self.STATUS[0]:
			colprint("Trimming")
			try:
				trimDAC_amplitude(20)
			except:
				colprint("-= UNABLE TO TRIM! =-")
				
				
	def Save(self):
		if self.STATUS[0]:
			power_off()
		if self.STATUS[1]:
			with open(self.DIR+'/CAL_VDACs.csv', 'wb') as csvfile:
		   		CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
				for i in self.CV: CVwriter.writerow(i)
		end = time.time()
		colprint("Measurement took: " + str(end - self.start))
		colprint("STATUS = " + str(self.STATUS))

if __name__ == '__main__': # TEST
	TEST = ProbeMeasurement("TEST")
	TEST.CalibChip()
	TEST.Align()
	TEST.TrimDACs()
	TEST.Save()
