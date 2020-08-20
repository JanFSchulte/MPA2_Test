from PyChipsUser import *
import sys
import os
from time import sleep
from fc7_lib import *

# Read in an address table by creating an AddressTable object (Note the forward slashes, not backslashes!)
fc7AddrTable = AddressTable('./fc7AddrTable.dat')

f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)

# enable
wr = 1
rd = 0
i2c_en    = 1
i2c_sel   = 0
i2c_presc = 1000
unused    = 0x00

i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc

fc7.write("i2c_settings", i2c_settings_value)
sleep(0.5)

#  (slv  ,r/w, regaddr, wrdata, m,16, dbg, max_attempts, text)
i2c(0x70 , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )
i2c(0x40 , wr, unused , 0xe6  , 0, 0, 1  , 10 )
i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )
print
i2c(0x70 , wr, unused , 0x02  , 0, 0, 1  , 10 )
i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4c , wr, 0x01   , 0x5f  , 1, 0, 1  , 10 )
i2c(0x4d , wr, 0x01   , 0x5e  , 1, 0, 1  , 10 )
i2c(0x4e , wr, 0x01   , 0x5c  , 1, 0, 1  , 10 )
i2c(0x4f , wr, 0x01   , 0x58  , 1, 0, 1  , 10 )

i2c(0x4c , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4c , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4d , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4d , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4e , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4e , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4f , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4f , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )

print
i2c(0x70 , wr, unused , 0x04  , 0, 0, 1  , 10 )
i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4c , wr, 0x01   , 0x5f  , 1, 0, 1  , 10 )
i2c(0x4d , wr, 0x01   , 0x5e  , 1, 0, 1  , 10 )
i2c(0x4e , wr, 0x01   , 0x5c  , 1, 0, 1  , 10 )
i2c(0x4f , wr, 0x01   , 0x58  , 1, 0, 1  , 10 )

i2c(0x4c , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4c , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4d , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4d , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4e , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4e , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4f , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4f , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )

print
i2c(0x70 , wr, unused , 0x08  , 0, 0, 1  , 10 )
i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4c , wr, 0x01   , 0x5f  , 1, 0, 1  , 10 )
i2c(0x4d , wr, 0x01   , 0x5e  , 1, 0, 1  , 10 )
i2c(0x4e , wr, 0x01   , 0x5c  , 1, 0, 1  , 10 )
i2c(0x4f , wr, 0x01   , 0x58  , 1, 0, 1  , 10 )

i2c(0x4c , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4c , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4d , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4d , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4e , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4e , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x4f , wr, unused , 0x01  , 0, 0, 1  , 10 )
i2c(0x4f , rd, unused , unused, 0, 0, 1  , 10 )

i2c(0x70 , rd, unused , unused, 0, 0, 1  , 10 )

i2c_en    = 0
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)