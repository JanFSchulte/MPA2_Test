########################################
# library calls
########################################
from PyChipsUser import *
from time import sleep
from d19cScripts.fc7_lib import *
#
import sys
args = sys.argv
arg_length = len(args)
#
from Tkinter import *
import time
import tkMessageBox
import tkFileDialog
import decimal
import ConfigParser
########################################
# basic d19c methods include
from d19cScripts.fc7_daq_methods import *

from d19cScripts import *
#from myScripts import *


#
########################################
# define fc7 object
########################################

#fc7AddrTable = AddressTable("./fc7AddrTable.dat")
#f = open('./d19cScripts/ipaddr.dat', 'r')
#ipaddr = f.readline()
#f.close()
#fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)


def SelectBoard(name):
	global ipaddr
	global fc7AddrTable
	global fc7
	if name == 'mpa' or name == 'MPA' or name == 0:
		f = open('./myScripts/ipaddr_mpa.dat', 'r')
		ipaddr = f.readline()
		f.close()
		print('MPA Board Selected on IP address: ' + str(ipaddr))
	elif name == 'ssa' or name == 'SSA' or name == 1:
		f = open('./myScripts/ipaddr_ssa.dat', 'r')
		ipaddr = f.readline()
		f.close()
		print('SSA Board Selected on IP address: ' + str(ipaddr))
	fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
	fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
	return ipaddr, fc7AddrTable, fc7



print '\n'
text = raw_input("Select board: mpa or ssa: ")
ipaddr, fc7AddrTable, fc7 = SelectBoard(text)
print '\n\n\n'

########################################
class BControl():
    def __init__(self):
        self.setting = 'default'
        self.readout = 'both'
        self.formatstring = 'noprocessing'
        self.threshold = '90'
        self.testbeam_clock = '1'
        self.title = 'none'
        self.shutter_duration = '0xFFFFF'
        self.normalize = 'False'

    def exit(self):
        print("Exit by Exit button in UI\n")
        sys.exit(0)

# define the i2c slave map signle item
class I2C_SlaveMapItem:
	def __init__(self):
        	self.i2c_address = 0
        	self.register_address_nbytes = 0
		self.data_wr_nbytes = 1
		self.data_rd_nbytes = 1
		self.stop_for_rd_en = 0
		self.nack_en = 0
		self.chip_name = "UNKNOWN"
	def SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en, chip_name):
		self.i2c_address = i2c_address
        	self.register_address_nbytes = register_address_nbytes
		self.data_wr_nbytes = data_wr_nbytes
		self.data_rd_nbytes = data_rd_nbytes
		self.stop_for_rd_en = stop_for_rd_en
		self.nack_en = nack_en
		self.chip_name = chip_name

# encode slave map item:
def EncodeSlaveMapItem(slave_item):

	# this peace of code just shifts the data, also checks if it fits the field
	shifted_i2c_address = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_i2c_address").shiftDataToMask(slave_item.i2c_address)
	shifted_register_address_nbytes = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_register_address_nbytes").shiftDataToMask(slave_item.register_address_nbytes)
	shifted_data_wr_nbytes = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_data_wr_nbytes").shiftDataToMask(slave_item.data_wr_nbytes)
	shifted_data_rd_nbytes = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_data_rd_nbytes").shiftDataToMask(slave_item.data_rd_nbytes)
	shifted_stop_for_rd_en = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_stop_for_rd_en").shiftDataToMask(slave_item.stop_for_rd_en)
	shifted_nack_en = fc7AddrTable.getItem("cnfg_mpa_ssa_board_slave_0_config_nack_en").shiftDataToMask(slave_item.nack_en)

	final_command = shifted_i2c_address + shifted_register_address_nbytes + shifted_data_wr_nbytes + shifted_data_rd_nbytes + shifted_stop_for_rd_en + shifted_nack_en

	return final_command

# setting the i2c slave map
#def SetSlaveMap():
#	# define the map itself
#	i2c_slave_map = [I2C_SlaveMapItem() for i in range(16)]
#
#	# set the values
#	# --- SetValues(self, i2c_address, register_address_nbytes, data_wr_nbytes, data_rd_nbytes, stop_for_rd_en, nack_en) --
#	i2c_slave_map[0].SetValues(0b1110000, 0, 1, 1, 0, 1, "PCA9646")
#	i2c_slave_map[1].SetValues(0b0100000, 0, 1, 1, 0, 1, "PCF8574")
#	i2c_slave_map[2].SetValues(0b0100100, 0, 1, 1, 0, 1, "PCF8574")
#	i2c_slave_map[3].SetValues(0b0010100, 0, 2, 3, 0, 1, "LTC2487")
#	i2c_slave_map[4].SetValues(0b1001000, 1, 2, 2, 0, 0, "DAC7678")
#	i2c_slave_map[5].SetValues(0b1000000, 1, 2, 2, 0, 1, "INA226")
#	i2c_slave_map[6].SetValues(0b1000001, 1, 2, 2, 0, 1, "INA226")
#	i2c_slave_map[7].SetValues(0b1000010, 1, 2, 2, 0, 1, "INA226")
#	i2c_slave_map[8].SetValues(0b1000100, 1, 2, 2, 0, 1, "INA226")
#	i2c_slave_map[9].SetValues(0b1000101, 1, 2, 2, 0, 1, "INA226")
#	i2c_slave_map[10].SetValues(0b1000110, 1, 2, 2, 0, 1, "INA226")
#	i2c_slave_map[15].SetValues(0b1011111, 1, 1, 1, 1, 0, "CBC3")
#
#	# updating the slave id table
#	print "---> Updating the Slave ID Map"
#	for slave_id in range(16):
#		fc7.write("cnfg_mpa_ssa_board_slave_" + str(slave_id) + "_config", EncodeSlaveMapItem(i2c_slave_map[slave_id]))

# i2c masters configuration
def Configure_MPA_SSA_I2C_Master(enabled, frequency=4):
	## ------ if enabled=1, enables the mpa ssa i2c master and disables the main one
	## ------ frequency: 0 - 0.1MHz, 1 - 0.2MHz, 2 - 0.4MHz, 3 - 0.8MHz, 4 - 1MHz, 5 - 2 MHz, 6 - 4MHz, 7 - 5MHz, 8 - 8MHz, 9 - 10MHz

	if enabled > 0:
		print "---> Enabling the MPA SSA Board I2C master"
	else:
		print "---> Disabling the MPA SSA Board I2C master"

	# sets the main CBC, MPA, SSA i2c master
	fc7.write("cnfg_phy_i2c_master_en", int(not enabled))
	# sets the MPA SSA board I2C master
	fc7.write("cnfg_mpa_ssa_board_i2c_master_en", enabled)

	# sets the frequency
	fc7.write("cnfg_mpa_ssa_board_i2c_freq", frequency)

	# wait a bit
	sleep(0.1)

	# now reset all the I2C related stuff
	fc7.write("ctrl_command_i2c_reset", 1)
	fc7.write("ctrl_command_i2c_reset_fifos", 1)
	fc7.write("ctrl_mpa_ssa_board_reset", 1)
	sleep(0.1)

def Send_MPA_SSA_I2C_Command(slave_id, board_id, read, register_address, data):

	# this peace of code just shifts the data, also checks if it fits the field
	# general
	shifted_command_type = fc7AddrTable.getItem("mpa_ssa_i2c_request_command_type").shiftDataToMask(8)
	shifted_word_id_0 = fc7AddrTable.getItem("mpa_ssa_i2c_request_word_id").shiftDataToMask(0)
	shifted_word_id_1 = fc7AddrTable.getItem("mpa_ssa_i2c_request_word_id").shiftDataToMask(1)
	# command specific
	shifted_slave_id = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_slave_id").shiftDataToMask(slave_id)
	shifted_board_id = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_board_id").shiftDataToMask(board_id)
	shifted_read = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_read").shiftDataToMask(read)
	shifted_register_address = fc7AddrTable.getItem("mpa_ssa_i2c_request_word0_register").shiftDataToMask(register_address)
	shifted_data = fc7AddrTable.getItem("mpa_ssa_i2c_request_word1_data").shiftDataToMask(data)

	# composing the word
	word_0 = shifted_command_type + shifted_word_id_0 + shifted_slave_id + shifted_board_id + shifted_read + shifted_register_address
	word_1 = shifted_command_type + shifted_word_id_1 + shifted_data

	# writing the command
	fc7.write("ctrl_command_i2c_command_fifo", word_0)
	fc7.write("ctrl_command_i2c_command_fifo", word_1)

	# wait for the reply to come back
	while fc7.read("stat_command_i2c_fifo_replies_empty") > 0:
		ReadStatus()
		sleep(0.1)

	# get the reply
	reply = fc7.read("ctrl_command_i2c_reply_fifo")
#	reply2 = fc7.read("ctrl_command_i2c_reply_fifo")
#	reply3 = fc7.read("ctrl_command_i2c_reply_fifo")

	reply_slave_id = DataFromMask(reply, "mpa_ssa_i2c_reply_slave_id")
	reply_board_id = DataFromMask(reply, "mpa_ssa_i2c_reply_board_id")
	reply_err = DataFromMask(reply, "mpa_ssa_i2c_reply_err")
	reply_data = DataFromMask(reply, "mpa_ssa_i2c_reply_data")

	# print full word
	print "Full Reply Word: ", hex(reply)
#	print "Full Reply Word2: ", hex(reply2)
#	print "Full Reply Word3: ", hex(reply3)

	# check the data
	if reply_err == 1:
		print "ERROR! Error flag is set to 1. The data is treated as the error code."
		print "Error code: ", hex(reply_data)
	elif reply_slave_id != slave_id:
		print "ERROR! Slave ID doesn't correspond to the one sent"
	elif reply_board_id != board_id:
		print "ERROR! Board ID doesn't correspond to the one sent"

	else:
		if read == 1:
			print "Data that was read is: ", hex(reply_data)
                        return reply_data
		else:
			print "Successful write transaction"
                        return 0

##----- end methods definition


########################################
# main
########################################


Vlimit = 1.3

def About():
    tkMessageBox.showinfo("About", "This is version 1.0\nDec, 2017")

def Exit():
    # disables the mpa/ssa i2c master
    Configure_MPA_SSA_I2C_Master(0)
    print "Exiting.."
    sys.exit(0)

def filesave():
    f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".cfg")
    if f is None: # return `None` if dialog closed with "cancel".
        return
    f.write("[RTB-config]\n");
    f.write("MPaPSTVdd=" + str(mpavddentry.get()) + "\n")
    f.write("MPaDigitalVdd=" + str(mpavddDentry.get()) + "\n")
    f.write("MPaAnalogVdd=" + str(mpavddAentry.get()) + "\n")
    f.write("SSaPSTVdd=" + str(ssavddentry.get()) + "\n")
    f.write("SSaDigitalVdd=" + str(ssavddDentry.get()) + "\n")
    f.write("SSaAnalogVdd=" + str(ssavddAentry.get()) + "\n")
    f.write("BGtest=" + str(dac0entry.get()) + "\n")
    f.write("VBF=" + str(dac1entry.get()) + "\n")
    f.write("MPaAddress=" + str(mpaaddressentry.get()) + "\n")
    f.write("SSaAddress=" + str(ssaaddressentry.get()) + "\n")
    f.close()

def fileopen():
    filename = tkFileDialog.askopenfilename(initialdir=".",title="Select file",filetypes=(("cfg files",".cfg"),("all files","*.*")))
    print "Loading: " + filename
    if (filename != ""):
        configParser = ConfigParser.ConfigParser()
        configParser.readfp(open(filename))
    #    tmp = configParser.get('RTB-config', 'MPaPSTVdd');
        mpavddentry.delete(0,END)
        mpavddentry.insert(END, configParser.get('RTB-config', 'MPaPSTVdd'));
        mpavddDentry.delete(0,END)
        mpavddDentry.insert(END, configParser.get('RTB-config', 'MPaDigitalVdd'));
        mpavddAentry.delete(0,END)
        mpavddAentry.insert(END, configParser.get('RTB-config', 'MPaAnalogVdd'));
        ssavddentry.delete(0,END)
        ssavddentry.insert(END, configParser.get('RTB-config', 'SSaPSTVdd'));
        ssavddDentry.delete(0,END)
        ssavddDentry.insert(END, configParser.get('RTB-config', 'SSaDigitalVdd'));
        ssavddAentry.delete(0,END)
        ssavddAentry.insert(END, configParser.get('RTB-config', 'SSaAnalogVdd'));
        dac0entry.delete(0,END)
        dac0entry.insert(END, configParser.get('RTB-config', 'BGtest'));
        dac1entry.delete(0,END)
        dac1entry.insert(END, configParser.get('RTB-config', 'VBF'));
        mpaaddressentry.delete(0,END)
        mpaaddressentry.insert(END, configParser.get('RTB-config', 'MPaAddress'));
        ssaaddressentry.delete(0,END)
        ssaaddressentry.insert(END, configParser.get('RTB-config', 'SSaAddress'));


def zeroentryfields():
    mpavddentry.delete(0,END)
    mpavddentry.insert(END,"0.0")
    mpavddDentry.delete(0,END)
    mpavddDentry.insert(END,"0.0")
    mpavddAentry.delete(0,END)
    mpavddAentry.insert(END,"0.0")
    ssavddentry.delete(0,END)
    ssavddentry.insert(END,"0.0")
    ssavddDentry.delete(0,END)
    ssavddDentry.insert(END,"0.0")
    ssavddAentry.delete(0,END)
    ssavddAentry.insert(END,"0.0")
    dac0entry.delete(0,END)
    dac0entry.insert(END,"0.0")
    dac1entry.delete(0,END)
    dac1entry.insert(END,"0.0")
    mpaaddressentry.delete(0,END)
    mpaaddressentry.insert(END, "0")
    ssaaddressentry.delete(0,END)
    ssaaddressentry.insert(END, "0")

def mpavddwrite():
    print "Write MPA vdd"
    print mpavddentry.get()
    targetvoltage = float(mpavddentry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        mpavddentry.delete(0,END)
        mpavddentry.insert(END,targetvoltage)
    print targetvoltage
    diffvoltage = 1.5 - targetvoltage
    setvoltage = int(round(diffvoltage / Vc))
    if (setvoltage > 4095):
        setvoltage = 4095
    print hex(setvoltage)
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x34, setvoltage)  # tx to DAC C

def mpavddread():
    print "Read MPA MAIN Shunt chip V I P"
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
    ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x02, 0)  # read V on shunt
    print hex(ret)
    #vret = Vcshunt * ret
    vret = 0.00125 * ret
    vret = float(round(vret, 3))
    print vret
    mpavddVentry.delete(0,'end')
    mpavddVentry.insert(0,format(vret,'.3f'))
    ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x01, 0)  #read VR on shunt
    print hex(ret)
    print ret
    iret = (Vcshunt * ret)/Rshunt
    iret = float(round(iret, 3))
    print iret
    mpavddIentry.delete(0,'end')
    mpavddIentry.insert(0,format(iret,'.3f'))
    pret = iret * vret
    pret = float(round(pret, 3))
    mpavddPentry.delete(0,'end')
    mpavddPentry.insert(0,format(pret,'.3f'))

def mpavddDwrite():
    print "Write MPA DIGITAL vdd"
    print mpavddDentry.get()
    targetvoltage = float(mpavddDentry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        mpavddDentry.delete(0,END)
        mpavddDentry.insert(END,targetvoltage)
    diffvoltage = 1.5 - targetvoltage
    setvoltage = int(round(diffvoltage / Vc))
    print hex(setvoltage)
    if (setvoltage > 4095):
        setvoltage = 4095
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x30, setvoltage)  # tx to DAC C

def mpavddDread():
    print "Read MPA DIGITAL Shunt chip V I P"
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
    ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x02, 0)  # read V on shunt
    print hex(ret)
    #vret = Vcshunt * ret
    vret = 0.00125 * ret
    vret = float(round(vret, 3))
    print vret
    mpavddDVentry.delete(0,'end')
    mpavddDVentry.insert(0,format(vret,'.3f'))
    ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt
    print hex(ret)
    iret = (Vcshunt * ret)/Rshunt
    #iret = (0.00125 * ret)/Rshunt
    iret = float(round(iret, 3))
    print iret
    mpavddDIentry.delete(0,'end')
    mpavddDIentry.insert(0,format(iret,'.3f'))
    pret = iret * vret
    pret = float(round(pret, 3))
    mpavddDPentry.delete(0,'end')
    mpavddDPentry.insert(0,format(pret,'.3f'))


def mpavddAwrite():
    print "Write MPA ANALOG vdd"
    targetvoltage = float(mpavddAentry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        mpavddAentry.delete(0,END)
        mpavddAentry.insert(END,targetvoltage)
    diffvoltage = 1.5 - targetvoltage
    setvoltage = int(round(diffvoltage / Vc))
    print hex(setvoltage)
    if (setvoltage > 4095):
        setvoltage = 4095
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x32, setvoltage)  # tx to DAC C

def mpavddAread():
    print "Read MPA ANALOG Shunt chip V I P"
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
    ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x02, 0)  # read V on shunt
    print hex(ret)
    #vret = Vcshunt * ret
    vret = 0.00125 * ret
    vret = float(round(vret, 3))
    print vret
    mpavddAVentry.delete(0,'end')
    mpavddAVentry.insert(0,format(vret,'.3f'))
    ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0)  # read V on shunt
    print hex(ret)
    iret = (Vcshunt * ret)/Rshunt
    iret = float(round(iret, 3))
    print iret
    mpavddAIentry.delete(0,'end')
    mpavddAIentry.insert(0,format(iret,'.3f'))
    pret = iret * vret
    pret = float(round(pret, 3))
    mpavddAPentry.delete(0,'end')
    mpavddAPentry.insert(0,format(pret,'.3f'))

## now SSA
def ssavddwrite():
    print "Write SSA vdd - testing"
    print ssavddentry.get()
    targetvoltage = float(ssavddentry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        ssavddentry.delete(0,END)
        ssavddentry.insert(END,targetvoltage)
    diffvoltage = 1.5 - targetvoltage
    setvoltage = int(round(diffvoltage / Vc))
    print hex(setvoltage)
    if (setvoltage > 4095):
        setvoltage = 4095
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x33, setvoltage)  # tx to DAC C

def ssavddread():
    print "Read SSA MAIN Shunt chip V I P"
    print "Read V from shunt"
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
    ret=Send_MPA_SSA_I2C_Command(ina226_7, 0, read, 0x02, 0)  # read V on shunt
    print hex(ret)
    #vret = Vcshunt * ret
    vret = 0.00125 * ret
    vret = float(round(vret, 3))
    print vret
    ssavddVentry.delete(0,'end')
    ssavddVentry.insert(0,format(vret,'.3f'))
    ret=Send_MPA_SSA_I2C_Command(ina226_7, 0, read, 0x01, 0)  # read V on shunt
    print hex(ret)
    iret = (Vcshunt * ret)/Rshunt
    iret = float(round(iret, 3))
    print iret
    ssavddIentry.delete(0,'end')
    ssavddIentry.insert(0,format(iret,'.3f'))
    pret = iret * vret
    pret = float(round(pret, 3))
    ssavddPentry.delete(0,'end')
    ssavddPentry.insert(0,format(pret,'.3f'))

def ssavddDwrite():
    print "Write SSA DIGITAL vdd"
    print ssavddDentry.get()
    targetvoltage = float(ssavddDentry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        ssavddDentry.delete(0,END)
        ssavddDentry.insert(END,targetvoltage)
    diffvoltage = 1.5 - targetvoltage
    setvoltage = int(round(diffvoltage / Vc))
    print hex(setvoltage)
    if (setvoltage > 4095):
        setvoltage = 4095
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x31, setvoltage)  # tx to DAC C

def ssavddDread():
    print "Read SSA DIGITAL Shunt chip V I P"
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
    ret=Send_MPA_SSA_I2C_Command(ina226_6, 0, read, 0x02, 0)  # read V on shunt
    print hex(ret)
    #vret = Vcshunt * ret
    vret = 0.00125 * ret
    vret = float(round(vret, 3))
    print vret
    ssavddDVentry.delete(0,'end')
    ssavddDVentry.insert(0,format(vret,'.3f'))
    ret=Send_MPA_SSA_I2C_Command(ina226_6, 0, read, 0x01, 0)  # read V on shunt
    print hex(ret)
    iret = (Vcshunt * ret)/Rshunt
    iret = float(round(iret, 3))
    print iret
    ssavddDIentry.delete(0,'end')
    ssavddDIentry.insert(0,format(iret,'.3f'))
    pret = iret * vret
    pret = float(round(pret, 3))
    ssavddDPentry.delete(0,'end')
    ssavddDPentry.insert(0,format(pret,'.3f'))


def ssavddAwrite():
    print "Write SSA ANALOG vdd"
    print ssavddAentry.get()
    targetvoltage = float(ssavddAentry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        ssavddAentry.delete(0,END)
        ssavddAentry.insert(END,targetvoltage)
    diffvoltage = 1.5 - targetvoltage
    setvoltage = int(round(diffvoltage / Vc))
    print hex(setvoltage)
    if (setvoltage > 4095):
        setvoltage = 4095
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x35, setvoltage)  # tx to DAC C

def ssavddAread():
    print "Read SSA ANALOG Shunt chip V I P"
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
    ret=Send_MPA_SSA_I2C_Command(ina226_5, 0, read, 0x02, 0)  # read V on shunt
    print hex(ret)
    #vret = Vcshunt * ret
    vret = 0.00125 * ret
    vret = float(round(vret, 3))
    print vret
    ssavddAVentry.delete(0,'end')
    ssavddAVentry.insert(0,format(vret, '.3f'))
    ret=Send_MPA_SSA_I2C_Command(ina226_5, 0, read, 0x01, 0)  # read V on shunt
    print hex(ret)
    iret = (Vcshunt * ret)/Rshunt
    iret = float(round(iret, 3))
    print iret
    ssavddAIentry.delete(0,'end')
    ssavddAIentry.insert(0,format(iret, '.3f'))
    pret = iret * vret
    pret = float(round(pret, 3))
    ssavddAPentry.delete(0,'end')
    ssavddAPentry.insert(0,format(pret, '.3f'))

def bgtestwrite():
    print "BGtest write: " + dac0entry.get()
    targetvoltage = float(dac0entry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        dac0entry.delete(0,END)
        dac0entry.insert(END,targetvoltage)
    Vc2 = 4095/1.5
    setvoltage = int(round(targetvoltage * Vc2))
    print hex(setvoltage)
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x36, setvoltage)  # tx to DAC C



def vbfwrite():
    print "VBF write: " + dac1entry.get()
    targetvoltage = float(dac1entry.get())
    if (targetvoltage > Vlimit):
        targetvoltage = Vlimit
        dac1entry.delete(0,END)
        dac1entry.insert(END,targetvoltage)
    Vc2 = 4095/1.5
    setvoltage = int(round(targetvoltage * Vc2))
    print hex(setvoltage)
    setvoltage = setvoltage << 4
    print hex(setvoltage)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
    Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x37, setvoltage)  # tx to DAC C

def mpaanalogtestread():
    adc0entry.delete(0,'end')
    print "ADC0 READ: " + adc0entry.get()
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SC0 on PCA9646
    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xB080)#0xB080)  #0b1011000010101000
    sleep(0.2)
    ret = Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0, 0)  #
    iret = hex(ret)
    bret = bin(ret)
    print bret
#    adc0entry.insert(0,iret)
    rret = ret >> 6
    rret = rret & 0x0000FFFF
    print bin(rret)
    print rret
    rvoltage = rret/43371.0
    print rvoltage
    rvoltage = float(round(rvoltage, 5))
    adc0entry.delete(0,'end')
    adc0entry.insert(0,format(rvoltage, '.5f'))

def ssaanalogtestread():
    adc1entry.delete(0,'end')
    print "ADC1 READ: " + adc1entry.get()
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SC0 on PCA9646
    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xB180)  #
    sleep(0.2)
    ret = Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0, 0)  #
    iret = hex(ret)
    bret = bin(ret)
    print bret
#    adc1entry.insert(0,iret)
    rret = ret >> 6
    rret = rret & 0x0000FFFF
    print bin(rret)
    print rret
    rvoltage = rret/43371.0
    print rvoltage
    rvoltage = float(round(rvoltage, 5))
    adc1entry.delete(0,'end')
    adc1entry.insert(0,format(rvoltage, '.5f'))

def ssaanalogtestread2():
    adc1entry.delete(0,'end')
    print "ADC1 READ: " + adc1entry.get()
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SC0 on PCA9646
#    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xC2C0)  # set temp sensor
#    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xC07F)  # set temp sensor
##    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xA0D0)  # set temp sensor
#    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xB080)  #
#    Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xB180)  #
##    sleep(1)
##    Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0, 0)  #
#    ret=Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0xC0C0, 0)  #
#    iret = hex(ret)
#    adc1entry.insert(0,iret)
    logfile = open("logfile.dat", "w")
    for i in range(1,10):
        Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xA0C0)  # set temp sensor
        sleep(1)
        ret0 = Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0, 0)  #
        Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xA0D0)  # set temp sensor
        sleep(1)
        ret = Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0, 0)  #
        sleep(1)
        Send_MPA_SSA_I2C_Command(ltc2487, 0, write, 0, 0xA0E0)  # set temp sensor
        sleep(1)
        ret2 = Send_MPA_SSA_I2C_Command(ltc2487, 0, read, 0, 0)  #
        sleep(1)
        logfile.write(str(i) + ',' + str(int(ret0)) + ',' + str(int(ret)) + ','+ str(int(ret2)) + '\n')

    logfile.close()


def mpaaddresswrite():
    print "MPA set address: " + mpaaddressentry.get()
    mpaid = int(mpaaddressentry.get())
    ssaid = int(ssaaddressentry.get())
    val = (mpaid << 5) + (ssaid << 1)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val)  # send 8bit port
    print hex(val)
#    sleep(1)
#    ret=Send_MPA_SSA_I2C_Command(pcf8574, 0, read, 2, 0)  # send 8bit port
#    print hex(ret)

def ssaaddresswrite():
    print "SSA set address: " + ssaaddressentry.get()
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val = (mpaid << 5) + (ssaid << 1)
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val)  # send 8bit port
    print hex(val)


#    fc7.write("mpa_ssa_fifo_control", 0x12345678)
#    sleep(1)
#    reply = hex(fc7.read("mpa_ssa_fifo_control"))
#    print reply


def mainpoweron():
    # first set all fields to what each field entry widget says it is
    setallfields()
    print "MAIN Power ON"
    # send command to turn power on.  First set speed and route i2cmux then send
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    # On powerup port defaults to on, so inverter is needed.
    # send on bit (12-2017).  Inverter must be manually soldered to board
    Send_MPA_SSA_I2C_Command(powerenable, 0, write, 0, 0x00)  # send on bit


def mainpoweroff():
    print "MAIN Power OFF"
    # send command to turn power off.First set speed and route i2cmux then send
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    # On powerup port defaults to on, so inverter is needed.
    # off bit (12-2017). Inverter must be manually soldered to board
    Send_MPA_SSA_I2C_Command(powerenable, 0, write, 0, 0x07)  # send off bit
    #Send_MPA_SSA_I2C_Command(powerenable, 0, write, 0, 0x01)  # send off bit


def mpareset():
    global mpastate, ssastate
    print "MPA reset"
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val  = (mpaid << 5) + (ssaid << 1)
    val2 = (mpaid << 5) + (ssaid << 1) + 16 # reset bit for MPA
    if(ssastate):
        val2 += 1
        val  += 1
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val)  # drop reset bit
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2)  # set reset bit
    print "\n\n" + bin(val2) + "\n\n"
    mpastate = True

def mpaenable():
    global mpastate, ssastate
    print "MPA enable"
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val2 = (mpaid << 5) + (ssaid << 1) + 16 # reset bit for MPA
    if(ssastate):
        val2 += 1
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2)  # set reset bit
    print "\n\n" + bin(val2) + "\n\n"
    mpastate = True

def mpadisable():
    global mpastate, ssastate
    print "MPA disable"
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val = (mpaid << 5) + (ssaid << 1)
    if(ssastate):
        val += 1
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val)  # set reset bit
    print "\n\n" + bin(val) + "\n\n"
    mpastate = False

def ssareset():
    global mpastate, ssastate
    print "SSA reset"
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val  = (mpaid << 5) + (ssaid << 1)
    val2 = (mpaid << 5) + (ssaid << 1) + 1 # reset bit for SSA
    if(mpastate):
        val2 += 16
        val  += 16
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val)  # drop reset bit
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2)  # set reset bit
    print "\n\n" + bin(val2) + "\n\n"
    ssastate = True

def ssaenable():
    global mpastate, ssastate
    print "SSA enable"
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val2 = (mpaid << 5) + (ssaid << 1) + 1 # reset bit for SSA
    if(mpastate):
        val2 += 16
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2)  # set reset bit
    print "\n\n" + bin(val2) + "\n\n"
    ssastate = True

def ssadisable():
    global mpastate, ssastate
    print "SSA disable"
    ssaid = int(ssaaddressentry.get())
    mpaid = int(mpaaddressentry.get())
    val = (mpaid << 5) + (ssaid << 1)
    if(mpastate):
        val += 16
    Configure_MPA_SSA_I2C_Master(1, SLOW)
    Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
    Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val)  # set reset bit
    print "\n\n" + bin(val) + "\n\n"
    ssastate = False

def setallfields():
    mpavddwrite()
    mpavddDwrite()
    mpavddAwrite()
    ssavddwrite()
    ssavddDwrite()
    ssavddAwrite()
    bgtestwrite()
    vbfwrite()
    mpaaddresswrite()
    ssaaddresswrite()

bcontrol = BControl()
root = Tk()
menu = Menu(root)
root.config(menu=menu)
filemenu = Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Exit", command=Exit)
helpmenu=Menu(menu)
menu.add_cascade(label="Help", menu=helpmenu)
helpmenu.add_command(label="About..", command=About)

bcontrolui = Frame(root)
bcontrolui.grid()
root.title("MPa/SSa Test Board")
root.geometry("700x575")
#root.configure(background='light blue')
root.resizable(False,False)

mytext = "Voltage (" + str(Vlimit) + "V max)"
mpavddlabel0 = Label(bcontrolui, text=mytext)
mpavddlabel0.grid(row=2,column=1, pady=0)

mpavddlabel = Label(bcontrolui, text="MPa PST Vdd")
mpavddlabel.grid(row=3,column=0, padx=10)
mpavalue=StringVar()
mpavddentry = Entry(bcontrolui, width=7, textvariable=mpavalue)
mpavddentry.delete(0,END)
mpavddentry.insert(END,"1.2500")
mpavddentry.grid(row=3, column=1, pady=0)
mpavddwritebutton = Button(bcontrolui, text="Set", command=mpavddwrite)
mpavddwritebutton.grid(row=3, column=2)
filllabel = Label(bcontrolui, text="       ")
filllabel.grid(row=2,column=3, pady=0)
mpavddVlabel = Label(bcontrolui, text="V")
mpavddVlabel.grid(row=2,column=4, pady=0)
mpavddVentry = Entry(bcontrolui, width=5)
mpavddVentry.grid(row=3, column=4, pady=0)
mpavddVentry.insert(0, "?")
mpavddIlabel = Label(bcontrolui, text="I(mA)")
mpavddIlabel.grid(row=2,column=5, pady=0)
mpavddIentry = Entry(bcontrolui, width=5)
mpavddIentry.grid(row=3, column=5, pady=0)
mpavddIentry.insert(0, "?")
mpavddPlabel = Label(bcontrolui, text="P(mW)")
mpavddPlabel.grid(row=2,column=6, pady=0)
mpavddPentry = Entry(bcontrolui, width=5)
mpavddPentry.grid(row=3, column=6, pady=0)
mpavddPentry.insert(0, "?")
mpavddreadbutton = Button(bcontrolui, text="Measure", command=mpavddread)
mpavddreadbutton.grid(row=3, column=7)

mpavddDlabel = Label(bcontrolui, text="MPa Digital Vdd")
mpavddDlabel.grid(row=4,column=0, padx=10)
mpaDvalue=StringVar()
mpavddDentry = Entry(bcontrolui, width=7, textvariable=mpaDvalue)
mpavddDentry.insert(END,"1.0000")
mpavddDentry.grid(row=4, column=1, pady=0)
mpavddDwritebutton = Button(bcontrolui, text="Set", command=mpavddDwrite)
mpavddDwritebutton.grid(row=4, column=2)
mpavddDVentry = Entry(bcontrolui, width=5)
mpavddDVentry.grid(row=4, column=4, pady=0)
mpavddDVentry.insert(0, "?")
mpavddDIentry = Entry(bcontrolui, width=5)
mpavddDIentry.grid(row=4, column=5, pady=0)
mpavddDIentry.insert(0, "?")
mpavddDPentry = Entry(bcontrolui, width=5)
mpavddDPentry.grid(row=4, column=6, pady=0)
mpavddDPentry.insert(0, "?")
mpavddDreadbutton = Button(bcontrolui, text="Measure", command=mpavddDread)
mpavddDreadbutton.grid(row=4, column=7)

mpavddAlabel = Label(bcontrolui, text="MPa Analog Vdd")
mpavddAlabel.grid(row=5,column=0, padx=10)
mpavalue=StringVar()
mpavddAentry = Entry(bcontrolui, width=7, textvariable=mpavalue)
mpavddAentry.insert(END,"1.2500")
mpavddAentry.grid(row=5, column=1, pady=0)
mpavddAwritebutton = Button(bcontrolui, text="Set", command=mpavddAwrite)
mpavddAwritebutton.grid(row=5, column=2)
mpavddAVentry = Entry(bcontrolui, width=5)
mpavddAVentry.grid(row=5, column=4, pady=0)
mpavddAVentry.insert(0, "?")
mpavddAIentry = Entry(bcontrolui, width=5)
mpavddAIentry.grid(row=5, column=5, pady=0)
mpavddAIentry.insert(0, "?")
mpavddAPentry = Entry(bcontrolui, width=5)
mpavddAPentry.grid(row=5, column=6, pady=0)
mpavddAPentry.insert(0, "?")
mpavddAreadbutton = Button(bcontrolui, text="Measure", command=mpavddAread)
mpavddAreadbutton.grid(row=5, column=7)

hrlabel = Label(bcontrolui, text=" ")
hrlabel.grid(row=6,column=0)

ssavddlabel = Label(bcontrolui, text="SSa PST Vdd")
ssavddlabel.grid(row=7,column=0, padx=10)
mpavalue=StringVar()
ssavddentry = Entry(bcontrolui, width=7, textvariable=mpavalue)
ssavddentry.insert(END,"1.2500")
ssavddentry.grid(row=7, column=1, pady=0)
ssavddwritebutton = Button(bcontrolui, text="Set", command=ssavddwrite)
ssavddwritebutton.grid(row=7, column=2)
ssavddVentry = Entry(bcontrolui, width=5)
ssavddVentry.grid(row=7, column=4, pady=0)
ssavddVentry.insert(0, "?")
ssavddIentry = Entry(bcontrolui, width=5)
ssavddIentry.grid(row=7, column=5, pady=0)
ssavddIentry.insert(0, "?")
ssavddPentry = Entry(bcontrolui, width=5)
ssavddPentry.grid(row=7, column=6, pady=0)
ssavddPentry.insert(0, "?")
ssavddreadbutton = Button(bcontrolui, text="Measure", command=ssavddread)
ssavddreadbutton.grid(row=7, column=7)

ssavddDlabel = Label(bcontrolui, text="SSa Digital Vdd")
ssavddDlabel.grid(row=8,column=0, padx=10)
mpaDvalue=StringVar()
ssavddDentry = Entry(bcontrolui, width=7, textvariable=mpaDvalue)
ssavddDentry.insert(END,"1.0000")
ssavddDentry.grid(row=8, column=1, pady=0)
ssavddDwritebutton = Button(bcontrolui, text="Set", command=ssavddDwrite)
ssavddDwritebutton.grid(row=8, column=2)
ssavddDVentry = Entry(bcontrolui, width=5)
ssavddDVentry.grid(row=8, column=4, pady=0)
ssavddDVentry.insert(0, "?")
ssavddDIentry = Entry(bcontrolui, width=5)
ssavddDIentry.grid(row=8, column=5, pady=0)
ssavddDIentry.insert(0, "?")
ssavddDPentry = Entry(bcontrolui, width=5)
ssavddDPentry.grid(row=8, column=6, pady=0)
ssavddDPentry.insert(0, "?")
ssavddDreadbutton = Button(bcontrolui, text="Measure", command=ssavddDread)
ssavddDreadbutton.grid(row=8, column=7)

ssavddAlabel = Label(bcontrolui, text="SSa Analog Vdd")
ssavddAlabel.grid(row=9,column=0, padx=10)
mpavalue=StringVar()
ssavddAentry = Entry(bcontrolui, width=7, textvariable=mpavalue)
ssavddAentry.insert(END,"1.2500")
ssavddAentry.grid(row=9, column=1, pady=0)
ssavddAwritebutton = Button(bcontrolui, text="Set", command=ssavddAwrite)
ssavddAwritebutton.grid(row=9, column=2)
ssavddAVentry = Entry(bcontrolui, width=5)
ssavddAVentry.grid(row=9, column=4, pady=0)
ssavddAVentry.insert(0, "?")
ssavddAIentry = Entry(bcontrolui, width=5)
ssavddAIentry.grid(row=9, column=5, pady=0)
ssavddAIentry.insert(0, "?")
ssavddAPentry = Entry(bcontrolui, width=5)
ssavddAPentry.grid(row=9, column=6, pady=0)
ssavddAPentry.insert(0, "?")
ssavddAreadbutton = Button(bcontrolui, text="Measure", command=ssavddAread)
ssavddAreadbutton.grid(row=9, column=7)

hrlabel2 = Label(bcontrolui, text=" ")
hrlabel2.grid(row=10,column=0,pady=10)

dac0label = Label(bcontrolui, text="BGtest:")
dac0label.grid(row=11,column=0, padx=0, sticky=E)
dac0value=StringVar()
dac0entry = Entry(bcontrolui, width=7, textvariable=dac0value)
dac0entry.insert(END,"?")
dac0entry.grid(row=11, column=1, pady=0)
dac0writebutton = Button(bcontrolui, text="Set", command=bgtestwrite)
dac0writebutton.grid(row=11, column=2)

dac1label = Label(bcontrolui, text="VBF:")
dac1label.grid(row=12,column=0, padx=0, sticky=E)
dac1value=StringVar()
dac1entry = Entry(bcontrolui, width=7, textvariable=dac1value)
dac1entry.insert(END,"?")
dac1entry.grid(row=12, column=1, pady=0)
dac1writebutton = Button(bcontrolui, text="Set", command=vbfwrite)
dac1writebutton.grid(row=12, column=2)

##
adc0label = Label(bcontrolui, text="MPA Analog Test:")
adc0label.grid(row=11,column=4, padx=0, sticky=E)
adc0value=StringVar()
adc0entry = Entry(bcontrolui, width=7, textvariable=adc0value)
adc0entry.insert(END,"?")
adc0entry.grid(row=11, column=5, pady=0)
adc0writebutton = Button(bcontrolui, text="Measure", command=mpaanalogtestread)
adc0writebutton.grid(row=11, column=6)

adc1label = Label(bcontrolui, text="SSA Analog Test:")
adc1label.grid(row=12,column=4, padx=0, sticky=E)
adc1value=StringVar()
adc1entry = Entry(bcontrolui, width=7, textvariable=adc1value)
adc1entry.insert(END,"?")
adc1entry.grid(row=12, column=5, pady=0)
adc1writebutton = Button(bcontrolui, text="Measure", command=ssaanalogtestread)
adc1writebutton.grid(row=12, column=6)

##
hrlabel3 = Label(bcontrolui, text=" ")
hrlabel3.grid(row=13,column=0,pady=10)


mpaaddresslabel = Label(bcontrolui, text="MPa Address: ")
mpaaddresslabel.grid(row=14,column=0, padx=0, sticky=E)
mpaaddressvalue=StringVar()
mpaaddressentry = Entry(bcontrolui, width=2, textvariable=mpaaddressvalue)
mpaaddressentry.insert(END,"0")
mpaaddressentry.grid(row=14, column=1, pady=0)
mpaaddressbutton = Button(bcontrolui, text="Set", command=mpaaddresswrite)
mpaaddressbutton.grid(row=14, column=2)

ssaaddresslabel = Label(bcontrolui, text="SSa Address: ")
ssaaddresslabel.grid(row=14,column=4, padx=0, sticky=E)
ssaaddressvalue=StringVar()
ssaaddressentry = Entry(bcontrolui, width=2, textvariable=ssaaddressvalue)
ssaaddressentry.insert(END,"7")
ssaaddressentry.grid(row=14, column=5, pady=0)
ssaaddressbutton = Button(bcontrolui, text="Set", command=ssaaddresswrite)
ssaaddressbutton.grid(row=14, column=6)

##
hrlabel4 = Label(bcontrolui, text=" ")
hrlabel4.grid(row=15,column=0,pady=10)


mainpowerlabel = Label(bcontrolui, text="Main Power: ")
mainpowerlabel.grid(row=16,column=0, padx=0, sticky=E)
mainpoweronbutton = Button(bcontrolui, text="On", command=mainpoweron)
mainpoweronbutton.grid(row=16, column=1)
mainpoweroffbutton = Button(bcontrolui, text="Off", command=mainpoweroff)
mainpoweroffbutton.grid(row=16, column=2)

#resetlabel = Label(bcontrolui, text="   Reset:")
#resetlabel.grid(row=16,column=4, padx=0, sticky=E)
mparesetbutton = Button(bcontrolui, text="MPA reset", command=mpareset)
mparesetbutton.grid(row=16, column=4)
mpaenablebutton = Button(bcontrolui, text="MPA enable", command=mpaenable)
mpaenablebutton.grid(row=17, column=4)
mpadisablebutton = Button(bcontrolui, text="MPA disable", command=mpadisable)
mpadisablebutton.grid(row=18, column=4)
ssaresetbutton = Button(bcontrolui, text="SSA reset", command=ssareset)
ssaresetbutton.grid(row=16, column=5)
ssaenablebutton = Button(bcontrolui, text="SSA enable", command=ssaenable)
ssaenablebutton.grid(row=17, column=5)
ssadisablebutton = Button(bcontrolui, text="SSA disable", command=ssadisable)
ssadisablebutton.grid(row=18, column=5)

#
hrlabel5 = Label(bcontrolui, text=" ")
hrlabel5.grid(row=17,column=0,pady=10)


filelabel = Label(bcontrolui, text="File: ")
filelabel.grid(row=18,column=0, padx=0, sticky=E)
filereadbutton = Button(bcontrolui, text="Load", command=fileopen)
filereadbutton.grid(row=18, column=1)
filewritebutton = Button(bcontrolui, text="Save", command=filesave)
filewritebutton.grid(row=18, column=2)

setallbutton = Button(bcontrolui, text="Set ALL", command=setallfields)
setallbutton.grid(row=18, column=7)

#button_exit = Button(bcontrolui, text="Exit")
#button_exit["command"]=lambda: bcontrol.exit()
#button_exit.grid(row=99,column=0, pady=5)



# constants

read = 1
write = 0
cbc3 = 15
FAST = 4
SLOW = 2

mpaid = 0 # default MPa address (0-7)
ssaid = 0 # default SSa address (0-7)

i2cmux = 0
pcf8574 = 1 # MPA and SSA address and reset 8 bit port
powerenable = 2    # i2c ID 0x44
dac7678 = 4
ina226_5 = 5
ina226_6 = 6
ina226_7 = 7
ina226_8 = 8
ina226_9 = 9
ina226_10 = 10
ltc2487 = 3
ssastate = False
mpastate = False

Vc = 0.0003632813 # V/Dac step
#Vcshunt = 5.0/4000
Vcshunt = 0.00250
Rshunt = 0.1
##----- end constants

# Reset the board
print "---> Sending global_reset to fc7 board"
SendCommand_CTRL("global_reset")
sleep(1)

# loads the slave map (needs to be done after each reset of the d19c)
SetSlaveMap()
# sets the mpa/ssa i2c master config
Configure_MPA_SSA_I2C_Master(1)
global s
#######


print "Mainloop"

zeroentryfields()

root.mainloop()




global s








# import sys
# args = sys.argv
# arg_length = len(args)

# if arg_length == 3: # script name + two parameters
# else:

	# print
	# print "-> Error!!! arguments are required."
	# print "-> "
	# print "-> Syntax:"
	# print "-> "
	# print "-> fc7_i2c_set_voltage.py <L8|L12> <p3v3|p2v5|p1v8>"
	# print "-> "
