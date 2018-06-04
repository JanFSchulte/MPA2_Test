from myScripts.BasicD19c import *
from ssa_reg_map import *
from myScripts.Utilities import *


class ssa_i2c_conf:

	def __init__(self):
		self.ssa_peri_reg_map = ssa_peri_reg_map
		self.ssa_strip_reg_map = ssa_strip_reg_map
		self.freq = 0
		self.debug = False
		self.readback = False

	def set_debug_mode(self, value = True):
		self.debug = value
		if(value): print "->  \tSSA Configuration debug mode Enabled"
		else: print "->  \tSSA Configuration debug mode Disabled"

	def set_readback_mode(self, value = True):
		self.readback = value
		if(value): print "->  \tSSA Configuration Write-Read-Back mode Enabled"
		else: print "->  \tSSA Configuration Write-Read-Back mode Disabled"

	def set_freq(self, value):
		self.freq = value
		return True

	def enable(self):
		activate_I2C_chip()

	def get_freq(self, value):
		return self.freq


	def peri_write(self, register, data):
		cnt = 0; st = True;
		while cnt < 4:
			try:
				data = data & 0xff
				if register not in self.ssa_peri_reg_map.keys():
					print "->  \tRegister name not found"
					rep = False
				else:
					base = ssa_peri_reg_map[register]
					adr  = (base & 0x0fff) | 0b0001000000000000
					rep  = write_I2C('SSA', adr, data, self.freq)
				if(self.readback):
					rep = self.peri_read(register)
					if(rep != data):
						print "->  \tI2C periphery write operation error. [%d][%d]" % (data, rep)
						st = False
				break
			except:
				print '=>  \tTB Communication error - I2C-Peri_write'
				time.sleep(0.1)
				cnt += 1
				st = False
		return st


	def peri_read(self, register, timeout = 0.01):
		cnt = 0; rep = True;
		while cnt < 4:
			try:
				if register not in self.ssa_peri_reg_map.keys():
					print "Register name not found"
					rep = False
				else:
					base = ssa_peri_reg_map[register]
					adr  = (base & 0xfff) | 0b0001000000000000
					rep  = read_I2C('SSA', adr, timeout)
					if rep is None:
						utils.activate_I2C_chip('print')
						rep  = read_I2C('SSA', adr, timeout)
					if rep is None:
						rep = False
				break
			except:
				print '=>  \tTB Communication error - I2C-Peri_read'
				time.sleep(0.1)
				cnt += 1
				rep = False
		return rep


	def strip_write(self, register, strip, data):
		cnt = 0; st = True;
		while cnt < 4:
			try:
				if register not in self.ssa_strip_reg_map.keys():
					print "Register name not found"
					rep = False
				else:
					strip_id = strip if (strip is not 'all') else 0b00000000
					base = ssa_strip_reg_map[register]
					adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111)
					rep  = write_I2C('SSA', adr, data, self.freq)
				if(self.readback):
					tmp = strip_id if (strip_id != 0) else 50
					rep = self.strip_read(register, tmp)
					if(rep != data):
						print "->  \tI2C Strip %d write operation error. [%d][%d]" % (strip_id, data, rep)
						st = False
				break
			except:
				print '=>  \tTB Communication error - I2C-Strip_write' + str(cnt)
				time.sleep(0.1)
				cnt += 1
				st = False
		return st


	def strip_read(self, register, strip, timeout = 0.01):
		cnt = 0; rep = True;
		while cnt < 4:
			try:
				if register not in self.ssa_strip_reg_map.keys():
					print "Register name not found"
					rep = False
				else:
					strip_id = strip if (strip is not 'all') else 0b00000000
					base = ssa_strip_reg_map[register]
					adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111)
					rep  = read_I2C('SSA', adr, timeout)
				break
			except:
				print '=>  \tTB Communication error - I2C-Strip-read'
				time.sleep(0.1)
				cnt += 1
				rep = False
		return rep
