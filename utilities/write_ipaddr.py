from utilities import tbconfig

ipaddr = tbconfig.ETHERS[tbconfig.BOARD_SELECT]['IP']
f=open("./utilities/ipaddr.dat",'w')
f.write(ipaddr)