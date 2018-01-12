########################################
# library calls
########################################
from PyChipsUser import *
from time import sleep
from fc7_lib import *
########################################



########################################
# define fc7 object
########################################
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
########################################



########################################
# main
########################################

# constants

RegBuffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RdxBuffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

LTC2990 = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]




i2c_slv   = 0x4c
i2c_all   = 0x77
wr = 1
rd = 0
unused = 0x00

single = 1
repeat = 0
trig   = 0x01
# variables

acq = single

# enable i2c

i2c_en    = 1
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)
fc7.queueClear()



reg = 0x00
ctrl = (acq<<6)+0x1f # mode V1,V2,V3,V4 voltage measurements


################################################################
# global sync 
################################################################

#(slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
i2c(i2c_all, wr, 0x01   , ctrl  , 1     , unused, 0    )
#print
#print "-> set mode (single acq)"
#(slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
i2c(i2c_all, wr, 0x02   , trig  , 1     , unused, 0    )
#print
#print "-> trigger acquisition"
sleep(0.5)


for j in range (0,4):
	################################################################
	# get voltages
	################################################################
	#print
	for i in range(0,16):
		#                 (slvaddr,r/w, regaddr, wrdata, m     , 16    , debug)
		RdxBuffer[i] = i2c(i2c_slv+j, wr, unused , reg+i , unused, unused, 0    )
		RegBuffer[i] = i2c(i2c_slv+j, rd, unused , unused, unused, unused, 0    )
		
	LTC2990[5*j+0]  = ((RegBuffer[0x06] & 0x03f)	<< 8) + RegBuffer[0x07]
	LTC2990[5*j+1]  = ((RegBuffer[0x08] & 0x03f)	<< 8) + RegBuffer[0x09]
	LTC2990[5*j+2]  = ((RegBuffer[0x0a] & 0x03f)	<< 8) + RegBuffer[0x0b]
	LTC2990[5*j+3]  = ((RegBuffer[0x0c] & 0x03f)	<< 8) + RegBuffer[0x0d]
	LTC2990[5*j+4]  = ((RegBuffer[0x0e] & 0x03f)	<< 8) + RegBuffer[0x0f]

#print
#for i in range(0,20):
#	print "-> LTC2990[%02d] = %04X" % (i,LTC2990[i])

	
################################################################
# calculate (external dividers, Vcc)
################################################################

LTC2990[0] = 0.00030518 * LTC2990[0]*((4.7+4.7)/4.7)
LTC2990[1] = 0.00030518 * LTC2990[1]*((4.7+4.7)/4.7)
LTC2990[2] = 0.00030518 * LTC2990[2]*((4.7+4.7)/4.7)
LTC2990[3] = 0.00030518 * LTC2990[3]*((4.7+4.7)/4.7)
LTC2990[4] = 0.00030518 * LTC2990[4] + 2.5

LTC2990[5] = 0.00030518 * LTC2990[5]*((4.7+1.18)/1.18)
LTC2990[6] = 0.00030518 * LTC2990[6]*((4.7+1.18)/1.18)
LTC2990[7] = 0.00030518 * LTC2990[7]
LTC2990[8] = 0.00030518 * LTC2990[8]
LTC2990[9] = 0.00030518 * LTC2990[9] + 2.5

LTC2990[10]= 0.00030518 * LTC2990[10]*((4.7+4.7)/4.7)
LTC2990[11]= 0.00030518 * LTC2990[11]*((4.7+4.7)/4.7)
LTC2990[12]= 0.00030518 * LTC2990[12]*((4.7+4.7)/4.7)
LTC2990[13]= 0.00030518 * LTC2990[13]*((4.7+4.7)/4.7)
LTC2990[14]= 0.00030518 * LTC2990[14] + 2.5
           
LTC2990[15]= 0.00030518 * LTC2990[15]*((4.7+1.18)/1.18)
LTC2990[16]= 0.00030518 * LTC2990[16]*((4.7+1.18)/1.18)
LTC2990[17]= 0.00030518 * LTC2990[17]
LTC2990[18]= 0.00030518 * LTC2990[18]
LTC2990[19]= 0.00030518 * LTC2990[19] + 2.5

################################################################
# print
################################################################
print
print "-> U18 V2  =  %.2fV  :          L8_VADJ" % (LTC2990[1])
print "-> U18 V1  =  %.2fV  :    SENSE_L8_VADJ" % (LTC2990[0])
print "-> U18 V4  =  %.2fV  :            +3.3V" % (LTC2990[3])
print "-> U18 V3  =  %.2fV  :   SENSE_L8_+3.3V" % (LTC2990[2])
#print "-> U18 Vcc =  %.2fV  :          U18 Vcc" % (LTC2990[4])
print "-> U83 V2  = %.2fV  :           +12.0V" % (LTC2990[6])
print "-> U83 V1  = %.2fV  :  SENSE_L8_+12.0V" % (LTC2990[5])
#print "-> U83 V3  =  %.2fV"                    % (LTC2990[7])
#print "-> U83 V4  =  %.2fV"                    % (LTC2990[8])
#print "-> U83 Vcc =  %.2fV  :          U83 Vcc" % (LTC2990[9])
print
print "-> U73 V2  =  %.2fV  :         L12_VADJ" % (LTC2990[11])
print "-> U73 V1  =  %.2fV  :   SENSE_L12_VADJ" % (LTC2990[10])
print "-> U73 V4  =  %.2fV  :            +3.3V" % (LTC2990[13])
print "-> U73 V3  =  %.2fV  :  SENSE_L12_+3.3V" % (LTC2990[12])
#print "-> U73 Vcc =  %.2fV  :          U73 Vcc" % (LTC2990[14])
print "-> U74 V2  = %.2fV  :           +12.0V" % (LTC2990[16])
print "-> U74 V1  = %.2fV  : SENSE_L12_+12.0V" % (LTC2990[15])
#print "-> U74 V3  =  %.2fV" 				   % (LTC2990[17])
#print "-> U74 V4  =  %.2fV"                    % (LTC2990[18])
#print "-> U74 Vcc =  %.2fV  :          U74 Vcc" % (LTC2990[19])
print









#print "-> disabling i2c controller "
#fc7.write("i2c_settings", i2c_ctrl_disable)	

i2c_en    = 0
i2c_sel   = 0
i2c_presc = 500
i2c_settings_value = i2c_en*(2**15) + i2c_sel*(2**10) + i2c_presc
fc7.write("i2c_settings", i2c_settings_value)