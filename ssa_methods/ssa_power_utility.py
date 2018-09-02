from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import time
import sys
import inspect


class ssa_power_utility:

	def __init__(self, I2C, FC7):
		self.I2C = I2C;
		self.fc7 = FC7;
		self.__initialise_constants()
		self.state = curstate(main = 0, dvdd = 0, avdd = 0, pvdd = 0)


	def set_clock_source(self, value = 'internal'):
		if(value == 'internal' or value == 0):
			self.fc7.write("cnfg_clock_ext_clk_en", 0)
		elif (value == 'external' or value == 1):
			self.fc7.write("cnfg_clock_ext_clk_en", 1)

	def on(self):
		self.set_supply('on')

	def off(self):
		self.set_supply('off')

	def set_supply(self, mode = 'on', d = 1.00, a = 1.25, p = 1.25, bg = 0.270, display = True):
		if(mode == 'on' or mode == 1):
			sleep(0.00); self.mainpoweron()
			sleep(0.01); self.set_pvdd(p);
			sleep(0.20); self.set_dvdd(d);
			sleep(0.00); self.set_avdd(a);
			sleep(0.10); self.set_vbf(bg)
			sleep(0.10); self.reset()
		elif(mode == 'off' or mode == 0):
			sleep(0.00); self.set_vbf(0)
			sleep(0.10); self.set_avdd(0);
			sleep(0.00); self.set_dvdd(0);
			sleep(0.10); self.set_pvdd(0)
			sleep(0.10); self.mainpoweroff()
		sleep(0.1); self.get_power(display = display)


	def get_power(self, display = True, return_all = False):
		Pd, Vd, Id = self.get_power_digital(display, False, True)
		Pa, Va, Ia = self.get_power_analog(display, False, True)
		Pp, Vp, Ip = self.get_power_pads(display, False, True)
		print '->  \tTotal: %7.3fmW  [I=%7.3fmA]' % (Pd+Pa+Pp, Id+Ia+Ip )
		utils.activate_I2C_chip()
		if not return_all:
			return [Pd,Pa,Pp]
		else:
			return [Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip]


	def get_power_digital(self, display = True, i2cact = True, rtv1 = False):
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08)  # to SC3 on PCA9646
		ret  = Send_MPA_SSA_I2C_Command(self.ina226_6, 0, self.pcbread, 0x02, 0)  # read V on shunt
		vret = 0.00125 * ret
		pret = float(round(vret, 3))
		ret  = Send_MPA_SSA_I2C_Command(self.ina226_6, 0, self.pcbread, 0x01, 0)  # read V on shunt
		iret = (self.Vcshunt * ret)/self.Rshunt
		iret = float(round(iret, 3))
		pret = iret * vret
		pret = float(round(pret, 3))
		if i2cact: utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			print '->  \tP_dig: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (pret, vret, iret)
		self.state.dvdd = pret
		if rtv1:
			return pret, vret, iret
		else:
			return pret


	def get_power_analog(self, display = True, i2cact = True, rtv1 = False):
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08)  # to SC3 on PCA9646
		ret  = Send_MPA_SSA_I2C_Command(self.ina226_5, 0, self.pcbread, 0x02, 0)  # read V on shunt
		vret = 0.00125 * ret
		vret = float(round(vret, 3))
		ret  = Send_MPA_SSA_I2C_Command(self.ina226_5, 0, self.pcbread, 0x01, 0)  # read V on shunt
		iret = (self.Vcshunt * ret)/self.Rshunt
		iret = float(round(iret, 3))
		pret = iret * vret
		pret = float(round(pret, 3))
		if i2cact: utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			print '->  \tP_ana: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (pret, vret, iret)
		self.state.avdd = pret
		if rtv1:
			return pret, vret, iret
		else:
			return pret


	def get_power_pads(self, display = True, i2cact = True, rtv1 = False):
		utils.print_enable(False)
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08)  # to SC3 on PCA9646
		ret  = Send_MPA_SSA_I2C_Command(self.ina226_7, 0, self.pcbread, 0x02, 0)  # read V on shunt
		vret = 0.00125 * ret
		vret = float(round(vret, 3))
		ret  = Send_MPA_SSA_I2C_Command(self.ina226_7, 0, self.pcbread, 0x01, 0)  # read V on shunt
		iret = (self.Vcshunt * ret)/self.Rshunt
		iret = float(round(iret, 3))
		pret = iret * vret
		pret = float(round(pret, 3))
		if i2cact: utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			print '->  \tP_pad: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (pret, vret, iret)
		self.state.pvdd = pret
		if rtv1:
			return pret, vret, iret
		else:
			return pret


	def set_dvdd(self, targetvoltage):
		utils.print_enable(False)
		if (targetvoltage > 1.25): targetvoltage = 1.25
		diffvoltage = 1.5 - targetvoltage
		setvoltage = int(round(diffvoltage / self.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, 0x31, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.dvdd = targetvoltage


	def set_avdd(self, targetvoltage):
		utils.print_enable(False)
		if (targetvoltage > 1.25): targetvoltage = 1.25
		diffvoltage = 1.5 - targetvoltage
		setvoltage = int(round(diffvoltage / self.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, 0x35, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.avdd = targetvoltage


	def set_pvdd(self, targetvoltage):
		utils.print_enable(False)
		if (targetvoltage > 1.25): targetvoltage = 1.25
		diffvoltage = 1.5 - targetvoltage
		setvoltage = int(round(diffvoltage / self.Vc))
		if (setvoltage > 4095): setvoltage = 4095
		setvoltage = setvoltage << 4
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SCO on PCA9646
		Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, 0x33, setvoltage)  # tx to DAC C
		utils.activate_I2C_chip()
		utils.print_enable(True)
		self.state.pvdd = targetvoltage


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

	def mainpoweron(self):
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x02)  # route to 2nd PCF8574
		Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b010)  # send on bit
		self.state.main = 1


	def mainpoweroff(self):
		Configure_MPA_SSA_I2C_Master(1, 2)
		Send_MPA_SSA_I2C_Command(self.i2cmux,0, self.pcbwrite, 0, 0x02)  # route to 2nd PCF8574
		Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b111)  # send off bit
		self.state.main = 0



	def resync(self):
		SendCommand_CTRL("fast_fast_reset");
		print '->  \tSent Re-Sync command'
		sleep(0.001)


	def reset(self, display=True):
		utils.print_enable(False)
		sleep(0.01); Configure_MPA_SSA_I2C_Master(1, 2);
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02); # route to 2nd PCF8574
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b0);  # drop reset bit
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b1);  # set reset bit
		sleep(0.01);
		utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display): print '->  \tSent Hard-Reset pulse '

	def _disable_ssa(self, display=True):
		utils.print_enable(False)
		sleep(0.01); Configure_MPA_SSA_I2C_Master(1, 2);
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02); # route to 2nd PCF8574
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b0);  # drop reset bit
		sleep(0.01);
		utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display): print '->  \tSSA disabled '

	def _enable_ssa(self, display=True):
		utils.print_enable(False)
		sleep(0.01); Configure_MPA_SSA_I2C_Master(1, 2);
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02); # route to 2nd PCF8574
		sleep(0.01); Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b1);  # set reset bit
		sleep(0.01);
		utils.activate_I2C_chip()
		utils.print_enable(True)
		if(display): print '->  \tSSA enabled '

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
