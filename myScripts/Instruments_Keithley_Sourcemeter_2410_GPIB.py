import time

try:
	import Gpib
except ImportError:
	print("->  Impossible to access GPIB instruments")


'''
Initialize:
	connect()

VOLTAGE SOURCE:
	config__voltage_source()
	set_voltage()
	get_current()
	output_enable()
	output_disable()

VOLTAGE MEASURE:
	config__voltage_measure()
	get_voltage()

'''

class Instruments_Keithley_Sourcemeter_2410_GPIB():
	def __init__(self, connect=False, avg = 5, address = 16):
		self.name = ''
		self.mode = ''
		self.inst = False
		if(connect):
			self.connect(avg=avg, address=address)

	def connect(self, address = 16, avg=1):
		try:
			print("->  Connecting to Sourcemeter on GPIB address " + str(address))
			time.sleep(0.1); self.inst = Gpib.Gpib(0, address)
			time.sleep(0.1); self.inst.write('*RST')
			time.sleep(0.1); self.inst.write("OUTPut OFF")
			time.sleep(0.1); self.inst.write("*IDN?")
			time.sleep(0.1); self.name = self.inst.read(100)
			print("    Return device name: " + str(self.name))
			self.config__voltage_measure()
		except:
			print('->  Impossible to establish the connection with Sourcemeter via GPIB on address {:d}'.format(address))
			self.inst = False

	def disable(self):
		if(not self.inst): return
		self.inst.write('*RST')
		self.inst.write(':OUTP OFF')

	############## VOLTAGE SOURCE - CURRENT MEASURE ######################################

	def config__voltage_source(self, compliance=10E-3, range=2):
		if(not self.inst): return False
		self.inst.write('*RST')
		self.inst.write(':SOUR:FUNC VOLT')
		self.inst.write(':SOUR:VOLT:MODE FIXED')
		self.inst.write(':SOUR:VOLT:RANG {:0d}'.format(range))
		self.inst.write(':SOUR:VOLT:LEV 0')
		self.inst.write(':SENS:CURR:PROT {:0.3E}'.format(compliance))
		self.inst.write(':SENS:FUNC "CURR"')
		self.inst.write(':SENS:CURR:RANG {:0.3E}'.format(compliance))
		self.inst.write(':FORM:ELEM CURR')
		self.inst.write(':OUTP ON')
		self.mode = 'VSOURCE'
		print('->  Sourcemeter configured for voltage source - current measurement')

	def output_enable(self):
		if(not self.__check_vsource_mode()): return
		self.inst.write(':OUTP ON')
		return True

	def output_disable(self):
		if(not self.__check_vsource_mode()): return
		self.inst.write(':OUTP OFF')

	def set_voltage(self, value=0):
		if(not self.__check_vsource_mode()):
			return
		if(value>1.4 or value<-0.3):
			print('->  You are trying to set a dangerous voltage for the chip {:0.3f}. Are you sure about?'.format(value))
			return
		self.inst.write(':SOUR:VOLT:LEV {:0.3E}'.format(value))

	def get_current(self):
		if(not self.__check_vsource_mode()): return
		return self.__read()


	############## VOLTAGE MEASURE ######################################

	def config__voltage_measure(self, range=1):
		self.inst.write('*RST')
		self.inst.write(':SOUR:FUNC CURR')
		self.inst.write(':SOUR:CURR:MODE FIXED')
		self.inst.write(':SENS:FUNC "VOLT"')
		self.inst.write(':SOUR:CURR:RANG MIN')
		self.inst.write(':SOUR:CURR:LEV 0')
		self.inst.write(':SENS:VOLT:PROT 1.5')
		self.inst.write(':SENS:VOLT:RANG {:0d}'.format(range))
		self.inst.write(':FORM:ELEM VOLT')
		self.inst.write(':OUTP ON')
		self.mode = 'VMEASURE'
		print('->  Sourcemeter configured for voltage measurement')

	def get_voltage(self):
		if(not self.__check_vmeasure_mode()): return
		return self.__read()


	############## COMPATIBILITY METHODS ######################################
	#for keeping the same mathods names as other instruments

	def measure(self):
		return self.get_voltage()

	def reset(self):
		return self.disable()

	############## PRIVATE METHODS ######################################

	def __check_vsource_mode(self):
		if((self.mode == 'VSOURCE') and (self.inst)):
			return True
		else:
			print('->  Please configure sourcemeter as voltage source before to call this method.')
			return False

	def __check_vmeasure_mode(self):
		if((self.mode == 'VMEASURE') and (self.inst)):
			return True
		else:
			print('->  Please configure sourcemeter as voltage measurement before to call this method.')
			return False

	def __read(self):
		if(not self.inst): return False
		self.inst.write("READ?")
		str_value = self.inst.read()
		value = float(str_value)
		return value





# multimeter = keithley_multimeter()
