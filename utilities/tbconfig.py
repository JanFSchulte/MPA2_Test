VERSION = {}
ETHERS = {}
SSA_ADR = {}
MPA_ADR = {}

#############################################################################
# Dafault values. This section is overwritten by "start_ssa_*.sh"
VERSION['SSA'] = 2
VERSION['MPA'] = 1
VERSION['INT_PCB'] = 2
BOARD_SELECT = "08:00:30:00:22:5d"
VERSION['uDTC'] = "08.2019"
MPA_ADR[0] = 0b1000000
SSA_ADR[0] = 0b0100011
SSA_ADR[1] = 0b0100111


#############################################################################

ETHERS["08:00:30:00:22:5d"] = {'IP' : "192.168.1.81" , 'Description' : "fc7 board 2 labelled 151000094" }
ETHERS["08:00:30:00:23:05"] = {'IP' : "192.168.1.79" , 'Description' : "fc7 board 3 R2 labelled 154900006" }
ETHERS["08:00:30:00:22:f0"] = {'IP' : "192.168.1.81" , 'Description' : "fc7 board 2 R1 labelled 154000033" }
ETHERS["08:00:30:00:29:61"] = {'IP' : "192.168.0.8" , 'Description' : "fc7 at SiDet MaPSA probe station" }
ETHERS["08:00:30:00:29:8e"] = {'IP' : "192.168.1.7" , 'Description' : "fc7 at Purdue probe station" }
#ETHERS["08:00:30:00:28:1f"] = {'IP' : "192.168.0.9" , 'Description' : "Second fc7 at SiDet MaPSA probe station" }
