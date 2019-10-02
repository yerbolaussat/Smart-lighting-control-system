"""
File name: sensing_module.py
Author: Yerbol Aussat
Python Version: 2.7

PortableSensingModule class initializes connection with a portable sensing module, and defines methods for
communication with it.
"""


class PortableSensingModule:
	def __init__(self, client):
		# IPV-4 address, TCP-oriented socket.
		self.client = client
		
	# Send a message msg to the sensing module.
	def send_msg(self, msg):
		self.client.send(msg)
		return self.client.recv(1024)
	
	# Disconnect from the sensing module.
	def disconnect(self):
		self.send_msg("disconnect")
