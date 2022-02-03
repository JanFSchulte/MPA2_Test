# Project imports

class ErrorHandler(object):

    def __init__(self):
        object.__init__(self)

    def getErrorDescription(self, block_id, error_code):
        if (block_id == 0 and error_code == 0):
            print "No Errors"
            return
        block_name = self.getBlockName(block_id)
        if block_id == 1:
            if hex(error_code) == "0x11L":
                message = "Unknown Command"
            elif hex(error_code) == "0x1eL":
                message = "Case Statement Exception"
            elif hex(error_code) == "0x1fL":
                message = "Command Processor has wrong FSM State"
            elif hex(error_code) == "0x41L":
                message = "Wrong Fast Command"
            elif hex(error_code) == "0x21L":
                message = "CMD_I2C: Wrong Command"
            elif hex(error_code) == "0x22L":
                message = "CMD_I2C: Status Changed During the Execution"
            elif hex(error_code) == "0x23L":
                message = "CMD_I2C: Wrong Hybrid/Chip ID"
	    elif hex(error_code) == "0x24L":
                message = "CMD_I2C: Reading or requiring readback is not permitted for broadcast I2C commands"
            elif hex(error_code) == "0x2fL":
                message = "CMD_I2C: FSM in a wrong state"
            elif  hex(error_code) == "0x3aL":
                message = "PHY_I2C: " + str(error_code) + " unknown register"
            elif hex(error_code) == "0x3bL":
                message = "PHY_I2C: " + str(error_code) + " i2c failed during the reading of the page"
            elif hex(error_code) == "0x3cL":
                message = "PHY_I2C: " + str(error_code) + " i2c failed during the reading the requested register"
	    elif hex(error_code) == "0x3dL":
                message = "PHY_I2C: " + str(error_code) + " i2c failed during write to page register"
	    elif hex(error_code) == "0x3eL":
                message = "PHY_I2C: " + str(error_code) + " writing/reading to/from requested register failed" 
	    else:
                message = "Unknown Code: " + str(hex(error_code))
        elif block_id == 2:
            if hex(error_code) == "0x1L":
                message = "Unknown Mode"
            elif hex(error_code) == "0x2L":
                message = "Unknown Source"
            elif hex(error_code) == "0x3L":
                message = "No triggers, check the clock please"
            else:
                message = "Unknown Code: " + str(hex(error_code))
        else:
            message = "Unknown Block & Code: " + str(hex(error_code))
        print "ERROR BLOCK: ", block_name, ", MESSAGE: ", message
        return

    def getBlockName(self, block_id):
        if block_id == 1:
            return "Command Processor Block"
        elif block_id == 2:
            return "Fast Command Block"
        elif block_id == 3:
            return "PHY Interface Block"
        else:
            return str(block_id)
