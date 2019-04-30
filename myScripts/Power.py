import time
import sys
import os
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from datetime import datetime



class pwrcst():
	def __init__(self, **kwds):
		self.__dict__.update(kwds)

class power_utilities:

	def  __init__(self, chip = 'SSA'):
		if(not isinstance(chip, str)):
			exit()
		self.chip = chip.upper()
		if(self.chip not in ['MPA', 'SSA']):
			exit()
		self.state = self.__initialise_state()
		self.const = self.__initialise_constants()
		SetSlaveMap(1)

	def main(self, state = 'off'):
		self.board(state)
		self.buffers(state)
		self.fuse(state)

	def board(self, state = 'off'):
		SetSlaveMap(1)
		utils.print_enable(False)
		if(state.upper() == 'ON' or state == 1): v = 0b0
		else: v = 0b1
		Configure_MPA_SSA_I2C_Master(1, 2)
		self.state.main = v
		val = self._assamlemain()
		Send_MPA_SSA_I2C_Command(self.const.i2cmux, 0, self.const.pcbwrite, 0, 0x02, False)
		time.sleep(0.1)
		Send_MPA_SSA_I2C_Command(self.const.powerenable, 0, self.const.pcbwrite, 0, val, False)
		time.sleep(0.001)
		utils.print_enable(True)


	def buffers(self, state = 'off'):
		SetSlaveMap(1)
		utils.print_enable(False)
		if(state.upper() == 'ON' or state == 1): v = 0b0
		else: v = 0b1
		Configure_MPA_SSA_I2C_Master(1, 2)
		self.state.buff = v
		val = self._assamlemain()
		Send_MPA_SSA_I2C_Command(self.const.i2cmux, 0, self.const.pcbwrite, 0, 0x02, False)
		Send_MPA_SSA_I2C_Command(self.const.powerenable, 0, self.const.pcbwrite, 0, val, False)
		time.sleep(0.001)
		utils.print_enable(True)


	def fuse(self, state = 'off'):
		SetSlaveMap(1)
		utils.print_enable(False)
		if(state.upper() == 'ON' or state == 1): v = 0b0
		else: v = 0b1
		Configure_MPA_SSA_I2C_Master(1, 2)
		self.state.fuse = v
		val = self._assamlemain()
		Send_MPA_SSA_I2C_Command(self.const.i2cmux, 0, self.const.pcbwrite, 0, 0x02, False)
		Send_MPA_SSA_I2C_Command(self.const.powerenable, 0, self.const.pcbwrite, 0, val, False)
		time.sleep(0.001)
		utils.print_enable(True)


	def write_mux(self, val):
		r = 'null'
		utils.print_enable(False)
		while r != val:
			Configure_MPA_SSA_I2C_Master(1, 2)
			Send_MPA_SSA_I2C_Command(self.const.i2cmux, 0, self.const.pcbwrite, 0, val, False)
			Configure_MPA_SSA_I2C_Master(1, 2)
			r =  Send_MPA_SSA_I2C_Command(self.const.i2cmux, 0, self.const.pcbread, 0, 0, False)
		utils.print_enable(True)
		return r

	def read_mux(self, val):
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		r =  Send_MPA_SSA_I2C_Command(self.const.i2cmux, 0, self.const.pcbread, 0, 0, False)
		utils.print_enable(True)
		return r

	def write_gpio():
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.const.powerenable, 0, self.const.pcbwrite, 0, val, False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		return Send_MPA_SSA_I2C_Command(self.const.powerenable, 0, self.const.pcbread, 0, 0, False)






	def set_supply(self,  chip, supply, voltage):
		if(chip == 'ssa'):
			if(supply == 'dvdd') : reg = 0x31
			if(supply == 'avdd') : reg = 0x35
			if(supply == 'pvdd') : reg = 0x33
		elif(chip == 'mpa'):
			if(supply == 'dvdd') : reg = 0x31
			if(supply == 'avdd') : reg = 0x35
			if(supply == 'pvdd') : reg = 0x33
		else:
			return False
		utils.print_enable(False)
		if (voltage > 1.25): voltage = 1.25
		diffvoltage = 1.5 - voltage
		setvoltage = int(round(diffvoltage / self.const.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.const.i2cmux,  0, self.const.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.const.dac7678, 0, self.const.pcbwrite, 0x35, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.ssa[supply] = voltage




	def set_vbf(self, targetvoltage = 0.270):
		utils.print_enable(False)
		if (targetvoltage > 0.5):
			targetvoltage = 0.5
		Vc2 = 4095/1.5
		setvoltage = int(round(targetvoltage * Vc2))
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, 0x37, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)









	def _assamlemain(self, ):
		return (
		    0b00000000            |
			self.state.main << 0  |
			self.state.fuse << 1  |
			self.state.buff << 2  |
			self.state.led5 << 4  |
			self.state.led6 << 5  |
			self.state.led7 << 6  |
			self.state.led8 << 7
			)

	def __initialise_state(self):
		const = pwrcst(
			mpa = {'dvdd':0, 'avdd':0, 'pvdd':0, 'vbg':0},
			ssa = {'dvdd':0, 'avdd':0, 'pvdd':0, 'vbg':0},
			main = 1,
			fuse = 1,
			buff = 1,
			led5 = 1,
			led6 = 1,
			led7 = 1,
			led8 = 1
		)
		return const


	def __initialise_constants(self):
		const = pwrcst(
			pcbwrite = 0,
			pcbread = 1,
			pcbi2cmux = 0,
			i2cmux = 0,
			Vc = 0.0003632813,
			dll_chargepump = 0b00,
			bias_dl_enable = False,
			cbc3 = 15,
			FAST = 4,
			SLOW = 2,
			mpaid = 0,
			ssaid = 0,
			pcf8574 = 1,
			powerenable = 2,
			dac7678 = 4,
			ina226_5 = 5,
			ina226_6 = 6,
			ina226_7 = 7,
			ina226_8 = 8,
			ina226_9 = 9,
			ina226_10 = 10,
			ltc2487 = 3,
			Vcshunt = 0.00250,
			Rshunt = 0.1
		)
		return const


	def write_I2C (self, destination, address, data):
		SendCommand_I2C  (0, 0, destination, 0, 0, address, data, 0)

	def read_I2C (self, chip, address, timeout = 0.001):
		SendCommand_I2C(0, 0, destination, 0, 1, address, data, readback)
		sleep(timeout)
		return ReadChipDataNEW()




p = power_utilities('SSA')
