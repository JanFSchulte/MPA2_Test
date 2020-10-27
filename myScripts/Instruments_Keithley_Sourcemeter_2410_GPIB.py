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
			time.sleep(0.1); self.__write('*RST')
			time.sleep(0.1); self.__write("OUTPut OFF")
			time.sleep(0.1); self.__write("*IDN?")
			time.sleep(0.1); self.name = self.inst.read(100)
			print("    Return device name: " + str(self.name))
			self.config__voltage_measure()
		except:
			print('->  Impossible to establish the connection with Sourcemeter via GPIB on address {:d}'.format(address))
			self.inst = False

	def disable(self):
		if(not self.inst): return
		self.__write('*RST')
		self.__write(':OUTP OFF')

	############## VOLTAGE SOURCE - CURRENT MEASURE ######################################

	def config__voltage_source(self, compliance=10E-3, range=2):
		if(not self.inst): return False
		self.__write('*RST')
		self.__write(':SOUR:FUNC VOLT')
		self.__write(':SOUR:VOLT:MODE FIXED')
		self.__write(':SOUR:VOLT:RANG {:0d}'.format(range))
		self.__write(':SOUR:VOLT:LEV 0')
		self.__write(':SENS:CURR:PROT {:0.3E}'.format(compliance))
		self.__write(':SENS:FUNC "CURR"')
		self.__write(':SENS:CURR:RANG {:0.3E}'.format(compliance))
		self.__write(':FORM:ELEM CURR')
		self.__write(':OUTP ON')
		self.mode = 'VSOURCE'
		print('->  Sourcemeter configured for voltage source - current measurement')

	def output_enable(self):
		if(not self.__check_vsource_mode()): return
		self.__write(':OUTP ON')
		return True

	def output_disable(self):
		if(not self.__check_vsource_mode()): return
		self.__write(':OUTP OFF')

	def set_voltage(self, value=0):
		if(not self.__check_vsource_mode()):
			return
		if(value>1.4 or value<-0.3):
			print('->  You are trying to set a dangerous voltage for the chip {:0.3f}. Are you sure about?'.format(value))
			return
		self.__write(':SOUR:VOLT:LEV {:0.3E}'.format(value))

	def get_current(self):
		if(not self.__check_vsource_mode()): return
		return self.__read()


	############## VOLTAGE MEASURE ######################################

	def config__voltage_measure(self, range=1):
		self.__write('*RST')
		self.__write(':SOUR:FUNC CURR')
		self.__write(':SOUR:CURR:MODE FIXED')
		self.__write(':SENS:FUNC "VOLT"')
		self.__write(':SOUR:CURR:RANG MIN')
		self.__write(':SOUR:CURR:LEV 0')
		self.__write(':SENS:VOLT:PROT 1.5')
		self.__write(':SENS:VOLT:RANG {:0d}'.format(range))
		self.__write(':FORM:ELEM VOLT')
		self.__write(':OUTP ON')
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
		time.sleep(0.001); self.inst.write("READ?")
		time.sleep(0.001); str_value = self.inst.read()
		value = float(str_value)
		return value

	def __write(self, command):
		time.sleep(0.001);
		self.inst.write(command)





# multimeter = keithley_multimeter()
