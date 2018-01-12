########################################
# library calls
########################################
from PyChipsUser import *
########################################



########################################
# define fc7 object
########################################
fc7AddrTable = AddressTable("./d19cScripts/fc7AddrTable.dat")
f = open('./d19cScripts/ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
########################################



########################################
def i2c(slave_addr, wr, reg_addr, wrdata, mem=0, m16b=0, debug=0, max_attempts=10, text=""):
########################################
	comm    = m16b*(2**25) + mem*(2**24) + wr*(2**23) + slave_addr *(2**16) + reg_addr *(2**8) + wrdata

	fc7.write("i2c_command", comm | 0x80000000) # strobe high
	fc7.write("i2c_command", comm)              # strobe low

	status	 = "busy"
	attempts = 0
	rddata   = 0xff

	while (status == "busy" and attempts <= max_attempts):
		#reply = fc7.read("i2c_reply")
		#print uInt32HexStr(reply)
		i2c_status = fc7.read("i2c_reply_status")
		attempts = attempts +1
		#
		if (i2c_status==1):
			status = "done"
			if m16b==0: rddata = fc7.read("i2c_reply_8b")
			if m16b==1: rddata = fc7.read("i2c_reply_16b")
		elif 	(i2c_status==0):
			status = "busy"
		else:
			status = "fail"
		#
	if debug==1:
		if wr==1 and m16b==0: print "-> slave",'%02x' % slave_addr, "wrdata", '%02x' % wrdata, status, text
		if wr==1 and m16b==1: print "-> slave",'%02x' % slave_addr, "wrdata", '%04x' % wrdata, status, text
		if wr==0 and m16b==0: print "-> slave",'%02x' % slave_addr, "rddata", '%02x' % rddata, status, text
		if wr==0 and m16b==1: print "-> slave",'%02x' % slave_addr, "rddata", '%04x' % rddata, status, text
		#

	return rddata
########################################



########################################
def usr_i2c(slave_addr, wr, reg_addr, wrdata, mem=0, m16b=0, debug=0, text=""):
########################################

	max_attempts = 10

	reg_i2c_settings_offset = 13
	reg_i2c_command_offset  = 14
	reg_i2c_reply_offset    = 15

	strobe 	= 1
	comm    = strobe*(2**31) + m16b*(2**25) + mem*(2**24) + wr*(2**23) + slave_addr *(2**16) + reg_addr *(2**8) + wrdata
	fc7.write("user_ipb_regs", comm, reg_i2c_command_offset)
	#print uInt32HexStr(comm)
	strobe 	= 0
	comm    = strobe*(2**31) + m16b*(2**25) + mem*(2**24) + wr*(2**23) + slave_addr *(2**16) + reg_addr *(2**8) + wrdata
	fc7.write("user_ipb_regs", comm, reg_i2c_command_offset)

	status	 = "busy"
	attempts = 0
	rddata   = 0xff

	while (status == "busy" and attempts <= max_attempts):
		#reply = fc7.read("user_ipb_regs", reg_i2c_reply_offset)
		#print uInt32HexStr(reply)
		i2c_status = (fc7.read("user_ipb_regs", reg_i2c_reply_offset) & 0x0c000000)/(2**26) # bit27-> error, bit26-> transaction finished
		attempts = attempts +1
		#
		if (i2c_status==1):
			status = "done"
			if m16b==0: rddata = fc7.read("user_ipb_regs", reg_i2c_reply_offset) & 0xff
			if m16b==1: rddata = fc7.read("user_ipb_regs", reg_i2c_reply_offset) & 0xffff
		#	reply = fc7.read("user_ipb_regs", reg_i2c_reply_offset)
		#	print uInt32HexStr(reply)
		elif 	(i2c_status==0):
			status = "busy"
		else:
			status = "fail"
		#
	if debug==1:
		if wr==1 and m16b==0: print "-> slave",'%02x' % slave_addr, "wrdata", '%02x' % wrdata, status, text
		if wr==1 and m16b==1: print "-> slave",'%02x' % slave_addr, "wrdata", '%04x' % wrdata, status, text
		if wr==0 and m16b==0: print "-> slave",'%02x' % slave_addr, "rddata", '%02x' % rddata, status, text
		if wr==0 and m16b==1: print "-> slave",'%02x' % slave_addr, "rddata", '%04x' % rddata, status, text
	#
########################################
