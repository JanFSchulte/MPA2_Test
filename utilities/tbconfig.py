VERSION = {}
ETHERS = {}

#############################################################################
# This section is overwritten by "start_ssa_*.sh"
VERSION['SSA'] = 1
VERSION['MPA'] = 1
VERSION['INT_PCB'] = 2
BOARD_SELECT = "08:00:30:00:22:5d"
VERSION['uDTC'] = "08.2019"
#############################################################################

ETHERS["08:00:30:00:22:5d"] = {'IP' : "192.168.0.77" , 'Description' : "fc7 board 2" }
ETHERS["08:00:30:00:23:05"] = {'IP' : "192.168.0.79" , 'Description' : "fc7 board 3 R2 labelled 154900006" }
ETHERS["08:00:30:00:22:f0"] = {'IP' : "192.168.0.79" , 'Description' : "fc7 board 2 R1 labelled 154000033" }
