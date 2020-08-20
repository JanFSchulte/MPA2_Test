from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
from time import sleep
import sys
import os
from fc7_lib import *

########################################
# IP address
########################################
f = open('./ipaddr.dat', 'r')
ipaddr = f.readline()
f.close()
fc7 = ChipsBusUdp(fc7AddrTable, ipaddr, 50001)
########################################

debug=0
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug=1
#





fmcL8_error_cnt = [0,0,0,0,0,0,0,0]
fmcL8_bits_cnt  = [0,0,0,0,0,0,0,0]

fmcL12_error_cnt = [0,0,0,0,0,0,0,0,0,0,0,0]
fmcL12_bits_cnt  = [0,0,0,0,0,0,0,0,0,0,0,0]

amc_error_cnt = [0,0,0,0,0,0,0,0,0,0,0,0]
amc_bits_cnt  = [0,0,0,0,0,0,0,0,0,0,0,0]

fc7.write("gtx_bert_reset", 1, 0)
fc7.write("gtx_bert_reset", 0, 0)

fmcL8_error_cnt[0]   = fc7.read("errCnt_fmcL8_berCnt_H_0" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_0")
fmcL8_bits_cnt[0]    = fc7.read("bitsCnt_fmcL8_berCnt_H_0")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_0")
fmcL8_error_cnt[1]   = fc7.read("errCnt_fmcL8_berCnt_H_1" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_1")
fmcL8_bits_cnt[1]    = fc7.read("bitsCnt_fmcL8_berCnt_H_1")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_1")
fmcL8_error_cnt[2]   = fc7.read("errCnt_fmcL8_berCnt_H_2" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_2")
fmcL8_bits_cnt[2]    = fc7.read("bitsCnt_fmcL8_berCnt_H_2")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_2")
fmcL8_error_cnt[3]   = fc7.read("errCnt_fmcL8_berCnt_H_3" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_3")
fmcL8_bits_cnt[3]    = fc7.read("bitsCnt_fmcL8_berCnt_H_3")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_3")
fmcL8_error_cnt[4]   = fc7.read("errCnt_fmcL8_berCnt_H_4" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_4")
fmcL8_bits_cnt[4]    = fc7.read("bitsCnt_fmcL8_berCnt_H_4")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_4")
fmcL8_error_cnt[5]   = fc7.read("errCnt_fmcL8_berCnt_H_5" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_5")
fmcL8_bits_cnt[5]    = fc7.read("bitsCnt_fmcL8_berCnt_H_5")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_5")
fmcL8_error_cnt[6]   = fc7.read("errCnt_fmcL8_berCnt_H_6" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_6")
fmcL8_bits_cnt[6]    = fc7.read("bitsCnt_fmcL8_berCnt_H_6")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_6")
fmcL8_error_cnt[7]   = fc7.read("errCnt_fmcL8_berCnt_H_7" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_7")
fmcL8_bits_cnt[7]    = fc7.read("bitsCnt_fmcL8_berCnt_H_7")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_7")

fmcL12_error_cnt[0]  = fc7.read("errCnt_fmcL12_berCnt_H_0" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_0")
fmcL12_bits_cnt[0]   = fc7.read("bitsCnt_fmcL12_berCnt_H_0")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_0")
fmcL12_error_cnt[1]  = fc7.read("errCnt_fmcL12_berCnt_H_1" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_1")
fmcL12_bits_cnt[1]   = fc7.read("bitsCnt_fmcL12_berCnt_H_1")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_1")
fmcL12_error_cnt[2]  = fc7.read("errCnt_fmcL12_berCnt_H_2" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_2")
fmcL12_bits_cnt[2]   = fc7.read("bitsCnt_fmcL12_berCnt_H_2")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_2")
fmcL12_error_cnt[3]  = fc7.read("errCnt_fmcL12_berCnt_H_3" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_3")
fmcL12_bits_cnt[3]   = fc7.read("bitsCnt_fmcL12_berCnt_H_3")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_3")
fmcL12_error_cnt[4]  = fc7.read("errCnt_fmcL12_berCnt_H_4" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_4")
fmcL12_bits_cnt[4]   = fc7.read("bitsCnt_fmcL12_berCnt_H_4")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_4")
fmcL12_error_cnt[5]  = fc7.read("errCnt_fmcL12_berCnt_H_5" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_5")
fmcL12_bits_cnt[5]   = fc7.read("bitsCnt_fmcL12_berCnt_H_5")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_5")
fmcL12_error_cnt[6]  = fc7.read("errCnt_fmcL12_berCnt_H_6" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_6")
fmcL12_bits_cnt[6]   = fc7.read("bitsCnt_fmcL12_berCnt_H_6")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_6")
fmcL12_error_cnt[7]  = fc7.read("errCnt_fmcL12_berCnt_H_7" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_7")
fmcL12_bits_cnt[7]   = fc7.read("bitsCnt_fmcL12_berCnt_H_7")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_7")
fmcL12_error_cnt[8]  = fc7.read("errCnt_fmcL12_berCnt_H_8" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_8")
fmcL12_bits_cnt[8]   = fc7.read("bitsCnt_fmcL12_berCnt_H_8")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_8")
fmcL12_error_cnt[9]  = fc7.read("errCnt_fmcL12_berCnt_H_9" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_9")
fmcL12_bits_cnt[9]   = fc7.read("bitsCnt_fmcL12_berCnt_H_9")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_9")
fmcL12_error_cnt[10] = fc7.read("errCnt_fmcL12_berCnt_H_10" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_10")
fmcL12_bits_cnt[10]  = fc7.read("bitsCnt_fmcL12_berCnt_H_10")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_10")
fmcL12_error_cnt[11] = fc7.read("errCnt_fmcL12_berCnt_H_11" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_11")
fmcL12_bits_cnt[11]  = fc7.read("bitsCnt_fmcL12_berCnt_H_11")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_11")

amc_error_cnt[1]    = fc7.read("errCnt_amc_berCnt_H_1")*2**32  +      fc7.read("errCnt_amc_berCnt_L_1")
amc_bits_cnt[1]     = fc7.read("bitsCnt_amc_berCnt_H_1")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_1") 
amc_error_cnt[2]    = fc7.read("errCnt_amc_berCnt_H_2")*2**32  +      fc7.read("errCnt_amc_berCnt_L_2")
amc_bits_cnt[2]     = fc7.read("bitsCnt_amc_berCnt_H_2")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_2") 
amc_error_cnt[3]    = fc7.read("errCnt_amc_berCnt_H_3")*2**32  +      fc7.read("errCnt_amc_berCnt_L_3")
amc_bits_cnt[3]     = fc7.read("bitsCnt_amc_berCnt_H_3")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_3") 
amc_error_cnt[4]    = fc7.read("errCnt_amc_berCnt_H_4")*2**32  +      fc7.read("errCnt_amc_berCnt_L_4")
amc_bits_cnt[4]     = fc7.read("bitsCnt_amc_berCnt_H_4")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_4") 
amc_error_cnt[5]    = fc7.read("errCnt_amc_berCnt_H_5")*2**32  +      fc7.read("errCnt_amc_berCnt_L_5")
amc_bits_cnt[5]     = fc7.read("bitsCnt_amc_berCnt_H_5")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_5") 
amc_error_cnt[6]    = fc7.read("errCnt_amc_berCnt_H_6")*2**32  +      fc7.read("errCnt_amc_berCnt_L_6")
amc_bits_cnt[6]     = fc7.read("bitsCnt_amc_berCnt_H_6")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_6") 
amc_error_cnt[7]    = fc7.read("errCnt_amc_berCnt_H_7")*2**32  +      fc7.read("errCnt_amc_berCnt_L_7")
amc_bits_cnt[7]     = fc7.read("bitsCnt_amc_berCnt_H_7")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_7") 
amc_error_cnt[8]    = fc7.read("errCnt_amc_berCnt_H_8")*2**32  +      fc7.read("errCnt_amc_berCnt_L_8")
amc_bits_cnt[8]     = fc7.read("bitsCnt_amc_berCnt_H_8")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_8") 
amc_error_cnt[9]    = fc7.read("errCnt_amc_berCnt_H_9")*2**32  +      fc7.read("errCnt_amc_berCnt_L_9")
amc_bits_cnt[9]     = fc7.read("bitsCnt_amc_berCnt_H_9")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_9") 
amc_error_cnt[10]   = fc7.read("errCnt_amc_berCnt_H_10")*2**32  +     fc7.read("errCnt_amc_berCnt_L_10")
amc_bits_cnt[10]    = fc7.read("bitsCnt_amc_berCnt_H_10")*2**32 +     fc7.read("bitsCnt_amc_berCnt_L_10") 
amc_error_cnt[11]   = fc7.read("errCnt_amc_berCnt_H_11")*2**32  +     fc7.read("errCnt_amc_berCnt_L_11")
amc_bits_cnt[11]    = fc7.read("bitsCnt_amc_berCnt_H_11")*2**32 +     fc7.read("bitsCnt_amc_berCnt_L_11") 

fc7.write("gtx_bert_trigger", 1, 0)
fc7.write("gtx_bert_trigger", 0, 0)

sleep(3)


fmcL8_error_cnt[0]   = fc7.read("errCnt_fmcL8_berCnt_H_0" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_0")
fmcL8_bits_cnt[0]    = fc7.read("bitsCnt_fmcL8_berCnt_H_0")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_0")
fmcL8_error_cnt[1]   = fc7.read("errCnt_fmcL8_berCnt_H_1" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_1")
fmcL8_bits_cnt[1]    = fc7.read("bitsCnt_fmcL8_berCnt_H_1")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_1")
fmcL8_error_cnt[2]   = fc7.read("errCnt_fmcL8_berCnt_H_2" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_2")
fmcL8_bits_cnt[2]    = fc7.read("bitsCnt_fmcL8_berCnt_H_2")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_2")
fmcL8_error_cnt[3]   = fc7.read("errCnt_fmcL8_berCnt_H_3" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_3")
fmcL8_bits_cnt[3]    = fc7.read("bitsCnt_fmcL8_berCnt_H_3")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_3")
fmcL8_error_cnt[4]   = fc7.read("errCnt_fmcL8_berCnt_H_4" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_4")
fmcL8_bits_cnt[4]    = fc7.read("bitsCnt_fmcL8_berCnt_H_4")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_4")
fmcL8_error_cnt[5]   = fc7.read("errCnt_fmcL8_berCnt_H_5" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_5")
fmcL8_bits_cnt[5]    = fc7.read("bitsCnt_fmcL8_berCnt_H_5")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_5")
fmcL8_error_cnt[6]   = fc7.read("errCnt_fmcL8_berCnt_H_6" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_6")
fmcL8_bits_cnt[6]    = fc7.read("bitsCnt_fmcL8_berCnt_H_6")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_6")
fmcL8_error_cnt[7]   = fc7.read("errCnt_fmcL8_berCnt_H_7" )*2**32 + fc7.read("errCnt_fmcL8_berCnt_L_7")
fmcL8_bits_cnt[7]    = fc7.read("bitsCnt_fmcL8_berCnt_H_7")*2**32 + fc7.read("bitsCnt_fmcL8_berCnt_L_7")

fmcL12_error_cnt[0]  = fc7.read("errCnt_fmcL12_berCnt_H_0" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_0")
fmcL12_bits_cnt[0]   = fc7.read("bitsCnt_fmcL12_berCnt_H_0")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_0")
fmcL12_error_cnt[1]  = fc7.read("errCnt_fmcL12_berCnt_H_1" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_1")
fmcL12_bits_cnt[1]   = fc7.read("bitsCnt_fmcL12_berCnt_H_1")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_1")
fmcL12_error_cnt[2]  = fc7.read("errCnt_fmcL12_berCnt_H_2" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_2")
fmcL12_bits_cnt[2]   = fc7.read("bitsCnt_fmcL12_berCnt_H_2")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_2")
fmcL12_error_cnt[3]  = fc7.read("errCnt_fmcL12_berCnt_H_3" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_3")
fmcL12_bits_cnt[3]   = fc7.read("bitsCnt_fmcL12_berCnt_H_3")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_3")
fmcL12_error_cnt[4]  = fc7.read("errCnt_fmcL12_berCnt_H_4" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_4")
fmcL12_bits_cnt[4]   = fc7.read("bitsCnt_fmcL12_berCnt_H_4")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_4")
fmcL12_error_cnt[5]  = fc7.read("errCnt_fmcL12_berCnt_H_5" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_5")
fmcL12_bits_cnt[5]   = fc7.read("bitsCnt_fmcL12_berCnt_H_5")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_5")
fmcL12_error_cnt[6]  = fc7.read("errCnt_fmcL12_berCnt_H_6" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_6")
fmcL12_bits_cnt[6]   = fc7.read("bitsCnt_fmcL12_berCnt_H_6")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_6")
fmcL12_error_cnt[7]  = fc7.read("errCnt_fmcL12_berCnt_H_7" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_7")
fmcL12_bits_cnt[7]   = fc7.read("bitsCnt_fmcL12_berCnt_H_7")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_7")
fmcL12_error_cnt[8]  = fc7.read("errCnt_fmcL12_berCnt_H_8" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_8")
fmcL12_bits_cnt[8]   = fc7.read("bitsCnt_fmcL12_berCnt_H_8")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_8")
fmcL12_error_cnt[9]  = fc7.read("errCnt_fmcL12_berCnt_H_9" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_9")
fmcL12_bits_cnt[9]   = fc7.read("bitsCnt_fmcL12_berCnt_H_9")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_9")
fmcL12_error_cnt[10] = fc7.read("errCnt_fmcL12_berCnt_H_10" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_10")
fmcL12_bits_cnt[10]  = fc7.read("bitsCnt_fmcL12_berCnt_H_10")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_10")
fmcL12_error_cnt[11] = fc7.read("errCnt_fmcL12_berCnt_H_11" )*2**32 + fc7.read("errCnt_fmcL12_berCnt_L_11")
fmcL12_bits_cnt[11]  = fc7.read("bitsCnt_fmcL12_berCnt_H_11")*2**32 + fc7.read("bitsCnt_fmcL12_berCnt_L_11")


amc_error_cnt[1]    = fc7.read("errCnt_amc_berCnt_H_1")*2**32  +      fc7.read("errCnt_amc_berCnt_L_1")
amc_bits_cnt[1]     = fc7.read("bitsCnt_amc_berCnt_H_1")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_1") 
amc_error_cnt[2]    = fc7.read("errCnt_amc_berCnt_H_2")*2**32  +      fc7.read("errCnt_amc_berCnt_L_2")
amc_bits_cnt[2]     = fc7.read("bitsCnt_amc_berCnt_H_2")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_2") 
amc_error_cnt[3]    = fc7.read("errCnt_amc_berCnt_H_3")*2**32  +      fc7.read("errCnt_amc_berCnt_L_3")
amc_bits_cnt[3]     = fc7.read("bitsCnt_amc_berCnt_H_3")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_3") 
amc_error_cnt[4]    = fc7.read("errCnt_amc_berCnt_H_4")*2**32  +      fc7.read("errCnt_amc_berCnt_L_4")
amc_bits_cnt[4]     = fc7.read("bitsCnt_amc_berCnt_H_4")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_4") 
amc_error_cnt[5]    = fc7.read("errCnt_amc_berCnt_H_5")*2**32  +      fc7.read("errCnt_amc_berCnt_L_5")
amc_bits_cnt[5]     = fc7.read("bitsCnt_amc_berCnt_H_5")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_5") 
amc_error_cnt[6]    = fc7.read("errCnt_amc_berCnt_H_6")*2**32  +      fc7.read("errCnt_amc_berCnt_L_6")
amc_bits_cnt[6]     = fc7.read("bitsCnt_amc_berCnt_H_6")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_6") 
amc_error_cnt[7]    = fc7.read("errCnt_amc_berCnt_H_7")*2**32  +      fc7.read("errCnt_amc_berCnt_L_7")
amc_bits_cnt[7]     = fc7.read("bitsCnt_amc_berCnt_H_7")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_7") 
amc_error_cnt[8]    = fc7.read("errCnt_amc_berCnt_H_8")*2**32  +      fc7.read("errCnt_amc_berCnt_L_8")
amc_bits_cnt[8]     = fc7.read("bitsCnt_amc_berCnt_H_8")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_8") 
amc_error_cnt[9]    = fc7.read("errCnt_amc_berCnt_H_9")*2**32  +      fc7.read("errCnt_amc_berCnt_L_9")
amc_bits_cnt[9]     = fc7.read("bitsCnt_amc_berCnt_H_9")*2**32 +      fc7.read("bitsCnt_amc_berCnt_L_9") 
amc_error_cnt[10]   = fc7.read("errCnt_amc_berCnt_H_10")*2**32  +     fc7.read("errCnt_amc_berCnt_L_10")
amc_bits_cnt[10]    = fc7.read("bitsCnt_amc_berCnt_H_10")*2**32 +     fc7.read("bitsCnt_amc_berCnt_L_10") 
amc_error_cnt[11]   = fc7.read("errCnt_amc_berCnt_H_11")*2**32  +     fc7.read("errCnt_amc_berCnt_L_11")
amc_bits_cnt[11]    = fc7.read("bitsCnt_amc_berCnt_H_11")*2**32 +     fc7.read("bitsCnt_amc_berCnt_L_11") 
##############################
gtx_err_fmcL8=0
for i in [0,1,2,3,4,5,6,7]:
	if fmcL8_error_cnt[i]!=0: gtx_err_fmcL8=1
	if debug==1: print "[info]: gtx |ber ch.%02d fmcL8  " % i," -> %010d" % fmcL8_error_cnt[i],"/ %010d" % fmcL8_bits_cnt[i]
if (gtx_err_fmcL8==1):
	print "[TEST]: gtx |test fmcL8         -> /FAIL/"
else:
	print "[TEST]: gtx |test fmcL8         -> /PASS/"	
if debug==1: print
##############################	
gtx_err_fmcL12=0
for i in [0,1,2,3,4,5,6,7,8,9]:
	if fmcL12_error_cnt[i]!=0: gtx_err_fmcL12=1
	if debug==1: print "[info]: gtx |ber ch.%02d fmcL12 " % i," -> %010d" % fmcL12_error_cnt[i],"/ %010d" % fmcL12_bits_cnt[i]
if (gtx_err_fmcL12==1):
	print "[TEST]: gtx |test fmcL12        -> /FAIL/"
else:
	print "[TEST]: gtx |test fmcL12        -> /PASS/"	
if debug==1: print
##############################	
gtx_err_amc=0
for i in [1,2,4,5,6,7,8,9,10,11]:
	if amc_error_cnt[i]!=0: gtx_err_amc=1
	if debug==1: print "[info]: gtx |ber ch.%02d amc    " % i," -> %010d" % amc_error_cnt[i],"/ %010d" % amc_bits_cnt[i]
if (gtx_err_amc==1):
	print "[TEST]: gtx |test amc           -> /FAIL/"
else:
	print "[TEST]: gtx |test amc           -> /PASS/"	
if debug==1: print
