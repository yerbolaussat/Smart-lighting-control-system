"""
	File name: omega_responder.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that sends sensor readings (light and occupancy) to Raspberry Pi, whenever it requests them 
"""

# from random import randint
import time
import socket
from tsl2561 import TSL2561
 
tsl = TSL2561()
print "[*] Light sensor is initialized"

# Occupancy score: discounted sum of occupancy values (which are 1 or 0)
def get_occup_score(motions):
	score = 0
	alpha = 0.9
	for i in range(len(motions)):	
		score += motions[i] * alpha**i
	return score	

def get_occupancy_status():
	try:
		# Read motion history
		f = open('motion_history.txt', 'r')
		motion_history = f.read()
		f.close()
		motions = [int(motion) for motion in motion_history]
		occup_score = get_occup_score(motions)

		if len(motions) >= 10 and occup_score>=0.8:
			return 1
		elif len(motions) < 10 and occup_score>=1:
			return 1
		else:
			return 0
			
	except IOError:
		return 0	

def start_server():

	# Create a TCP socket object
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPV-4 address, TCP$
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows to reuse the address (ip and port)
	machine_name = socket.gethostname() # name of host computer
	
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = s.getsockname()[0]
	s.close()
	
	print "IP address of the Onion machine {}: {}".format(machine_name, ip)
	port = 1234
	address = (ip, port)
	server.bind(address)
	
	# Receive an incoming connection from a client
	server.listen(1)
	print "[*] Started listening on", ip, ":", port
	client, addr = server.accept()
	print "[*] Got a connection from", addr[0], ":", addr[1]
	

	# Responder's logic:
	while True:
		# Receive data from client
		data = client.recv(1024)
		
# 		data = "Read"
# 		time.sleep(2)
		
		print "\n[*] Received '",data,"' from the client"
		
		if data == "Check connection":
			client.send(str(machine_name) + " is Initialized")
			print "    Processing done.\n[*] Reply sent"
			
		elif data == "disconnect":
			client.send("Goodbye")
			print "[*] Client disconnected"
			client.close()
			server.close()
			print "[*] Restarting the server"
			start_server()
			break
			
		elif data == "Read":
			visible_light_read = tsl.read_value(TSL2561.Light.Visible)
			occupancy_read = get_occupancy_status()
			combined_string = '{} {}'.format(str(visible_light_read), str(occupancy_read))
			client.send(combined_string)
			print "    Light:", visible_light_read
			print "    Occupancy:", occupancy_read
			print "[*] Sensor readings sent to the client"
start_server()
	