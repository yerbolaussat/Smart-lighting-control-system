import socket

class SensingModule:
	def __init__(self, ip, port):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPV-4 address, TCP-oriented socket 
		self.ip = ip
		self.port = port
		self.client.connect((ip, port))
		
	# Send a message msg from client to the server
	def send_msg(self, msg):
		self.client.send(msg)
		return self.client.recv(1024)
	
	# Disconnect from the server	
	def disconnect(self):
		self.send_msg("disconnect")