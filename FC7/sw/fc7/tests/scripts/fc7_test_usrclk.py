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

#
debug=0
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug=1
#

off = 0
red = 1
green = 2
orange = 3
blue = 4
purple = 5
#blue_green = 6
#purple_light = 7

osc_xpoint_a      = 0
osc_xpoint_b      = 1
osc_xpoint_c      = 2
osc_xpoint_d      = 3
ttc_mgt_xpoint_a  = 4
ttc_mgt_xpoint_b  = 5
ttc_mgt_xpoint_c  = 6
osc125_b          = 7
fmc_l12_gbtclk0_a = 8
fmc_l12_gbtclk1_a = 9
fmc_l12_gbtclk0_b = 10
fmc_l12_gbtclk1_b = 11
fmc_l8_gbtclk0    = 12
fmc_l8_gbtclk1 	  = 13
pcie_clk          = 14
fmc_l8_clk0       = 15
fmc_l8_clk1       = 16
fmc_l12_clk0      = 17
fmc_l12_clk1      = 18
fabric_clk        = 19

led1_colour = off
led1_input  = fabric_clk
led2_colour = red
led2_input  = fabric_clk
#
rst_value = 2**28
enable_value = 2**24
ctrl_value = led2_input*2**16 + led2_colour*2**12 + led1_input*2**4 + led1_colour
#
coax = 0
xtal = 1
fc7.write("ttc_xpoint_B_out1",xtal)		     

#
fclka = 0
tclka = 2
tclkc = 1
ckx   = 3

fabric_clk_src = tclka

fc7.write("ttc_xpoint_A_out1", ckx)	  # osc_xpoint_in1	     
fc7.write("ttc_xpoint_A_out2", ckx)	  # cdce_sec_ref	     
fc7.write("ttc_xpoint_A_out3", tclka) # normally ckx, for test purposes set to tclka		     
fc7.write("ttc_xpoint_A_out4", fclka) # source of tclkb/tclkd		     
fc7.write("tclkb_tclkd_en", 1)
# with the current config: fclka->mlvds_buf->tclkb->sma_loopback->tclka->FPGA(fabric_clk input) 

fc7.write("cdce_xpoint_out1",1)
fc7.write("cdce_xpoint_out2",1)
fc7.write("cdce_xpoint_out3",1)
fc7.write("cdce_xpoint_out4",1)
 

# set pcie gen to 125MHz
fc7.write("pcieclk_mr",0)
fc7.write("pcieclk_mr",1)
fc7.write("pcieclk_mr",0)
fc7.write("pcieclk_pll_sel",1)
#fc7.write("pcieclk_fsel1",1)
#fc7.write("pcieclk_fsel0",1)
 
#		
  
fc7.write("user_ipb_ctrl_regs",rst_value + ctrl_value,4)
fc7.write("user_ipb_ctrl_regs",rst_value + enable_value + ctrl_value,4) # clear  counters
fc7.write("user_ipb_ctrl_regs",            enable_value + ctrl_value,4) # start  counters
sleep(1)
fc7.write("user_ipb_ctrl_regs",                           ctrl_value,4) # freeze counters
#

#######################
# measure frequencies
####6##################

clkcnt = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
clkcnt = fc7.blockRead("user_ipb_stat_regs", 21, 9)

print '[info]: clk |-------------------------------'
print '[info]: clk | check frequency'
print '[info]: clk |-------------------------------'
print '[info]: clk |osc_125_a          -> %3d MHz' % (clkcnt[0] *125.0/clkcnt[0])
print '[info]: clk |ttc_mgt_xpoint_a   -> %3d MHz' % (clkcnt[6] *125.0/clkcnt[0])
print '[info]: clk |ttc_mgt_xpoint_b   -> %3d MHz' % (clkcnt[7] *125.0/clkcnt[0])
print '[info]: clk |ttc_mgt_xpoint_c   -> %3d MHz' % (clkcnt[8] *125.0/clkcnt[0])
print '[info]: clk |fmc_l12_gbtclk0_a  -> %3d MHz' % (clkcnt[9] *125.0/clkcnt[0])
print '[info]: clk |fmc_l12_gbtclk1_a  -> %3d MHz' % (clkcnt[10]*125.0/clkcnt[0])
print '[info]: clk |fmc_l12_gbtclk0_b  -> %3d MHz' % (clkcnt[11]*125.0/clkcnt[0])
print '[info]: clk |fmc_l12_gbtclk1_b  -> %3d MHz' % (clkcnt[12]*125.0/clkcnt[0])
print '[info]: clk |fmc_l8_gbtclk0     -> %3d MHz' % (clkcnt[13]*125.0/clkcnt[0])
print '[info]: clk |fmc_l8_gbtclk1     -> %3d MHz' % (clkcnt[14]*125.0/clkcnt[0])
print '[info]: clk |pcie_clk           -> %3d MHz' % (clkcnt[15]*125.0/clkcnt[0])
print '[info]: clk |fmc_l8_clk0        -> %3d MHz' % (clkcnt[16]*125.0/clkcnt[0])
print '[info]: clk |fmc_l8_clk1        -> %3d MHz' % (clkcnt[17]*125.0/clkcnt[0])
print '[info]: clk |fmc_l12_clk0       -> %3d MHz' % (clkcnt[18]*125.0/clkcnt[0])
print '[info]: clk |fmc_l12_clk1       -> %3d MHz' % (clkcnt[19]*125.0/clkcnt[0])
print '[info]: clk |fabric_clk(tclka)  -> %3d MHz' % (clkcnt[20]*125.0/clkcnt[0])
print '[info]: clk |-------------------------------'

#######################
# basic test
#######################
clk_status = fc7.read("user_ipb_stat_regs",4)
if debug==1: print "[info]: clk |clk_status         -> %05x" % clk_status

clk_mask = 0xfbfe0 # ignore the pcie_clk
if debug==1: print "[info]: clk |clk_mask           -> %05x" % clk_mask     

err=0

clk_masked = clk_status & clk_mask
if (clk_masked!=0x000fbfe0): err=1

###########
# VERDICT
###########
if (err==1):
	print "[TEST]: clk |usr clk testing    -> /FAIL/"
else:
	print "[TEST]: clk |usr clk testing    -> /PASS/"	

