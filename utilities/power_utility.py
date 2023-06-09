from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import time
import sys
import inspect


class PowerUtility:

    def __init__(self, I2C, FC7, chip_name):
        self.I2C = I2C;
        self.fc7 = FC7;
        self.chip = chip_name
        self.__initialise_constants()
        self.state = curstate(main = 0, dvdd = 0, avdd = 0, pvdd = 0)


    def set_clock_source(self, value = 'internal'):
        if(value == 'internal' or value == 0):
            self.fc7.write("fc7_daq_cnfg.clock.ext_clk_en", 0)
            rp = self.fc7.read("fc7_daq_cnfg.clock.ext_clk_en")
        elif (value == 'external' or value == 1):
            self.fc7.write("fc7_daq_cnfg.clock.ext_clk_en", 1)
            rp = self.fc7.read("fc7_daq_cnfg.clock.ext_clk_en")
        else:
            rp = -1
        return rp

    def on(self, display=True):
        self.set_supply(mode='on',  display=display)

    def off(self, display=True):
        self.set_supply(mode='off', display=display)

    def set_supply(self, mode = 'on', d = 1.0, a = 1.2, p = 1.2, bg = 0.270, display = True):
        utils.activate_I2C_chip(self.fc7)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        if(mode == 'on' or mode == 1):
            time.sleep(0.00); self.mainpoweron(fast=True)
            time.sleep(0.01); self.set_pvdd(p, chip='SSA', fast=True); self.set_pvdd(p, chip='MPA', fast=True)
            time.sleep(0.20); self.set_dvdd(d, chip='SSA', fast=True); self.set_dvdd(d, chip='MPA', fast=True)
            time.sleep(0.00); self.set_avdd(a, chip='SSA', fast=True); self.set_avdd(a, chip='MPA', fast=True)
            time.sleep(0.10); self.set_vbf(bg); self.set_vbf(bg, chip='MPA')
            time.sleep(0.50); self.reset_m(display=display)
            time.sleep(0.10)
            if(display):
                #time.sleep(0.4); self.get_power(display = True, chip='SSA')
                time.sleep(0.1); self.get_power(display = True, chip='MPA')
        elif(mode == 'off' or mode == 0):
            time.sleep(0.00); self.set_vbf(0,  chip='MPA', fast=True); self.set_vbf(0,  chip='SSA', fast=True);
            time.sleep(0.10); self.set_avdd(0, chip='MPA', fast=True); self.set_avdd(0, chip='SSA', fast=True)
            time.sleep(0.00); self.set_dvdd(0, chip='MPA', fast=True); self.set_dvdd(0, chip='SSA', fast=True)
            time.sleep(0.10); self.set_pvdd(0, chip='MPA', fast=True); self.set_pvdd(0, chip='SSA', fast=True)
            time.sleep(0.10); self.mainpoweroff(fast=True)
            if(display):
                #time.sleep(0.10); self.get_power(display = True, chip='SSA')
                time.sleep(0.1); self.get_power(display = True, chip='MPA')
        utils.activate_I2C_chip(self.fc7)

    # pwr reset function from mpa_methods, for comparison purposes
    def reset_m(self, display=True):
        utils.print_enable(False)
        time.sleep(0.01); self.fc7.Configure_MPA_SSA_I2C_Master(1, 2, verbose = 0);
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02, verbose = 0); # route to 2nd PCF8574
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0, verbose = 0);  # drop reset bit
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 16, verbose = 0);  # set reset bit
        time.sleep(0.01);
        utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        if(display): print('->  \tSent Hard-Reset pulse ')

    def test_power(self, state = 'operation', display=True):
        good = True
        if(state=='off'):      #power off
            d_limit = [ 0.0, 1.0]
            a_limit = [ 0.0, 1.0]
            p_limit = [ 0.0, 1.0]
        elif(state=='reset'):  #with reset_b = 0
            d_limit = [ 5.0, 15.0]
            a_limit = [18.0, 28.0]
            p_limit = [ 0.0,  8.0]
        elif(state=='reset_mpa'):
            d_limit = [ 5.0,  20.0]
            a_limit = [50.0, 100.0]
            p_limit = [ 5.0,  25.0]
        elif(state=='startup'):   #enable after reset
            d_limit = [18.0, 35.0]
            a_limit = [18.0, 28.0]
            p_limit = [ 0.0,  8.0]
        elif(state=='startup_mpa'):   #enable after reset
            d_limit = [50.0, 100.0]
            a_limit = [50.0, 100.0]
            p_limit = [ 5.0,  25.0]
        elif(state=='uncalibrated'): #configured
            d_limit = [18.0, 35.0]
            a_limit = [18.0, 28.0]
            p_limit = [10.0, 40.0]
        elif(state=='calibrated'):  #configured and calibrated
            d_limit = [18.0, 35.0]
            a_limit = [18.0, 28.0]
            p_limit = [10.0, 40.0]
        else:
            d_limit = [ 5.0, 35.0]
            a_limit = [18.0, 28.0]
            p_limit = [ 1.0, 40.0]
        [Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.get_power(display=False, return_all=True)
        if(display):
            dstr = "  \tP_dig:{:7.3f}mW [V={:5.3f}V - I={:5.3f}mA]".format(Pd, Vd, Id)
            astr = "  \tP_ana:{:7.3f}mW [V={:5.3f}V - I={:5.3f}mA]".format(Pa, Va, Ia)
            pstr = "  \tP_pad:{:7.3f}mW [V={:5.3f}V - I={:5.3f}mA]".format(Pp, Vp, Ip)
            utils.print_info("->  Power measurement (chip in '{:s}' mode)".format(state))
            if(Id>d_limit[0] and Id<d_limit[1]):
                utils.print_good(dstr)
            else:
                utils.print_error(dstr)
                good = False
            if(Ia>a_limit[0] and Ia<a_limit[1]):
                utils.print_good(astr)
            else:
                utils.print_error(astr)
                good = False
            if(Ip>p_limit[0] and Ip<p_limit[1]):
                utils.print_good(pstr)
            else:
                utils.print_error(pstr)
                good = False
        return [good, Id, Ia, Ip]


    def get_power(self, display = True, return_all = False, chip = False, fast=False):
        chip = self.chip if not chip else chip
        Pd, Vd, Id = self.get_power_digital(display, False, True, chip = chip) #, fast=fast)
        Pa, Va, Ia = self.get_power_analog(display, False, True, chip = chip) #, fast=fast)
        Pp, Vp, Ip = self.get_power_pads(display, False, True, chip = chip) #, fast=fast)
        if(display):
            utils.print_log('->  Total: %7.3fmW  [             I=%7.3fmA]' % (Pd+Pa+Pp, Id+Ia+Ip ))
        utils.activate_I2C_chip(self.fc7)
        if not return_all:
            return [Pd,Pa,Pp]
        else:
            return [Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip]

    def get_power_repeat(self, duration = 5):
        t1 = time.time()
        t0 = t1
        while(t1<(t0+duration)):
            utils.print_log("____________________________________________________\n")
            self.get_power(display = True)
            t1 = time.time()

    def get_power_digital(self, display = True, i2cact = True, rtv1 = False, chip = False):
        chip = self.chip if not chip else chip
        device = self.ina226_6 if (chip == 'SSA') else self.ina226_9
        utils.print_enable(False)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        time.sleep(0.001)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08, note='i2cmux')  # to SC3 on PCA9646
        time.sleep(0.001)
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x02, 0, note='ina226_6')  # read V on shunt
        vret = 0.00125 * ret
        pret = float(round(vret, 3))
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x01, 0, note='ina226_6')  # read V on shunt
        time.sleep(0.001)
        iret = (self.Vcshunt * ret)/self.Rshunt
        iret = float(round(iret, 3))
        pret = iret * vret
        pret = float(round(pret, 3))
        if i2cact: utils.activate_I2C_chip(self.fc7)
        time.sleep(0.001)
        utils.print_enable(True)
        if(display):
            utils.print_log( '->  P_dig: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (pret, vret, iret))
        self.state.dvdd = pret
        if rtv1:
            return pret, vret, iret
        else:
            return pret

    def get_power_digital_average(self, nsamples=10):
        isample = []
        vsample = []
        psample = []
        utils.activate_I2C_chip(self.fc7)
        for i in range(nsamples):
            pret, vret, iret = self.get_power_digital(display=0, i2cact=0, rtv1=1)
            isample.append(iret)
            vsample.append(vret)
            psample.append(pret)
        vmean = np.mean(vsample)
        imean = np.mean(isample)
        pmean = np.mean(psample)
        return pmean, vmean, imean

    def get_dvdd(self):
        utils.print_enable(False)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        time.sleep(0.001)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08, note='i2cmux')  # to SC3 on PCA9646
        time.sleep(0.001)
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(self.ina226_6, 0, self.pcbread, 0x02, 0, note='ina226_6')  # read V on shunt
        time.sleep(0.001)
        vret = 0.00125 * ret
        pret = float(round(vret, 3))
        utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        return pret


    def get_power_analog(self, display = True, i2cact = True, rtv1 = False, chip = False):
        chip = self.chip if not chip else chip
        device = self.ina226_5 if (chip == 'SSA') else self.ina226_8
        utils.print_enable(False)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        time.sleep(0.001)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08, note='i2cmux')  # to SC3 on PCA9646
        time.sleep(0.001)
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x02, 0, note='ina226_5')  # read V on shunt
        time.sleep(0.001)
        vret = 0.00125 * ret
        vret = float(round(vret, 3))
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x01, 0, note='ina226_5')  # read V on shunt
        time.sleep(0.001)
        iret = (self.Vcshunt * ret)/self.Rshunt
        iret = float(round(iret, 3))
        pret = iret * vret
        pret = float(round(pret, 3))
        if i2cact: utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        if(display):
            utils.print_log( '->  P_ana: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (pret, vret, iret))
        self.state.avdd = pret
        if rtv1:
            return pret, vret, iret
        else:
            return pret


    def get_power_pads(self, display = True, i2cact = True, rtv1 = False, chip = False):
        chip = self.chip if not chip else chip
        device = self.ina226_7 if (chip == 'SSA') else self.ina226_10
        utils.print_enable(False)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        time.sleep(0.001)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x08, note='i2cmux')  # to SC3 on PCA9646
        time.sleep(0.001)
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x02, 0, note='ina226_7')  # read V on shunt
        time.sleep(0.001)
        vret = 0.00125 * ret
        vret = float(round(vret, 3))
        ret  = self.fc7.Send_MPA_SSA_I2C_Command(device, 0, self.pcbread, 0x01, 0, note='ina226_7')  # read V on shunt
        time.sleep(0.001)
        iret = (self.Vcshunt * ret)/self.Rshunt
        iret = float(round(iret, 3))
        pret = iret * vret
        pret = float(round(pret, 3))
        if i2cact: utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        if(display):
            utils.print_log( '->  P_pad: %7.3fmW  [V=%7.3fV - I=%7.3fmA]' % (pret, vret, iret))
        self.state.pvdd = pret
        if rtv1:
            return pret, vret, iret
        else:
            return pret


    def set_dvdd(self, targetvoltage, chip = False, fast=False):
        chip = self.chip if not chip else chip
        val = 0x31 if (chip == 'SSA') else 0x30
        utils.print_enable(False)
        if (targetvoltage > 1.3): targetvoltage = 1.3
        if (targetvoltage < 0):   targetvoltage = 0
        diffvoltage = 1.500 - targetvoltage
        setvoltage = int(round(diffvoltage / self.Vc))
        if (setvoltage > 4095): setvoltage = 4095
        setvoltage = setvoltage << 4
        time.sleep(0.001)
        if(not fast): self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        time.sleep(0.001)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01, note='i2cmux')  # to SCO on PCA9646
        time.sleep(0.001)
        self.fc7.Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage, note='dac7678')  # tx to DAC C
        time.sleep(0.001)
        if(not fast): utils.activate_I2C_chip(self.fc7)
        time.sleep(0.001)
        utils.print_enable(True)
        self.state.dvdd = targetvoltage


    def set_avdd(self, targetvoltage, chip = False, fast=False):
        chip = self.chip if not chip else chip
        val = 0x35 if (chip == 'SSA') else 0x32
        utils.print_enable(False)
        if (targetvoltage > 1.3): targetvoltage = 1.3
        if (targetvoltage < 0):   targetvoltage = 0
        diffvoltage = 1.470 - targetvoltage
        setvoltage = int(round(diffvoltage / self.Vc))
        if (setvoltage > 4095): setvoltage = 4095
        setvoltage = setvoltage << 4
        if(not fast): self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01, note='i2cmux')  # to SCO on PCA9646
        self.fc7.Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage, note='dac7678')  # tx to DAC C
        if(not fast): utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        self.state.avdd = targetvoltage


    def set_pvdd(self, targetvoltage, chip = False, fast=False):
        chip = self.chip if not chip else chip
        val = 0x33 if (chip == 'SSA') else 0x34
        utils.print_enable(False)
        if (targetvoltage > 1.3): targetvoltage = 1.3
        if (targetvoltage < 0):   targetvoltage = 0
        diffvoltage = 1.470 - targetvoltage
        setvoltage = int(round(diffvoltage / self.Vc))
        if (setvoltage > 4095): setvoltage = 4095
        setvoltage = setvoltage << 4
        if(not fast): self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01, note='i2cmux')  # to SCO on PCA9646
        self.fc7.Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage, note='dac7678')  # tx to DAC C
        if(not fast): utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        self.state.pvdd = targetvoltage


    def set_vbf(self, targetvoltage = 0.270, chip = False, fast=False):
        chip = self.chip if not chip else chip
        val = 0x37 if (self.chip== 'SSA') else 0x36
        utils.print_enable(False)
        if (targetvoltage > 0.5):
            targetvoltage = 0.5
        Vc2 = 4095/1.5
        setvoltage = int(round(targetvoltage * Vc2))
        setvoltage = setvoltage << 4
        if(not fast): self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01, note='i2cmux')  # to SCO on PCA9646
        self.fc7.Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage, note='dac7678')  # tx to DAC C
        if(not fast): utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)

    def mainpoweron(self, fast=False):
        #utils.print_enable(False)
        if(not fast): self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x02, note='i2cmux', verbose = 0)  # route to 2nd PCF8574
        self.fc7.Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b010, note='powerenable', verbose = 0)  # send on bit
        #utils.print_enable(True)
        self.state.main = 1


    def mainpoweroff(self, fast=False):
        utils.print_enable(False)
        if(not fast): self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,0, self.pcbwrite, 0, 0x02, note='i2cmux', verbose = 0)  # route to 2nd PCF8574
        self.fc7.Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b111, note='powerenable', verbose = 0)  # send off bit
        utils.print_enable(True)
        self.state.main = 0

    def efusepoweron(self):
        "Sets enable for 2.5V_En signal in Interface Board v3. Required for efuse writing."
        utils.print_enable(False)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux, 0, self.pcbwrite, 0, 0x02, note='i2cmux', verbose = 0)  # route to 2nd PCF8574
        self.fc7.Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b000, note='powerenable', verbose = 0)  # send on bit
        utils.print_enable(True)
        self.state.main = 1

    def efusepoweroff(self):
        utils.print_enable(False)
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,0, self.pcbwrite, 0, 0x02, note='i2cmux', verbose = 0)  # route to 2nd PCF8574
        self.fc7.Send_MPA_SSA_I2C_Command(self.powerenable, 0, self.pcbwrite, 0, 0b010, note='powerenable', verbose = 0)  # send off bit
        utils.print_enable(True)
        self.state.main = 0

    def resync(self):
        SendCommand_CTRL("fast_fast_reset");
        utils.print_log( '->  Sent Re-Sync command')
        time.sleep(0.001)

    def reset(self, display = True, mode = 'auto'):
        self.disable_ssa(display)
        self.disable_mpa(display)
        time.sleep(0.1)
        self.enable_ssa(display)
        self.enable_mpa(display)

    def reset_mpa(self, display = True):
        self.disable_mpa(display)
        time.sleep(0.001)
        self.enable_mpa(display)

    def disable_ssa(self, display=True):
        self.ssastate = False
        self.__enable_disable_chip()
        if(display):
            utils.print_log('->  SSA disabled ')

    def enable_ssa(self, display=True):
        self.ssastate = True
        self.__enable_disable_chip()
        if(display):
            utils.print_log('->  SSA enabled ')

    def disable_mpa(self, display=True):
        self.mpastate = False
        self.__enable_disable_chip()
        if(display): utils.print_log('->  MPA disabled ')

    def enable_mpa(self, display=True):
        self.mpastate = True
        self.__enable_disable_chip()
        if(display):
            utils.print_log('->  MPA enabled ')

    def __enable_disable_chip(self):
        #val = (self.mpaid << 5) | (self.ssaid << 1) | (self.ssastate << 0) + (self.mpastate << 4)
        #val = (self.ssaid << 1) | (self.ssastate << 0)

        # Jennet needs this for MPA
        val = (self.mpaid << 5) | (self.mpastate << 4)
        utils.print_enable(False)
        time.sleep(0.01); self.fc7.Configure_MPA_SSA_I2C_Master(1, 2);
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02); # route to 2nd PCF8574
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0, verbose = 0);  # drop reset bit
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, val);  # set reset bit
        time.sleep(0.01);
        utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)

#	def reset(self, display=True, mode = 'auto'):
#		utils.print_enable(False)
#		#time.sleep(0.01);
#		self.fc7.Configure_MPA_SSA_I2C_Master(1, 2);
#		#time.sleep(0.01);
#		self.fc7.Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02, note='pcbi2cmux'); # route to 2nd PCF8574
#		if(mode == 'auto'):
#			self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b0, note='pcf8574');  # drop reset bit
#			time.sleep(0.01);
#			self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b1, note='pcf8574');  # set reset bit
#			if(display): utils.print_log( '->  Sent Hard-Reset pulse ')
#		else:
#			self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, int(mode), note='pcf8574');  # drop reset bit
#			if(display): utils.print_log( '->  SSA Enabled ' if mode == 1 else '->  SSA Disabled ')
#		time.sleep(0.01);
#		utils.activate_I2C_chip(self.fc7)
#		utils.print_enable(True)
#		utils.activate_I2C_chip(self.fc7)
#		if(display):
#			if(mode == 'auto'): utils.print_log( '->  Sent Hard-Reset pulse ')
#			else: utils.print_log( '->  SSA Enabled ' if mode == 1 else '->  SSA Disabled ')

    def _disable(self, display=True):
        utils.print_enable(False)
        time.sleep(0.01); self.fc7.Configure_MPA_SSA_I2C_Master(1, 2, verbose = 0);
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02, verbose = 0); # route to 2nd PCF8574
        time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0, verbose = 0);  # drop reset bit
        time.sleep(0.01);
        utils.activate_I2C_chip(self.fc7)
        utils.print_enable(True)
        if(display): print('->  \tMPA disabled ')

#	def _disable_ssa(self, display=True):
#		utils.print_enable(False)
#		time.sleep(0.01); self.fc7.Configure_MPA_SSA_I2C_Master(1, 2);
#		time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02, note='pcbi2cmux'); # route to 2nd PCF8574
#		time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b0, note='pcf8574');  # drop reset bit
#		time.sleep(0.01);
#		utils.activate_I2C_chip(self.fc7)
#		utils.print_enable(True)
#		if(display): utils.print_log( '->  SSA disabled ')
#
#	def _enable_ssa(self, display=True):
#		utils.print_enable(False)
#		time.sleep(0.01); self.fc7.Configure_MPA_SSA_I2C_Master(1, 2);
#		time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcbi2cmux, 0, self.pcbwrite, 0, 0x02, note='pcbi2cmux'); # route to 2nd PCF8574
#		time.sleep(0.01); self.fc7.Send_MPA_SSA_I2C_Command(self.pcf8574,   0, self.pcbwrite, 0, 0b1, note='pcf8574');  # set reset bit
#		time.sleep(0.01);
#		utils.activate_I2C_chip(self.fc7)
#		utils.print_enable(True)
#		if(display): utils.print_log( '->  SSA enabled ')

    def set_vbg(self, targetvoltage = 0.280):
        val = 0x37 if (self.chip == 'SSA') else 0x36
        utils.print_enable(False)
        if (targetvoltage > 0.5):
            targetvoltage = 0.5
        Vc2 = 4095/1.5
        setvoltage = int(round(targetvoltage * Vc2))
        setvoltage = setvoltage << 4
        self.fc7.Configure_MPA_SSA_I2C_Master(1, 2)
        self.fc7.Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01, note='i2cmux')  # to SCO on PCA9646
        self.fc7.Send_MPA_SSA_I2C_Command(self.dac7678, 0, self.pcbwrite, val, setvoltage, note='dac7678')  # tx to DAC C
        utils.activate_I2C_chip(self.fc7)
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
        self.mpastate = False
        self.ssastate = False
