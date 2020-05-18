from time import sleep
from myScripts.Utilities import *


class onboard_adc():

    def __init__(self):
        self.__set_variables()

    def measure(self, chip = 'SSA', naverages = 1, raw = False):
        utils.print_enable(False)
        if(  chip in ['SSA', 'ssa', 0]):
            cmd = self.ssaCMD
        elif(chip in ['MPA', 'mpa', 1]):
            cmd = self.mpaCMD
        else:
            return False
        Configure_MPA_SSA_I2C_Master(1, self.SLOW)
        Send_MPA_SSA_I2C_Command(self.i2cmux,  0, self.pcbwrite, 0, 0x01)  # to SC0 on PCA9646
        Send_MPA_SSA_I2C_Command(self.ltc2487, 0, self.pcbwrite, 0, 0xB180)  #
        time.sleep(0.2)
        varray=[]
        for i in range(0,naverages):
            reply = Send_MPA_SSA_I2C_Command(self.ltc2487, 0, self.pcbread, 0, 0)  #
            code  = (reply >> 6) & self.ltc2487_mask
            if(raw):
                utils.print_enable(True)
                return code
            rv = code / self.ltc2487_gain
            varray.append(rv)
        voltage = np.mean(varray)
        utils.activate_I2C_chip()
        utils.print_enable(True)
        return voltage

    def __set_variables(self):
        self.pcbwrite = 0;
        self.pcbread = 1;
        self.i2cmux = 0;
        self.bias_dl_enable    = False
        self.FAST = 4
        self.SLOW = 2
        self.mpaCMD = 0xB080
        self.ssaCMD = 0xB180
        self.ltc2487 = 3
        self.ltc2487_mask = 0x0000FFFF
        self.ltc2487_gain = 43371.0
