from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import time
import sys
import inspect


class mpassa_power_utility:

	def __init__(self, I2C, FC7, MPA, SSA):
		self.I2C = I2C;	self.fc7 = FC7;
		self.MPA = MPA;	self.SSA = SSA;
		self.__initialise_constants()
		self.state = curstate(main = 0, dvdd = 0, avdd = 0, pvdd = 0)

	def set_clock_source(self, value = 'internal'):
		if(value == 'internal' or value == 0):
			self.fc7.write("cnfg_clock_ext_clk_en", 0)
		elif (value == 'external' or value == 1):
			self.fc7.write("cnfg_clock_ext_clk_en", 1)

	def on(self, slvs = 0b111):
		self.set_supply('on', display = False)
		self.enable_ssa(display = False)
		self.enable_mpa(display = False)
		self.SSA.ctrl.init_slvs(slvs)
		sleep(0.1);
		self.get_power(display = True)

	def off(self):
		self.disable_ssa()
		self.disable_mpa()
		self.set_supply('off')

	def reset(self, display = True):
		self.disable_ssa(display)
		self.disable_mpa(display)
		time.sleep(0.1)
		self.enable_ssa(display)
		self.enable_mpa(display)

	def resync(self):
		SendCommand_CTRL("fast_fast_reset");
		print '->  \tSent Re-Sync command'
		sleep(0.001)

	def set_slvs(self, val=0b110):
		self.SSA.ctrl.init_slvs(val&0b111)

	def set_supply(self, mode = 'on', d = 1.0, a = 1.20, p = 1.20, bg = 0.280, display = True):
		# d = 1.0; a = 1.25; p = 1.25; bg = 0.280; self=pwr;
		if(mode == 'on' or mode == 1):
			sleep(0.00); self.mainpoweron()
			sleep(0.01); self.set_pvdd('SSA', p);  self.set_pvdd('MPA', p);
			sleep(0.20); self.set_dvdd('SSA', d);  self.set_dvdd('MPA', d);
			sleep(0.00); self.set_avdd('SSA', a);  self.set_avdd('MPA', a);
			sleep(0.10); self.set_vbg( 'SSA', bg); self.set_vbg( 'MPA', bg);
			sleep(0.10); self.reset(display = False)
		elif(mode == 'off' or mode == 0):
			sleep(0.00); self.set_vbg( 'SSA',0); self.set_vbg( 'MPA',0);
			sleep(0.00); self.set_dvdd('SSA',0); self.set_dvdd('MPA',0);
			sleep(0.00); self.set_avdd('SSA',0); self.set_avdd('MPA',0);
			sleep(0.10); self.set_pvdd('SSA',0); self.set_pvdd('MPA',0);
			sleep(0.10); self.mainpoweroff()
		if(display):
			sleep(0.1); self.get_power(display = display)

	def get_power(self, display = True):
		sPd, sVd, sId = self.get_pwr_dvdd('SSA', display, False, True)
		sPa, sVa, sIa = self.get_pwr_avdd('SSA', display, False, True)
		sPp, sVp, sIp = self.get_pwr_pvdd('SSA', display, False, True)
		if(display): print("")
		mPd, mVd, mId = self.get_pwr_dvdd('MPA', display, False, True)
		mPa, mVa, mIa = self.get_pwr_avdd('MPA', display, False, True)
		mPp, mVp, mIp = self.get_pwr_pvdd('MPA', display, False, True)
		utils.activate_I2C_chip()
		return [mPd,mPa,mPp,sPd,sPa,sPp]

	def get_power_repeat(self, duration = 5):
		t1 = time.time()
		t0 = t1
		while(t1<(t0+duration)):
			print("____________________________________________________\n")
			self.get_power(display = True)
			t1 = time.time()

	def mainpoweron(self):
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x02)  # route to 2nd PCF8574
		Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b010)  # send on bit
		utils.print_enable(True)
		self.state.main = 1

	def mainpoweroff(self):
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,0, self.pcbwrite, 0, 0x02)  # route to 2nd PCF8574
		Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b111)  # send off bit
		utils.print_enable(True)
		self.state.main = 0

	def disable_ssa(self, display=True):
		self.ssastate = False
		self.__enable_disable_chip()
		if(display):
			print '->  \tSSA disabled '

	def enable_ssa(self, display=True):
		self.ssastate = True
		self.__enable_disable_chip()
		if(display):
			print '->  \tSSA enabled '

	def disable_mpa(self, display=True):
		self.mpastate = False
		self.__enable_disable_chip()
		if(display): print '->  \tMPA disabled '

	def enable_mpa(self, display=True):
		self.mpastate = True
		self.__enable_disable_chip()
		if(display):
			print '->  \tMPA enabled '

	def __enable_disable_chip(self):
		val = (self.mpaid << 5) | (self.ssaid << 1) | (self.ssastate << 0) + (self.mpastate << 4)
		utils.print_enable(False)
		sleep(0.01); Configure_MPA_SSA_I2C_Master(1, 2);
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02); # route to 2nd PCF8574
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, val);  # set reset bit
		sleep(0.01);
		utils.activate_I2C_chip()
		utils.print_enable(True)

	def get_pwr_dvdd(self, chip = 'SSA', display = True, i2cact = True, rtv1 = False):
		device = self.ina226_6 if (chip == 'MPA') else self.ina226_9
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08)  # to SC3 on PCA9646
		ret  = Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x02, 0)  # read V on shunt
		vret = 0.00125 * ret
		pret = float(round(vret, 3))
		ret  = Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x01, 0)  # read V on shunt
		iret = (self.Vcshunt * ret)/self.Rshunt
		iret = float(round(iret, 3))
		pret = iret * vret
		pret = float(round(pret, 3))
		if i2cact: utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			print '->  \t%3s - P_dig: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (chip, pret, vret, iret)
		self.state.dvdd = pret
		if rtv1:
			return pret, vret, iret
		else:
			return pret

	def get_pwr_avdd(self, chip = 'SSA', display = True, i2cact = True, rtv1 = False):
		device = self.ina226_5 if (chip == 'MPA') else self.ina226_8
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08)  # to SC3 on PCA9646
		ret  = Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x02, 0)  # read V on shunt
		vret = 0.00125 * ret
		vret = float(round(vret, 3))
		ret  = Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x01, 0)  # read V on shunt
		iret = (self.Vcshunt * ret)/self.Rshunt
		iret = float(round(iret, 3))
		pret = iret * vret
		pret = float(round(pret, 3))
		if i2cact: utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			print '->  \t%3s - P_ana: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (chip, pret, vret, iret)
		self.state.avdd = pret
		if rtv1:
			return pret, vret, iret
		else:
			return pret

	def get_pwr_pvdd(self, chip = 'SSA', display = True, i2cact = True, rtv1 = False):
		device = self.ina226_7 if (chip == 'MPA') else self.ina226_10
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08)  # to SC3 on PCA9646
		ret  = Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x02, 0)  # read V on shunt
		vret = 0.00125 * ret
		vret = float(round(vret, 3))
		ret  = Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x01, 0)  # read V on shunt
		iret = (self.Vcshunt * ret)/self.Rshunt
		iret = float(round(iret, 3))
		pret = iret * vret
		pret = float(round(pret, 3))
		if i2cact: utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			print '->  \t%3s - P_pad: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (chip, pret, vret, iret)
		self.state.pvdd = pret
		if rtv1:
			return pret, vret, iret
		else:
			return pret


	def set_dvdd(self, chip = 'SSA', targetvoltage = 1.00):
		val = 0x31 if (chip == 'MPA') else 0x30
		utils.print_enable(False)
		if (targetvoltage > 1.25): targetvoltage = 1.25
		diffvoltage = 1.5 - targetvoltage
		setvoltage = int(round(diffvoltage / self.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.dvdd = targetvoltage


	def set_avdd(self, chip = 'SSA', targetvoltage = 1.25):
		val = 0x35 if (chip == 'MPA') else 0x32
		utils.print_enable(False)
		if (targetvoltage > 1.25): targetvoltage = 1.25
		diffvoltage = 1.5 - targetvoltage
		setvoltage = int(round(diffvoltage / self.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.avdd = targetvoltage


	def set_pvdd(self, chip = 'SSA', targetvoltage = 1.25):
		val = 0x33 if (chip == 'MPA') else 0x34
		utils.print_enable(False)
		if (targetvoltage > 1.25): targetvoltage = 1.25
		diffvoltage = 1.5 - targetvoltage
		setvoltage = int(round(diffvoltage / self.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.pvdd = targetvoltage


	def set_vbg(self, chip = 'SSA', targetvoltage = 0.280):
		val = 0x37 if (chip == 'SSA') else 0x36
		utils.print_enable(False)
		if (targetvoltage > 0.5):
			targetvoltage = 0.5
		Vc2 = 4095/1.5
		setvoltage = int(round(targetvoltage * Vc2))
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)

	def __initialise_constants(self):
		self.pcbwrite = 0;
		self.pcbread = 1;
		self.pcbi2cmux = 0;
		self.i2cmux = 0;
		self.Vc = 0.0003632813;
		self.dll_chargepump = 0b00;
		self.bias_dl_enable    = False
		self.cbc3 = 15
		self.FAST = 4
		self.SLOW = 2
		self.mpaid = 0
		self.ssaid = 0
		self.i2cmux = 0
		self.pcf8574 = 1
		self.powerenable = 2
		self.dac7678 = 4
		self.ina226_5 = 5
		self.ina226_6 = 6
		self.ina226_7 = 7
		self.ina226_8 = 8
		self.ina226_9 = 9
		self.ina226_10 = 10
		self.ltc2487 = 3
		self.Vc = 0.0003632813 # V/Dac step
		self.Vcshunt = 0.00250
		self.Rshunt = 0.1
		self.mpaid = 0
		self.ssaid = 0
		self.mpastate = False
		self.ssastate = False
