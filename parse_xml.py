from FC7.sw.pychips.src.AddressTableItem import AddressTableItem
import xml.etree.ElementTree as ET
mytree = ET.parse('./d19cScripts/uDTC_OT_address_table_v2.xml')
myroot = mytree.getroot()

for child in myroot:
    print(child.tag, child.attrib)

myroot.findall(".//node/[@id='command_fifo']")

def getNode(self, path = False):
    path_list = path.split(".")
    xpath = "./"
    for node_id in path_list:
        xpath = f"{xpath}/node[@id='{node_id}']"
    return xpath

def all_kids(root):
    for elem in root:
        all_descendants = [e.tag.split('}', 1)[1] for e in elem.iter()]
        print(all_descendants)

def extract(root, reg_name= "", reg_addr = 0, reg_mask = 0, reg_rw = ""):
    kids = root.findall("./node")
    if kids:
        for elem in kids:
            reg_name = f"{reg_name}.{elem.attrib['id']}"
            reg_addr = reg_addr + elem['address']
            if elem.attrib['mask']: reg_mask = reg_mask + elem.attrib['mask']
            reg_rw = elem.attrib["rw"]
            extract(elem, reg_name, reg_addr, reg_mask, reg_rw)
    else:
        if reg_rw == "rw":
            reg_read = 1
            reg_write = 1
        elif reg_rw == "r":
            reg_read = 1
            reg_write = 0
        elif reg_rw == "w":
            reg_read = 0
            reg_write = 1
        item = AddressTableItem(reg_name, reg_addr, reg_mask, reg_read, reg_write)
        self.items[reg_name] = item.additem(reg_name, item)
    
kids = myroot.findall("./node")
for elem in kids:
    print (elem.attrib)

def getNode(self, path = False):
    path_list = path.split(".")
    xpath = "./"
    for node_id in path_list:
        xpath = f"{xpath}/node[@id='{node_id}']"
    self.find
    return xpath
def additem(self, reg_name, item):
    self.items[reg_name] = item
    
def extract(self, root, reg_name= ".", reg_addr = 0, reg_mask = 0, reg_rw = ""):
    kids = root.findall("./node")
    if kids:
        for elem in kids:
            reg_name = f"{reg_name}.{elem.attrib['id']}"
            if "address" in elem.attrib:   
                reg_addr = reg_addr + int(elem.attrib['address'], 16)
            if "mask" in elem.attrib: 
                reg_mask = reg_mask + elem.attrib['mask']
            if "permission" in elem.attrib:
                reg_rw = elem.attrib["permission"]
            import pdb; pdb.set_trace()
            self.extract(root=elem, reg_name = reg_name, reg_addr = reg_addr, reg_mask = reg_mask, reg_rw = reg_rw)
    else:
        if reg_rw == "rw":
            reg_read = 1
            reg_write = 1
        elif reg_rw == "r":
            reg_read = 1
            reg_write = 0
        elif reg_rw == "w":
            reg_read = 0
            reg_write = 1
        print (f"{reg_name} {reg_addr} {reg_mask} {reg_rw}")
        #item = AddressTableItem(reg_name, reg_addr, reg_mask, reg_read, reg_write)
        #self.items[reg_name] = item