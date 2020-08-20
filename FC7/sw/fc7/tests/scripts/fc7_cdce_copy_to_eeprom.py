from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")

spi_comm = 0x8FA38014;
cdce_write_to_eeprom_unlocked = 0x0000001F

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

print
print "-> copying the register contents to EEPROM"
print
fc7.write("spi_txdata", cdce_write_to_eeprom_unlocked)
fc7.write("spi_command", spi_comm)
fc7.read("spi_rxdata") # dummy read
fc7.read("spi_rxdata") # dummy read

print
print "--=======================================--"
print
print 
