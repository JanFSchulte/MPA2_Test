from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")

spi_comm = 0x8FA38014;
cdce_readcommand = [0xE,0x1E,0x2E,0x3E,0x4E,0x5E,0x6E,0x7E,0x8E] 
RdBuffer = [0,0,0,0,0,0,0,0,0,0]

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
print "-> reading CDCE62005 registers"
print
for i in range(0,9):
	fc7.write("spi_txdata",cdce_readcommand[i])
	fc7.write("spi_command", spi_comm)
	fc7.write("spi_txdata",0xAAAAAAAA) # dummy write
	fc7.write("spi_command", spi_comm);
	RdBuffer[i] = fc7.read("spi_rxdata")
	print "-> register",'%02d' % i,"contents =",uInt32HexStr(RdBuffer[i])

print
print "--=======================================--"
print
print 