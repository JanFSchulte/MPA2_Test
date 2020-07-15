import json
import time
from myScripts.BasicD19c import *
#from myScripts.Utilities import *
from utilities.tbsettings import *
from ssa_methods.Configuration.ssa1_reg_map import *

class ssa_i2c_conf:

	def __init__(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			#from ssa_methods.Configuration.ssa2_reg_map import *
			ssa_reg_map = json.load(open('./ssa_methods/Configuration/ssa2_reg_map.json', 'r'))
			ssa_cal_map = json.load(open('./ssa_methods/Configuration/ssa2_cal_map.json', 'r'))
			self.ssa_strip_reg_map = ssa_reg_map['STRIP']
			self.ssa_peri_reg_map  = ssa_reg_map['PERIPHERY']
			self.analog_mux_map    = ssa_cal_map['PAD']
			self.analog_adc_map    = ssa_cal_map['ADC']
			print('->  Loaded configuration for SSA v2')
		else:
			self.ssa_strip_reg_map = ssa_strip_reg_map_v1
			self.ssa_peri_reg_map  = ssa_peri_reg_map_v1
			self.analog_mux_map    = analog_mux_map_v1
			print('->  Loaded configuration for SSA v2')
		self.freq = 0
		self.debug = False
		self.readback = False
		self.delay = 0.001

	def get_strip_reg_map(self):
		return self.ssa_strip_reg_map

	def get_peri_reg_map(self):
		return self.ssa_peri_reg_map

	def get_analog_mux_map(self):
		return self.analog_mux_map

	def set_debug_mode(self, value = True, display = 0):
		self.debug = value
		if(display):
			if(value): print("->  SSA Configuration debug mode Enabled")
			else: print("->  SSA Configuration debug mode Disabled")

	def set_readback_mode(self, value = True, display = 0):
		self.readback = value
		if(display):
			if(value): print("->  SSA Configuration Write-Read-Back mode Enabled")
			else: print("->  SSA Configuration Write-Read-Back mode Disabled")

	def set_freq(self, value):
		self.freq = value
		return True

	def enable(self):
		activate_I2C_chip()

	def get_freq(self, value):
		return self.freq

	def peri_write(self, register, data, field=False, use_onchip_mask = True):
		cnt = 0; st = True;
		#while cnt < 4:
		#	try:
		cnt += 1
		data = data & 0xff
		time.sleep(self.delay)
		if(register not in self.ssa_peri_reg_map.keys()):
			print("'X>  I2C Periphery register name not found")
			rep = 'Null'
		else:
			if(tbconfig.VERSION['SSA'] >= 2):
				reg_adr = self.tonumber(self.ssa_peri_reg_map[register]['adr'],0)
			else:
				base = self.ssa_peri_reg_map[register]
				reg_adr  = (base & 0x0fff) | 0b0001000000000000
			if(field):
				if(tbconfig.VERSION['SSA']<2):
					print('X>  I2C Strip {:3d} error. Field available only for SSA v2'.format(strip_id))
					return 'Null'
				####################################
				mask_val = self.tonumber(self.ssa_peri_reg_map[register]['fields_mask'][field], 0)
				loc = self._get_field_location(mask_val)
				tdata = (data << loc[0]) & 0xff & mask_val

				if(use_onchip_mask): ### this is the procedure to use
					mask_name = self.ssa_peri_reg_map[register]['mask_reg']
					mask_adr  = self.tonumber(self.ssa_peri_reg_map[mask_name]['adr'], 0)
					rep  = write_I2C('SSA', mask_adr, mask_val, self.freq)
					rep  = write_I2C('SSA', reg_adr, tdata, self.freq)
				else:
					readreg  = read_I2C('SSA', reg_adr, timeout)
					if(readreg != None):
						wdata = (readreg & (~int(mask, 2))) | (tdata & int(mask, 2))
						rep  = write_I2C('SSA', reg_adr, wdata, self.freq)
					else:
						print('X>  I2C Periphery read  - Adr=[0x{:4x}], Value=[{:s}] - ERROR'.format(reg_adr, 'NOVALUE'))
						st = 'Null';
				####################################
				if(self.debug):
					print('->  I2C Periphery write - Adr=[0x{:4x}], Value=[{:d}]'.format(reg_adr, tdata))
			else:
				rep  = write_I2C('SSA', reg_adr, data, self.freq)
				if(self.debug):
					print('->  I2C Periphery write - Adr=[0x{:4x}], Value=[{:d}]'.format(reg_adr, data))
		if(self.readback):
			rep = self.peri_read(register)
			if(rep != data):
				print("->  I2C periphery write - [%d][%d] - ERROR" % (data, rep))
				st = 'Null'
			#	if(st):
			#		break
			#except:
			#	print('=>  TB Communication error - I2C-Peri_write')
			#	time.sleep(0.1)
			#	st = 'Null'
		return st

	def peri_read(self, register, field=False, timeout = 0.01):
		cnt = 0; rep = True;
		time.sleep(self.delay)
		#while cnt < 4:
		#	try:
		cnt += 1
		if(register not in self.ssa_peri_reg_map.keys()):
			print("'X>  I2C Periphery register name not found")
			rep = 'Null'
		else:
			if(tbconfig.VERSION['SSA'] == 2):
				adr = self.tonumber(self.ssa_peri_reg_map[register]['adr'], 0)
			else:
				base = self.ssa_peri_reg_map[register]
				adr  = (base & 0xfff) | 0b0001000000000000
			repd = read_I2C('SSA', adr, timeout)
			if(repd == None):
				#utils.activate_I2C_chip()
				#rep  = read_I2C('SSA', adr, timeout)
				rep  = 'Null'
				print('X>  I2C Periphery read  - Adr=[0x{:4x}], Value=[{:s}] - ERROR'.format(adr, 'NOVALUE'))
				#self.utils.activate_I2C_chip()
			else:
				if(field):
					mask = self.ssa_peri_reg_map[register]['fields_mask'][field]
					loc  = self._get_field_location(mask)
					rep  = ((repd & mask) >> loc[0])
				else:
					rep  = repd
				if(self.debug):
					print('->  I2C Periphery read  - Adr=[0x{:4x}], Value=[{:b}] - GOOD'.format(adr, repd))
			#			break
			#except:
			#	print('=>  TB Communication error - I2C-Peri_read')
			#	time.sleep(0.1)
			#	rep = 'Null'
		return rep


	def strip_write(self, register, strip, data, field=False, timeout = 0.01, use_onchip_mask = True):
		#example: ssa.i2c.strip_write('StripControl2',0, 0xff, 'HipCut')
		cnt = 0; st = True;
		V = tbconfig.VERSION['SSA']
		#while cnt < 4:
		#	try:
		cnt += 1
		if register not in self.ssa_strip_reg_map.keys():
			print("'X>  I2C Strip register name not found")
			rep = 'Null'
		else:
			if(V>=2): strip_id = strip if (strip is not 'all') else 0x7f
			else:     strip_id = strip if (strip is not 'all') else 0x00
			if(V>=2): base = self.tonumber(self.ssa_strip_reg_map[register]['adr'],0)
			else:     base = self.tonumber(self.ssa_strip_reg_map[register],0)
			reg_adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111)

			if(field):
				if(V<2):
					print('X>  I2C Strip {:3d} error. Field available only for SSA v2'.format(strip_id))
					return 'Null'
				####################################
				mask_val = self.tonumber(self.ssa_strip_reg_map[register]['fields_mask'][field],0)
				loc  = self._get_field_location(mask_val)
				tdata = (data << loc[0]) & 0xff & mask_val

				if(use_onchip_mask):  ### this is the procedure to use
					mask_adr = self.tonumber(self.ssa_peri_reg_map['mask_strip']['adr'],0)
					rep  = write_I2C('SSA', mask_adr, mask_val, self.freq)
					rep  = write_I2C('SSA', reg_adr, tdata, self.freq)
				else:
					if(strip=='all'): readreg  = read_I2C('SSA', 1, timeout)
					else: readreg  = read_I2C('SSA', reg_adr, timeout)
					if(readreg != None):
						wdata = (readreg & (~int(mask, 2))) | (tdata & int(mask, 2))
						rep  = write_I2C('SSA', reg_adr, wdata, self.freq)
					else:
						print('X>  I2C Strip {:3d} read  -  Adr=[0x{:4x}], Value=[{:s}] - ERROR'.format(strip_id, reg_adr, 'NOVALUE'))
						st = 'Null';

				if(self.debug):
					print('->  I2C Strip {:3d} write - Adr=[0x{:4x}], Value=[{:d}]'.format(strip_id, reg_adr, tdata))
			else:
				wdata = data
				rep  = write_I2C('SSA', reg_adr, wdata, self.freq)
				if(self.debug):
					print('->  I2C Strip {:3d} write - Adr=[0x{:4x}], Value=[{:d}]'.format(strip_id, reg_adr, wdata))
		if(self.readback):
			tmp = strip_id if (strip_id != 0) else 50
			rep = self.strip_read(register, tmp)
			if(rep != data):
				print("->  I2C Strip {:3d} write - [{:d}][{:d}] - ERROR".format(strip_id, data, rep))
				st = 'Null'
		#		if(st):
		#			break
		#	except:
		#		print('=>  TB Communication error - I2C-Strip_write' + str(cnt))
		#		time.sleep(0.1)
		#		st = 'Null'
		return st

	def strip_read(self, register, strip, field=False, timeout = 0.01):
		cnt = 0; rep = True;
		#while cnt < 4:
		#	try:
		cnt += 1
		if register not in self.ssa_strip_reg_map.keys():
			print("'X>  I2C Strip register name not found")
			rep = 'Null'
		else:
			if(tbconfig.VERSION['SSA'] >= 2):
				strip_id = strip if (strip is not 'all') else 0x7f
				base = self.tonumber(self.ssa_strip_reg_map[register]['adr'],0)
			else:
				strip_id = strip if (strip is not 'all') else 0x00
				base = self.tonumber(self.ssa_strip_reg_map[register],0)
			adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111)
			repd = read_I2C('SSA', adr, timeout)
			if(repd == None):
				rep  = 'Null'
				print('X>  I2C Strip {:3d} read  -  Adr=[{:h}], Value=[{:s}] - ERROR'.format(strip_id, adr, 'NOVALUE'))
			else:
				if(field):
					mask = self.ssa_strip_reg_map[register]['fields_mask'][field]
					loc  = self._get_field_location(mask)
					rep  = ((repd & mask) >> loc[0])
				else:
					rep  = repd
				if(self.debug):
					print("->  I2C Strip {:3d} read  - [{:x}] - GOOD".format(strip_id, rep))
			#			break
			#except:
			#	print('=>  TB Communication error - I2C-Strip-read')
			#	time.sleep(0.1)
			#	rep = 'Null'
		return rep

	def _get_field_location(self, mask):
		if(isinstance(mask, int)):   maskd = bin(mask)
		elif(isinstance(mask, str)): maskd = mask
		else: return [-1, -1]
		bitarray = [int(i) for i in np.binary_repr(int(maskd, 2), 8)]
		bitarray.reverse()
		oneloc = np.nonzero(np.array(bitarray) == 1)[0]
		if(len(oneloc)>0): rval = [oneloc[0], oneloc[-1]]
		else: rval = [-1, -1]
		return rval

	def tonumber(self, value, base):
		if(isinstance(value, str)):
			return int(value, base)
		else:
			return value
