from d19cScripts.fc7_daq_methods import *

def I2CTester(CBC_type):

    ReadStatus("Before I2C Configuration")
    Configure_I2C(255)
    ReadStatus("After I2C Configuration")
    fc7.write("cnfg_phy_i2c_freq",4)
    sleep(1)
    #number of registers implemented in the cbc3 emulator
    if(CBC_type == "CBC3_emulator"):
	num_i2c_registersPage1 = 35
    	num_i2c_registersPage2 = 2
    if(CBC_type == "CBC2_real"):
	num_i2c_registersPage1 = 64
	num_i2c_registersPage2 = 256	
    #the parameters of the SendCommand_I2C function are as defined below (all values in decimal). 
    # command_i2c: 0 - send command to certain hybrid/chip, 1 - send command to all chips on hybrid, 2 - send command to all chips on all hybrids, 3-broadcast to a specific hybrid, 4-broadcast to all hybrids
    #SendCommand_I2C(i2c_command , hybrid_id ,  chip_id,  page , read , register_address , data,readback); --readback is useful eg when you write it will directly readback
    
    read = 1
    write = 0
    numberOfI2C = 0
    
    ################################################reading a first time##############################################
    #read all (except non existing once) page 1 registers:
    print "page 1 initial"
    for i in range(0, num_i2c_registersPage1):
		#some register addresses are not defined in the CBC2 chip. Skip read and writes to them!
		skip_register_for_CBC2 = (CBC_type == "CBC2_real") and ((i >= int("12",16)  and i<= int("17",16)) or (i>=int("30",16) and i<= int("2a",16)) or (i>=int("1a",16) and i<=int("1f",16)))
		if(not(skip_register_for_CBC2)):
                	SendCommand_I2C(          2,         0,       1,    0, read,        i,    10, 0)
    			numberOfI2C += 1
    sleep(1)
    ReadChipData(False, 0)

    #read all page 2 registers
    print "page 2 initial"
    for i in range(0, num_i2c_registersPage2):
		SendCommand_I2C(          2,         0,       0,    1, read,        i,    10, 0)
    		numberOfI2C+=1
    sleep(1)
    ReadChipData(False, 0)

    ################################################writing##########################################################
    #write value d5 to all (except first register = with the page and the non existing registers) registers on page 1 
    for i in range(1, num_i2c_registersPage1):	
     		skip_register_for_CBC2 = (CBC_type == "CBC2_real") and ((i >= int("12",16)  and i<= int("17",16)) or (i>=int("30",16) and i<= int("2a",16)) or (i>=int("1a",16) and i<=int("1f",16)))
                if(not(skip_register_for_CBC2)):   	          	
			SendCommand_I2C(          2,         0,       0,     0, write,       i,    5, 0)
    sleep(1)
   #write value d7 to second register on page 2        
    for i in range(1, num_i2c_registersPage2):		
       		SendCommand_I2C(          2,         0,       0,     1, write,       i,    7, 0)

    sleep(1)
    ################################################reading a second time############################################
    #read all (except non existing once) page 1 registers to check the write    
    print "page 1 final"
    for i in range(0, num_i2c_registersPage1):		
		skip_register_for_CBC2 = (CBC_type == "CBC2_real") and ((i >= int("12",16)  and i<= int("17",16)) or (i>=int("30",16) and i<= int("2a",16)) or (i>=int("1a",16) and i<=int("1f",16)))
		if(not(skip_register_for_CBC2)):
       	   	     SendCommand_I2C(          2,         0,       0,     0, read,        i,    10, 0)
    
    sleep(1)
    #checking if the written value 5 is what is read
    ReadChipData(True, 5)

    #read all page 2 registers to check the write
    print "page 2 final"
    for i in range(0, num_i2c_registersPage2):		
       		SendCommand_I2C(          2,         0,       0,    1, read,        i,    10, 0)
    sleep(1)
    #checking if the written value 7 is what is read
    ReadChipData(True, 7)
    sleep(1)

    ReadStatus("After Send Command")
    ReadChipData(False,0)
    ReadStatus("After Read Reply")
    print "numberOfI2C: ", numberOfI2C

def SingleI2Ccommand():
    read = 1
    write = 0
    
    fc7.write("cnfg_phy_i2c_freq",1)
    sleep(1)
    print "cnfg_phy_i2c_freq register: ",fc7.read("cnfg_phy_i2c_freq")
    #SendCommand_I2C(i2c_command , hybrid_id ,  chip_id, page , read , register_address , data;
    SendCommand_I2C(2,          0,         0,    0,  read,                 1,    10, 0)
    sleep(1)
    ReadChipData(False, 0)
    SendCommand_I2C(2,          0,         0,    0,  write,                1,    11, 0)
    SendCommand_I2C(2,          0,         0,    0,  read,                 1,    10, 0)
    ReadStatus("After Send Command")
    sleep(1)
    ReadChipData(False,0)
    ReadStatus("After Read Reply")

def sendLotsOfRead():
    read = 1
    write = 0
    fc7.write("cnfg_phy_i2c_freq",0)
    sleep(1)
    print "cnfg_phy_i2c_freq register: ",fc7.read("cnfg_phy_i2c_freq")
    #read register 1 on all chips for i times. This will take some time for the i2c to execute as it is slow. If you read back the chipdata to fast after the sending you will not have all replies.
    #you can than increase the sleep or you can modify the i2c frequency so it goes faster.
    i = 0
    while(i<500):
	SendCommand_I2C(2,          0,         0,    0,  write,                 1,    7, 0)
    	SendCommand_I2C(2,          0,         0,    0,  read,                  1,    7, 0)
	i = i+1
    #give the i2c some time to execute	
    sleep(0)
    ReadStatus("After Send Command")
    ReadChipData(True,7)
    ReadStatus("After Read Reply")
    


####################
## Program Running #
####################
SendCommand_CTRL("global_reset")
sleep(1)

# to test I2C Commands (does a read, then a write and then reads this write off all i2c registers on the chips(except for the page registers). It will exit with an error if the written value is not the same as the read one. 
# the real CBC2 chips and the emulated CBC3 chip have some differences in the registers eg the CBC2 chip ships some register addresses + it also has more registers then the emulated chip.)
I2CTester("CBC3_emulator")

#to test a first time a single read-write-read command
#SingleI2Ccommand()

#this command has a while loop where it sends continuosly i2c writes and reads. You can use it to test the speed of the i2c. It prints at the end the number of reads. If you speed up the i2c clock by programming the cnfg_phy_i2c_freq
#register then you can increase the number of transactions within a given sleep.
#sendLotsOfRead()

# to test Fast Command Block 
#FastTester()
# set of commands one may need but not used in FastTester
#SendCommand_CTRL("fast_orbit_reset")
#SendCommand_CTRL("start_trigger")
#SendCommand_CTRL("fast_fast_reset")
#SendCommand_CTRL("fast_test_pulse")
#SendCommand_CTRL("fast_i2c_refresh")
#sleep(1)
#SendCommand_CTRL("start_trigger")
#sleep(0.00001)
#SendCommand_CTRL("stop_trigger")
#sleep(1)
