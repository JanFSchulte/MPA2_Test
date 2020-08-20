from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")

########################################
# IP address
########################################
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
print
print "--=======================================--"
print "  Opening fc7 with IP", ipaddr
print "--=======================================--"
########################################

spi_comm = 0x8FA38014;
cdce_readcommand = 0x8E 

deassert_powerup = 0
assert_powerup  = 1
deassert_sync = 0
assert_sync = 1

print 
print "-> ctrl value      ", uInt32HexStr(fc7.read ("ctrl")) 

print 
fc7.write("cdce_ctrl_sel", 1) # controlled by IPbus
print
fc7.write("cdce_sync", deassert_sync)
fc7.read ("ctrl") # dummy read
fc7.read ("ctrl") # dummy read
print "-> deasserting sync", uInt32HexStr(fc7.read ("ctrl")) 

print
fc7.write("cdce_sync", assert_sync)
fc7.read ("ctrl") # dummy read
fc7.read ("ctrl") # dummy read
print "-> asserting sync  ", uInt32HexStr(fc7.read ("ctrl")) 



fc7.write("spi_txdata",cdce_readcommand)
fc7.write("spi_command", spi_comm)
fc7.write("spi_txdata",0xAAAAAAAA) # dummy write
fc7.write("spi_command", spi_comm);
RdBuffer = fc7.read("spi_rxdata")
print
print "-> reg 08 contents ",uInt32HexStr(RdBuffer)

fc7.write("cdce_ctrl_sel", 0) # controlled by user




print
print "-> done"



print
print "--=======================================--"
print
print
