# uhal
import uhal
# sleep
from time import sleep
# os to get folder
import os

## fc7 interface class
class fc7_interface:
    # init class
    def __init__(self, name, uri, address_table):
        # set log level
        uhal.setLogLevelTo(uhal.LogLevel.ERROR)
        # assign vars
        self.name = name
        self.uri = uri
        self.address_table = address_table
        # init hardware
        self.hw = uhal.getDevice(name, uri, address_table)
    
    # simple read
    def read(self, reg_name, p2 = 0):
        # read the value
        reg = self.hw.getNode(reg_name).read()
        # transaction
        self.hw.dispatch()
        # return
        return reg.value() 

    # simple write
    def write(self, reg_name, value, p3 = 0): # p3...dummy parameter
        # write the value
        self.hw.getNode(reg_name).write(value)
        # transaction
        self.hw.dispatch()

    def blockRead(self, reg_name, value, p3 = 0):
        ret = self.hw.getNode(reg_name).readBlock(value)
        self.hw.dispatch()
        return ret

    def blockWrite(self, reg_name, value, p3 = 0):
        self.hw.getNode(reg_name).writeBlock(value)
        self.hw.dispatch()
