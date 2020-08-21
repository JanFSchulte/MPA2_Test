import time
try:
	import Gpib
except ImportError:
	print("->  Impossible to access GPIB instruments")

class keithley_multimeter():
	def __init__(self, connect=False, avg = 5, address = 16):
		if(connect):
			self.init_keithley()

	def init_keithley(self, avg = 5, address = 16):
		try:
			#print("->  \tConnecting to Multimeter on GPIB address " + str(address))
			inst = Gpib.Gpib(0, address)

			# reset and clear
			#inst.write("*RST")
			#inst.write("*CLR")
			#time.sleep(0.1)
			# idn
			#inst.write("*IDN?")
			#print(inst.read(100))

			# don't know what is that
			#inst.write(":SYST:AZER:TYPE SYNC")
			#inst.write(":SYST:LSYN:STAT ON")
			# measure dc voltage
			inst.write(":SENS:FUNC 'VOLT:DC'")
			# we averaging, resolution number of samples
			if (avg > 0):
				inst.write(":SENS:VOLT:DC:NPLC 1; AVER:COUN %d" % int(avg))
				#inst.write(":SENS:VOLT:DC:DIG 9; NPLC 10; AVER:COUN 5; TCON REP")
				inst.write(":SENS:VOLT:DC:AVER:STAT ON")
			# range
			#inst.write(":SENS:VOLT:DC:RANG")
			# the format of the query
			inst.write(":FORM:ELEM READ")
			# write empty to the display
			#inst.write(":DISP:WIND:TEXT:DATA \"               \";STAT ON;")
		except:
			print('->  Impossible to establish the connection with Multimeter via GPIB on address {:d}'.format(address))
			inst = False
		return inst

	def measure(self, inst):
		inst.write("READ?")
		str_value = inst.read()
		value = float(str_value)
		#inst.write(":DISP:WIND2:TEXT:DATA \"  %8.3f mV\";STAT ON;" % (value*1E3))
		return value


# multimeter = keithley_multimeter()