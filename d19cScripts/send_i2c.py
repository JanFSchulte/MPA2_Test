from fc7_daq_methods import *
SendCommand_CTRL("global_reset")
sleep(1)
#SendCommand_I2C(command type, hybrid_id, chip_id, page, read, register_address, data, ReadBack)
# command type: 0 - write to certain chip, hybrid; 1 - write to all chips on hybrid; 2 - write to all chips/hybrids (same for READ)
#write to register 1 24 as data
SendCommand_I2C(            0,         0,       0,    0,     0,               1,    24,       0)
#write to register 2 1 as data
SendCommand_I2C(            0,         0,       0,    0,     0,               2,    1,        0)
#read register 1
SendCommand_I2C(            0      ,   0,       0,    0,     1,               1,    0,        0)
#read register 2
SendCommand_I2C(            0      ,   0,       0,    0,     1,               2,    0,        0)
sleep(1)
ReadStatus()
ReadChipData(0,0)

