"""
	File name: omega_responder.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that sends sensor readings (light and occupancy) to Raspberry Pi, whenever it requests them 
"""

import time
import socket
import threading
from onionGpio import OnionGpio
from tsl2561 import TSL2561

motion_history_size = 500
tsl = TSL2561()
print "[*] Light sensor is initialized"
pin = 1
pir = OnionGpio(pin)
pir_status  = pir.setInputDirection()
print "[*] PIR sensor is initialized"

lock = threading.Lock()
motion_history = []

def update_motion_history():
	while True:
		# Read from PIR sensor:
		try:
			occupancy_reading = int(pir.getValue())	
		except Exception, e:
			print "Error Message:\n", str(e)
			continue
	
		# Update motion history:
		global motion_history
		with lock:
			if len(motion_history) >= motion_history_size:
				motion_history.pop()
			motion_history.insert(0, occupancy_reading)		
		time.sleep(0.15)

# Occupancy score: discounted sum of occupancy values (which are 1 or 0)
def get_occup_score(motion_history):
	score = 0
	alpha = 0.995
	for i, motion in enumerate(motion_history):	
		score += motion * alpha**i
	return score	

def get_occupancy_status():		
	global motion_history
	with lock:		
		occup_score = get_occup_score(motion_history)
		print "MOTION HISTORY: {}".format(motion_history)
		print "\nOCCUPANCY SCORE: {}\n".format(occup_score)

		if len(motion_history) >= motion_history_size and occup_score>=0.8:
			return 1
		elif len(motion_history) < motion_history_size and occup_score>=1:
			return 1
		else:
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
			visible_light_reading = tsl.read_value(TSL2561.Light.Visible)
			occupancy_reading = get_occupancy_status()
			combined_string = '{} {}'.format(str(visible_light_reading), str(occupancy_reading))
			client.send(combined_string)
			print "    Light:", visible_light_reading
			print "    Occupancy:", occupancy_reading
			print "[*] Sensor readings sent to the client"

thread = threading.Thread(target = update_motion_history)
thread.daemon = True
thread.start()
start_server()