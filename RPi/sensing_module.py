"""
File name: sensing_module.py
Author: Yerbol Aussat
Python Version: 2.7

SensingModule class initializes connection with a sensing module, and defines methods for communication with it.
"""

import socket


class SensingModule:
	def __init__(self, ip, port):
		# IPV-4 address, TCP-oriented socket.
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ip = ip
		self.port = port
		self.client.connect((ip, port))
		
	# Send a message msg to the sensing module.
	def send_msg(self, msg):
		self.client.send(msg)
		return self.client.recv(1024)
	
	# Disconnect from the sensing module.
	def disconnect(self):
		self.send_msg("disconnect")
