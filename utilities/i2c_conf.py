import json
import time
#from myScripts.BasicD19c import *
from myScripts.Utilities import *
from utilities.tbsettings import *
from ssa_methods.Configuration.ssa1_reg_map import *
from ssa_methods.Configuration.mpa_reg_map import * # Change location for register map file

class I2CConf:

    def __init__(self, fc7, fc7AddrTable, debug=False, index=0, address=0):
        self.fc7 = fc7
        self.chip_adr = index
        self.__load_reg_map(version=tbconfig.VERSION['SSA'])
        self.__set_parameters(debug=debug)
        #self.i2c_address = address
        self.fc7AddrTable = fc7AddrTable

    def __load_reg_map(self, version):
        if(self.chip_adr == "MPA"):
            self.peri_reg_map = mpa_peri_reg_map
            self.mpa_pixel_reg_map = mpa_pixel_reg_map
            self.mpa_row_reg_map = mpa_row_reg_map
            print('->  Loaded configuration for MPA')
        elif (version >= 2) and not (self.chip_adr == "MPA"):
            #from ssa_methods.Configuration.ssa2_reg_map import *
            ssa_reg_map = json.load(open('./ssa_methods/Configuration/ssa2_reg_map.json', 'r'))
            ssa_cal_map = json.load(open('./ssa_methods/Configuration/ssa2_cal_map.json', 'r'))
            self.ssa_strip_reg_map = ssa_reg_map['STRIP']
            self.peri_reg_map  = ssa_reg_map['PERIPHERY']
            self.analog_mux_map    = ssa_cal_map['PAD']
            self.analog_adc_map    = ssa_cal_map['ADC']
            print('->  Loaded configuration for SSA v2')
        else:
            self.ssa_strip_reg_map = ssa_strip_reg_map_v1
            self.peri_reg_map  = ssa_peri_reg_map_v1
            self.analog_mux_map    = analog_mux_map_v1
            print('->  Loaded configuration for SSA v1')

    def __set_parameters(self, debug=False):
        self.freq = 0
        self.debug = debug
        self.readback = False
        ##### for 2SSA
        self.delay = 0.0005
        self.mask_active = {'mask_strip':True, 'mask_peri_A':True, 'mask_peri_D':True, 'None':False}

    def get_strip_reg_map(self):
        return self.ssa_strip_reg_map

    def get_pixel_reg_map(self):
        return self.mpa_pixel_reg_map

    def get_row_reg_map(self):
        return self.mpa_pixel_reg_map

    def get_peri_reg_map(self):
        return self.peri_reg_map

    def get_analog_mux_map(self):
        return self.analog_mux_map

    def set_debug_mode(self, value = True, display = 0):
        self.debug = value
        if(display):
            if(value): utils.print_log("->  SSA Configuration debug mode Enabled")
            else: utils.print_log("->  SSA Configuration debug mode Disabled")

    def set_readback_mode(self, value = True, display = 0):
        self.readback = value
        if(display):
            if(value): utils.print_log("->  SSA Configuration Write-Read-Back mode Enabled")
            else: utils.print_log("->  SSA Configuration Write-Read-Back mode Disabled")

    def set_freq(self, value):
        self.freq = value
        return True

    def enable(self):
        utils.activate_I2C_chip(self.fc7)

    def get_freq(self, value):
        return self.freq

    def peri_write(self, register, data, field=False, use_onchip_mask = True):
        cnt = 0; st = True;
        while cnt < 4:
            try:
                cnt += 1
                data = data & 0xff
                time.sleep(self.delay)
                if(register not in self.peri_reg_map.keys()):
                    utils.print_error("'X>  I2C Periphery register name not found: key: {:s} ".format(register))
                    rep = 'Null'
                else:
                    if (tbconfig.VERSION['SSA'] >= 2) and not (self.chip_adr == 'MPA'):
                        reg_adr = self.tonumber(self.peri_reg_map[register]['adr'],0)
                        mask_name = self.peri_reg_map[register]['mask_reg']
                        mask_adr  = self.tonumber(self.peri_reg_map[mask_name]['adr'], 0)
                    elif(self.chip_adr == 'MPA'):
                        base = self.peri_reg_map[register]
                        #adr  = (base & 0x0fff) | 0b0001000000000000
                        reg_adr   = base
                    else:
                        base = self.peri_reg_map[register]
                        reg_adr  = (base & 0x0fff) | 0b0001000000000000
                        mask_name = 'None'
                    if(field):
                        if(tbconfig.VERSION['SSA']<2):
                            utils.utils.print_error('X>  I2C Strip {:3d} error. Field available only for SSA v2'.format(strip_id))
                            return 'Null'
                        ####################################
                        mask_val = self.tonumber(self.peri_reg_map[register]['fields_mask'][field], 0)
                        loc = self._get_field_location(mask_val)
                        tdata = (data << loc[0]) & 0xff & mask_val

                        if(use_onchip_mask): ### this is the procedure to use
                            self.mask_active[mask_name] = True
                            rep  = self.write_I2C(self.chip_adr, mask_adr, mask_val, self.freq)
                            rep  = self.write_I2C(self.chip_adr, reg_adr, tdata, self.freq)
                        else:
                            readreg  = self.read_I2C(self.chip_adr, reg_adr)
                            if(readreg != None):
                                wdata = (readreg & (~int(mask, 2))) | (tdata & int(mask, 2))
                                rep  = self.write_I2C(self.chip_adr, reg_adr, wdata, self.freq)
                            else:
                                utils.print_error('X>  I2C Periphery read  - Adr=[0x{:4x}], Value=[{:s}] - ERROR'.format(reg_adr, 'NOVALUE'))
                                st = 'Null'
                        ####################################
                        if(self.debug):
                            utils.print_log('->  I2C Periphery write - Adr=[0x{:4x}], Value=[{:d}]'.format(reg_adr, tdata))
                    else:
                        if not (self.chip_adr == 'MPA'):
                            if(self.mask_active[mask_name] and (tbconfig.VERSION['SSA']>=2)):
                                rep  = self.write_I2C(self.chip_adr, mask_adr, 0xff, self.freq)
                                self.mask_active[mask_name] = False
                        rep  = self.write_I2C(self.chip_adr, reg_adr, data, self.freq)
                        if(self.debug):
                            utils.print_log('->  I2C Periphery write - Adr=[0x{:4x}], Value=[{:d}]'.format(reg_adr, data))
                if(self.readback):
                    rep = self.peri_read(register)
                    if(rep != data):
                        utils.print_error("->  I2C periphery write - [%d][%d] - ERROR" % (data, rep))
                        st = 'Null'
                if(st):
                    break
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                utils.print_error('=>  TB Communication error - I2C-Peri_write')
                print(exc_type, fname, exc_tb.tb_lineno)
                time.sleep(0.1)
                st = 'Null'
        return st

    def peri_read(self, register, field=False):
        cnt = 0; rep = True;
        time.sleep(self.delay)
        while cnt < 4:
            try:
                cnt += 1
                if(register not in self.peri_reg_map.keys()):
                    utils.print_error("'X>  I2C Periphery register name not found: key: {:s} ".format(register))
                    rep = 'Null'
                else:
                    if(tbconfig.VERSION['SSA'] == 2) and not (self.chip_adr == 'MPA'):
                        adr = self.tonumber(self.peri_reg_map[register]['adr'], 0)
                    elif(self.chip_adr == 'MPA'):
                        base = self.peri_reg_map[register]
                        #adr  = (base & 0x0fff) | 0b0001000000000000
                        adr = base
                    else:
                        base = self.peri_reg_map[register]
                        adr  = (base & 0xfff) | 0b0001000000000000
                    repd = self.read_I2C(self.chip_adr, adr)
                    if(repd == None):
                        #utils.activate_I2C_chip(self.fc7)
                        #rep  = self.read_I2C(self.chip_adr, adr)
                        rep  = 'Null'
                        utils.print_error('X>  I2C Periphery read  - Adr=[0x{:4x}], Value=[{:s}] - ERROR'.format(adr, 'NOVALUE'))
                        #self.utils.activate_I2C_chip(self.fc7)
                    else:
                        if(field):
                            mask = int(self.peri_reg_map[register]['fields_mask'][field], 2)
                            loc  = self._get_field_location(mask)
                            rep  = ((repd & mask) >> loc[0])
                        else:
                            rep  = repd
                        if(self.debug):
                            utils.print_log('->  I2C Periphery read  - Adr=[0x{:4x}], Value=[{:b}] - GOOD'.format(adr, repd))
                break
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                utils.print_error('=>  TB Communication error - I2C-Peri_write')
                print(exc_type, fname, exc_tb.tb_lineno)
                time.sleep(0.1)
                st = 'Null'
        return rep

    def row_write(self, register, row, data):

        if register not in list(self.mpa_row_reg_map.keys()):
            print("Register name not found")
            rep = False

        else:
            pixel_id = 0b1111001
            base = mpa_row_reg_map[register]
            adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | pixel_id
            #print bin(adr)
            rep  = self.write_I2C('MPA', adr, data, self.freq)

    def row_read(self, register, row, timeout = 0.001):

        if register not in list(self.mpa_row_reg_map.keys()):
            print("Register name not found")
            rep = False

        else:
            pixel_id = 0b1111001
            base = mpa_row_reg_map[register]
            adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | pixel_id
            #print bin(adr)
            rep  = self.read_I2C('MPA', adr, timeout)
        return rep

    def pixel_write(self, register, row, pixel, data):

        if register not in list(self.mpa_pixel_reg_map.keys()):
            print("Register name not found")
            rep = False

        else:
            pixel_id = pixel if (pixel is not 'all') else 0b00000000
            base = mpa_pixel_reg_map[register]
            adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | (pixel_id & 0xfffffff)
            #print bin(adr)
            rep  = self.write_I2C('MPA', adr, data, self.freq)

        #return rep

    def pixel_read(self, register, row, pixel, timeout = 0.001):

        if register not in list(self.mpa_pixel_reg_map.keys()):
            print("Register name not found")
            rep = False

        else:
            pixel_id = pixel if (pixel is not 'all') else 0b00000000
            base = mpa_pixel_reg_map[register]
            adr  = ((row & 0x0001f) << 11 ) | ((base & 0x000f) << 7 ) | (pixel_id & 0xfffffff)
            #print bin(adr)
            rep  = self.read_I2C('MPA', adr, timeout)
            if rep == None:
                time.sleep(1)
                activate_I2C_chip()
                time.sleep(1)
                rep  = self.read_I2C('MPA', adr, timeout)

        return rep



    def strip_write(self, register, strip, data, field=False, use_onchip_mask = True):
        #example: ssa.i2c.strip_write('StripControl2',0, 0xff, 'HipCut')
        cnt = 0; st = True;
        V = tbconfig.VERSION['SSA']
        #while cnt < 4:
        #	try:
        cnt += 1
        if register not in self.ssa_strip_reg_map.keys():
            utils.print_error("'X>  I2C Strip register name not found")
            rep = 'Null'
        else:

            if(V>=2):
                if(isinstance(strip, str)):
                    if(strip != 'all'):
                        utils.print_error('->  Requested to write on strip ID {:s} is invalid. Valid range 1:120 or "all" '.format(strip))
                        return 'Null'
                elif(strip<1 or strip>120):
                    utils.print_error('->  Requested to write on strip ID {:d} is invalid. Valid range 1:120 or "all" '.format(strip))
                    return 'Null'
                strip_id = strip-1 if (strip is not 'all') else 0x7f
            else:
                strip_id = strip   if (strip is not 'all') else 0x00

            if(V>=2): base = self.tonumber(self.ssa_strip_reg_map[register]['adr'],0)
            else:     base = self.tonumber(self.ssa_strip_reg_map[register],0)

            reg_adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111)

            if(V>=2): strip_id+=1 # for print purposes only

            if(field):
                if(V<2):
                    utils.print_error('X>  I2C Strip {:3d} error. Field available only for SSA v2'.format(strip_id))
                    return 'Null'
                ####################################
                mask_val = self.tonumber(self.ssa_strip_reg_map[register]['fields_mask'][field],0)
                loc  = self._get_field_location(mask_val)
                tdata = (data << loc[0]) & 0xff & mask_val

                if(use_onchip_mask):  ### this is the procedure to use
                    self.mask_active['mask_strip'] = True
                    mask_adr = self.tonumber(self.peri_reg_map['mask_strip']['adr'],0)
                    rep  = self.write_I2C(self.chip_adr, mask_adr, mask_val, self.freq)
                    rep  = self.write_I2C(self.chip_adr, reg_adr, tdata, self.freq)
                else:
                    if(strip=='all'): readreg  = self.read_I2C(self.chip_adr, 1)
                    else: readreg  = self.read_I2C(self.chip_adr, reg_adr)
                    if(readreg != None):
                        wdata = (readreg & (~int(mask, 2))) | (tdata & int(mask, 2))
                        rep  = self.write_I2C(self.chip_adr, reg_adr, wdata, self.freq)
                    else:
                        utils.print_error('X>  I2C Strip {:3d} read  -  Adr=[0x{:4x}], Value=[{:s}] - ERROR'.format(strip_id, reg_adr, 'NOVALUE'))
                        st = 'Null';

                if(self.debug):
                    utils.print_log('->  I2C Strip {:3d} write - Adr=[0x{:4x}], Value=[{:d}]'.format(strip_id, reg_adr, tdata))
            else:
                if(self.mask_active['mask_strip'] and (tbconfig.VERSION['SSA']>=2) ):
                    mask_adr  = self.tonumber(self.peri_reg_map['mask_strip']['adr'], 0)
                    rep  = self.write_I2C(self.chip_adr, mask_adr, 0xff, self.freq)
                    self.mask_active['mask_strip'] = False
                wdata = data
                rep  = self.write_I2C(self.chip_adr, reg_adr, wdata, self.freq)
                if(self.debug):
                    utils.print_log('->  I2C Strip {:3d} write - Adr=[0x{:4x}], Value=[{:d}]'.format(strip_id, reg_adr, wdata))
        if(self.readback):
            tmp = strip_id if (strip_id != 0) else 50
            rep = self.strip_read(register, tmp)
            if(rep != data):
                utils.print_error("->  I2C Strip {:3d} write - [{:d}][{:d}] - ERROR".format(strip_id, data, rep))
                st = 'Null'
        #		if(st):
        #			break
        #	except:
        #		print('=>  TB Communication error - I2C-Strip_write' + str(cnt))
        #		time.sleep(0.1)
        #		st = 'Null'
        return st

    def strip_read(self, register, strip, field=False):
        cnt = 0; rep = True;
        V = tbconfig.VERSION['SSA']
        cnt += 1
        if register not in self.ssa_strip_reg_map.keys():
            utils.print_error("'X>  I2C Strip register name not found")
            rep = 'Null'
        else:
            if(V >= 2):
                if(isinstance(strip, str)):
                    if(strip != 'all'):
                        utils.print_error('->  Requested to read from strip ID {:s} is invalid. Valid range 1:120 or "all" '.format(strip))
                        return 'Null'
                elif(strip<1 or strip>120):
                    utils.print_error('->  Requested to read from strip ID {:d} is invalid. Valid range 1:120 or "all" '.format(strip))
                    return 'Null'
                strip_id = strip-1 if (strip is not 'all') else 0x7f
                base = self.tonumber(self.ssa_strip_reg_map[register]['adr'],0)
                isreadonly = (self.ssa_strip_reg_map[register]['permissions'] == 'R')
                adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111) | isreadonly<<7
                #print(isreadonly)
            else:
                strip_id = strip if (strip is not 'all') else 0x00
                base = self.tonumber(self.ssa_strip_reg_map[register],0)
                adr  = ((base & 0x000f) << 8 ) | (strip_id & 0b01111111)
            repd = self.read_I2C(self.chip_adr, adr)
            if(V>=2): strip_id+=1 # for print purposes only
            if(repd == None):
                rep  = 'Null'
                utils.print_error('X>  I2C Strip {:3d} read  -  Adr=[{:s}][0x{:x}], Value=[{:s}] - ERROR'.format(strip_id, register, adr, 'NOVALUE'))
            else:
                if(field):
                    mask = int(self.ssa_strip_reg_map[register]['fields_mask'][field], 2)
                    loc  = self._get_field_location(mask)
                    rep  = ((repd & mask) >> loc[0])
                else:
                    rep  = repd
                if(self.debug):
                    utils.print_log("->  I2C Strip {:3d} read  - [0x{:x}] - GOOD".format(strip_id, rep))
            #			break
            #except:
            #	print('=>  TB Communication error - I2C-Strip-read')
            #	time.sleep(0.1)
            #	rep = 'Null'
        return rep

    # Using FC7 class in SSA methods to handle typical IP bus communication losses (firmware issue)
    def write_I2C (self, chip, address, data, frequency = 0):
        read = 1; write = 0; readback = 0
        if  (chip == 'MPA'):  self.SendCommand_I2C(0, 0, 0, 0, write, address, data, readback)
        elif(chip == 'SSA'):  self.SendCommand_I2C(0, 0, 1, 0, write, address, data, readback)
        elif(chip == 'SSA0'): self.SendCommand_I2C(0, 0, 1, 0, write, address, data, readback)
        elif(chip == 'SSA1'): self.SendCommand_I2C(0, 0, 2, 0, write, address, data, readback)
        else: utils.print_error('ERROR I2C Chip Name ' + str(chip))


    def read_I2C (self, chip, address):
        read = 1; write = 0; readback = 0
        data = 0
        tinit=time.time()
        if   (chip == 'MPA'):  self.SendCommand_I2C(0, 0, 0, 0, read, address, data, readback)
        elif (chip == 'SSA'):  self.SendCommand_I2C(0, 0, 1, 0, read, address, data, readback)
        elif (chip == 'SSA0'): self.SendCommand_I2C(0, 0, 1, 0, read, address, data, readback)
        elif (chip == 'SSA1'): self.SendCommand_I2C(0, 0, 2, 0, read, address, data, readback)
        else: utils.print_error('ERROR I2C Chip Name ' + str(chip))
        time.sleep(self.delay)
        read_data = self.fc7.ReadChipDataNEW()
        return read_data

    def SendCommand_I2C(self, command, hybrid_id, chip_id, page, read, register_address, data, ReadBack):
        """
        #new addresstable
        raw_command   = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.command_type").shiftDataToMask(command)
        raw_word0     = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word_id").shiftDataToMask(0)
        raw_word1     = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word_id").shiftDataToMask(1)
        raw_hybrid_id = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_board_id").shiftDataToMask(hybrid_id)
        raw_chip_id   = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_slave_id").shiftDataToMask(chip_id)
        raw_readback  = 0
        raw_page      = 0
        # raw_readback  = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_readback").shiftDataToMask(ReadBack)
        # raw_page      = self.fc7AddrTable.getItem("ctrl_command_i2c_command_page").shiftDataToMask(page)
        raw_read      = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_read").shiftDataToMask(read)
        raw_register  = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word0_register").shiftDataToMask(register_address)
        raw_data      = self.fc7AddrTable.getItem("fc7_daq_ctrl.command_processor_block.i2c.mpa_ssa_i2c_command.word1_data").shiftDataToMask(data)
        """

        
        #old bit mapping
        raw_command   = self.fc7AddrTable.getItem("ctrl_command_i2c_command_type").shiftDataToMask(command)
        raw_word0     = self.fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(0)
        raw_word1     = self.fc7AddrTable.getItem("ctrl_command_i2c_command_word_id").shiftDataToMask(1)
        raw_hybrid_id = self.fc7AddrTable.getItem("ctrl_command_i2c_command_hybrid_id").shiftDataToMask(hybrid_id)
        raw_chip_id   = self.fc7AddrTable.getItem("ctrl_command_i2c_command_chip_id").shiftDataToMask(chip_id)
        raw_readback  = self.fc7AddrTable.getItem("ctrl_command_i2c_command_readback").shiftDataToMask(ReadBack)
        raw_page      = self.fc7AddrTable.getItem("ctrl_command_i2c_command_page").shiftDataToMask(page)
        raw_read      = self.fc7AddrTable.getItem("ctrl_command_i2c_command_read").shiftDataToMask(read)
        raw_register  = self.fc7AddrTable.getItem("ctrl_command_i2c_command_register").shiftDataToMask(register_address)
        raw_data      = self.fc7AddrTable.getItem("ctrl_command_i2c_command_data").shiftDataToMask(data)
        
        """
        #d19-software manual shifting
        raw_readback  = 0
        raw_page      = 0
        raw_command    = command << 31
        raw_word0       = 0
        raw_chip_id        = chip_id << 21
        raw_hybrid_id        = hybrid_id << 20
        raw_read            = read << 16
        raw_register = register_address

        raw_word1  = 1<<27
        raw_data       = data
        """
        cmd0          = raw_command + raw_word0 + raw_hybrid_id + raw_chip_id + raw_readback + raw_read + raw_page + raw_register;
        cmd1          = raw_command + raw_word1 + raw_data
        description   = "Command: type = " + str(command) + ", hybrid = " + str(hybrid_id) + ", chip = " + str(chip_id)
        #print(hex(cmd))
        if(read == 1):
            self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", cmd0)
        else:
            self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", cmd0)
            #time.sleep(0.01)
            self.fc7.write("fc7_daq_ctrl.command_processor_block.i2c.command_fifo", cmd1)
        return description

    def _get_field_location(self, mask):
        if(isinstance(mask, int)):   maskd = bin(mask)
        elif(isinstance(mask, str)): maskd = mask
        else: return [-1, -1]
        bitarray = [int(i) for i in np.binary_repr(int(maskd, 2), 8)]
        bitarray.reverse()
        oneloc = np.nonzero(np.array(bitarray) == 1)[0]
        if(len(oneloc)>0): rval = [oneloc[0], oneloc[-1]]
        else: rval = [-1, -1]
        return rval

    def tonumber(self, value, base):
        if(isinstance(value, str)):
            return int(value, base)
        else:
            return value
