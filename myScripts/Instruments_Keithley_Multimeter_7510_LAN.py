import socket
import time
import numpy as np

class Instruments_Keithley_Multimeter_7510_LAN:

	def __init__(self, name='Multimeter', IP='192.168.0.90', PORT=5025):
		self.available = False
		self.connect(IP, PORT, name)
		self.nsamples = 10
		self.nplc_filter = False

	def connect(self, IP, PORT=5025, name=''):
		self.s = socket.socket()
		self.s.settimeout(0.1)
		if self.s.connect_ex((IP, PORT)):
			print('->  Impossible to establish the connection with {:s} on address {:s}'.format( str(name), (IP+':'+str(PORT))))
			self.available = False
		else:
			print('->  Communication established with {:s} on address {:s}'.format( str(name), (IP+':'+str(PORT))))
			self.available = True
			#self.s.send("*CLS;*RST\n")
			self.s.settimeout(10)

	def _isavailable(self):
		if not self.available:
			print('-x  Impossible to communicate with Keitley-2410, check the local network.')
		return self.available

	def send(self, cmd):
		if(not self._isavailable()): return False
		else: return self.s.sendall(str.encode(cmd + '\n') )

	def sendall(self, cmd):
		if(not self._isavailable()): return False
		else: return self.s.sendall(cmd)

	def receive(self):
		if(not self._isavailable()): return False
		else: return self.s.recv(256)

	def reset(self):
		self.send('*RST')

	def configure_dc_high_accuracy(self, nplc_filter=False, nsamples=10):
		if((nsamples != self.nsamples) or (nplc_filter != self.nplc_filter)):
			self.nsamples = nsamples
			self.nplc_filter = nplc_filter
			self.send('*RST')
			self.send(':SENS:FUNC "VOLT:DC"')
			self.send(':SENS:VOLT:RANG 1')
			self.send(':SENS:VOLT:INP AUTO')
			self.send(':SENS:VOLT:NPLC {:d}'.format(10 if nplc_filter else 1))
			self.send(':SENS:VOLT:AZER ON')
			self.send(':SENS:VOLT:AVER:TCON REP')
			self.send(':SENS:VOLT:AVER:COUN {:d}'.format(nsamples))
			self.send(':SENS:VOLT:AVER ON')
			print('->  Multimeter configured for high accuracy, nplc_filter {:s}, {:d} averages'.format('ON' if nplc_filter else 'OFF' , nsamples))

	def configure_measure_resistence(self):
		self.send('*RST')
		self.send(':SENS:FUNC "FRES"')
		self.send(':SENS:FRES:OCOM ON')
		self.send(':SENS:FRES:AZER ON')
		self.send(':SENS:FRES:NPLC 1')

	def measure(self):
		self.send(':READ?')
		rep = np.float( self.receive() )
		return rep

#self = multimeter_lan

'''
import socket
s = socket.socket()
s.settimeout(1)
IP='192.168.0.90'
PORT=5025
s.connect((IP, PORT))
s.sendall( str.encode(':READ?' + '\n') )
s.recv(256)
'''



# import socket
# import sys
# from _thread import *
#
# host = ""
# port = 5025
# s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#
# try:
#     s.bind((host,port))
# except socket.error as e:
#     print(str(e))
#
# s.listen(5) #Enable a server to accept connections.
# print("Waiting for a connection...")
#
# def threaded_client(conn):
#     conn.send(str.encode("Welcome\n"))
#     while True:
#     # for m in range (0,20): #Disconnects after x chars
#         data = conn.recv(2048) #Receive data from the socket.
#         reply = "Server output: "+ data.decode("utf-8")
#         print(data)
#         if not data:
#             break
#         conn.sendall(str.encode(reply))
#     conn.close()
#
# while True:
#     conn, addr = s.accept()
#     print("connected to: "+addr[0]+":"+str(addr[1]))
#     start_new_thread(threaded_client,(conn,))
