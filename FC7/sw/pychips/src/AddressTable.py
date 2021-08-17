'''
@author: Robert Frazier

May 2010
'''


# Project imports
from pdb import set_trace
from AddressTableItem import AddressTableItem
from CommonTools import uInt32Compatible
from ChipsException import ChipsException



from FC7.sw.pychips.src.AddressTableItem import AddressTableItem
import xml.etree.ElementTree as ET
import numpy as np
from functools import reduce

class AddressTable(object):
    '''Address table class to hold address table items and read in address tables from file

    The format is very simple.  Each line should contain a register name,
    a 32-bit (hex) register address, and a 32-bit (hex) register mask, in
    that order.  Any further words/values on that line are then ignored.
    Empty lines or lines starting with a "*" character are also ignored.
    Note that the IPbus protocol, and hence PyChips assumes 32-bit word
    addressing, allowing up to 2^34 bytes to be addressed.  I.e. each
    address points to a 32-bit word.
    
    An example is as follows:
    
    * RegName              RegAddr      RegMask      R     W     Description
    *---------------------------------------------------------------------------------------------
    someRegister           00000001     ffffffff     1     0     Any text you like here
    anotherRegister_low    0000000f     0000ffff     1     1     Bottom 16 bits for one purpose
    anotherRegister_high   0000000f     ffff0000     1     1     Top 16 bits for another purpose.
    *---------------------------------------------------------------------------------------------
    '''

    def __init__(self, addressTableFile):
        object.__init__(self)
        self.items = {}
        self.fileName = addressTableFile
        self._readAddrTable(addressTableFile)
        self.mytree = ET.parse('./d19cScripts/uDTC_OT_address_table_v2.xml')
        self.myroot = self.mytree.getroot()
        self.read_addr_table_xml(self.myroot)


    def getItem(self, registerName):
        """Returns the AddressTableItem object that corresponds to a particular register name."""
        if self.checkItem(registerName):
            return self.items[registerName]
        else:
            raise ChipsException("Register '" + registerName + "' does not exist in the address table file '" + self.fileName + "'!")


    def checkItem(self, registerName):
        """Returns True if registerName is present in the address table; returns False if it's not."""
        if registerName in self.items:
            return True
        return False


    def _readAddrTable(self, addressTableFile):
        '''Read in an address table from the specified file'''

        file = open(addressTableFile, 'r')
        line = file.readline() # Get the first line
        lineNum = 1

        while len(line) != 0:  # i.e. not the end of the file
            words = line.split()   # Split up the line into words by its whitespace
            if len(words) != 0:  # A blank line (or a line with just whitespace).
                if line[0] != '*':  # Not a commented line
                    if len(words) < 5:
                        raise ChipsException("Line " + str(lineNum) + " of file '" + addressTableFile + 
                                             "' does not conform to file format expectations!")
                    try:
                        regName = words[0]
                        regAddr = int(words[1], 16)
                        regMask = int(words[2], 16)
                        regRead = int(words[3])
                        regWrite= int(words[4])
                    except Exception as err:
                        raise ChipsException("Line " + str(lineNum) + " of file '" + addressTableFile + 
                                             "' does not conform to file format expectations! (Detail: " + str(err))
                    if regName in self.items:
                        raise ChipsException("Register '" + regName + "' is included in the file '"
                                             + addressTableFile + "' more than once!")
                    if not(uInt32Compatible(regAddr) and uInt32Compatible(regMask)):
                        raise ChipsException("Register address or mask on line " + str(lineNum) +
                                             " of file '" + addressTableFile + "' is not " \
                                             "a valid 32-bit unsigned number!")
                    if regMask == 0: raise ChipsException("Register mask on line " + str(lineNum) +
                                                          " of file '" + addressTableFile + 
                                                          "' is zero! This is not allowed!")
                    if regRead != 0 and regRead != 1:raise ChipsException("Read flag on line " +
                                                                          str(lineNum) + " of file '" +
                                                                          addressTableFile + "' is not one or zero!")
                    if regWrite != 0 and regWrite != 1: raise ChipsException("Write flag on line " +
                                                                             str(lineNum) + " of file '" +
                                                                             addressTableFile + "' is not one or zero!")

                    item = AddressTableItem(regName, regAddr, regMask, regRead, regWrite)
                    self.items[regName] = item
            line = file.readline()  # Get the next line and start again.
            lineNum += 1

    def get_Node(self, path = False):
        path_list = path.split(".")
        xpath = "./"
        for node_id in path_list:
            xpath = f"{xpath}/node[@id='{node_id}']"
        self.find
        return xpath

    def read_addr_table_xml(self, root, reg_name= [], reg_addr = [], reg_mask = [], reg_rw = []):

        for child in root.getchildren():

            reg_name.append(child.attrib["id"])
            if "address" in child.attrib:   
                reg_addr.append(int(child.attrib["address"],16))
            else: 
                reg_addr.append(0)
            if "mask" in child.attrib: 
                reg_mask.append(int(child.attrib["mask"],16))
            else: 
                reg_mask.append(0x0)
            if "permission" in child.attrib:
                reg_rw = child.attrib["permission"]

            # recursive depth first traversal of xml Elementree
            if child.getchildren(): 
                # if further children available
                self.read_addr_table_xml(root=child, reg_name = reg_name, reg_addr = reg_addr, reg_mask = reg_mask, reg_rw = reg_rw)

            reg_read = 0; reg_write = 0
            if reg_rw == "rw":
                reg_read = 1
                reg_write = 1
            elif reg_rw == "r":
                reg_read = 1
                reg_write = 0
            elif reg_rw == "w":
                reg_read = 0
                reg_write = 1

            # consolidate lists of accumaleted info of the register
            s = '.'
            reg_name_full = s.join(reg_name)
            reg_addr_full = reduce(lambda x, y: x | y, reg_addr)
            reg_mask_full = reduce(lambda x, y: x | y, reg_mask)

            if not reg_mask_full: reg_mask_full = 0xffffffff

            print (f"{reg_name_full} {hex(reg_addr_full)} {hex(reg_mask_full)} {reg_rw}")

            item = AddressTableItem(reg_name_full, reg_addr_full, reg_mask_full, reg_read, reg_write)
            self.items[reg_name_full] = item

            # remove last entry when going back up the Elementree
            if reg_name: reg_name.pop()
            if reg_mask: reg_mask.pop()
            if reg_addr: reg_addr.pop()