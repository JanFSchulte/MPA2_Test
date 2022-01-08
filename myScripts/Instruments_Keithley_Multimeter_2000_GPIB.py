import time
try:
	import Gpib
except ImportError:
	print("->  Impossible to access GPIB instruments")

class Instruments_Keithley_Multimeter_2000_GPIB():
	def __init__(self, connect=True, avg = 5, address = 16):
		if(connect):
			self.connect(avg=avg, address=address)

	def connect(self, address = 16, avg = 5):
		try:
			print("->  Connecting to Multimeter on GPIB address " + str(address))
			self.inst = Gpib.Gpib(0, address)
			self.inst.write(":SENS:FUNC 'VOLT:DC'")
			if (avg > 0):
				self.inst.write(":SENS:VOLT:DC:NPLC 1; AVER:COUN %d" % int(avg))
				self.inst.write(":SENS:VOLT:DC:AVER:STAT ON")
			self.inst.write(":FORM:ELEM READ")
		except:
			print('->  Impossible to establish the connection with Multimeter via GPIB on address {:d}'.format(address))
			self.inst = False
		return self.inst

	def measure(self):
		self.inst.write("READ?")
		str_value = self.inst.read(100)
		value = float(str_value)
		#self.inst.write(":DISP:WIND2:TEXT:DATA \"  %8.3f mV\";STAT ON;" % (value*1E3))
		return value

# For MPA methods
keithley_multimeter = Instruments_Keithley_Multimeter_2000_GPIB

# multimeter = keithley_multimeter()
