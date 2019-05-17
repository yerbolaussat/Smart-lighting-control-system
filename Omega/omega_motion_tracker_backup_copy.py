"""
	File name: omega_motion_tracker.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process on Omega Onion that continuously reads PIR sensor readings and updates motion_history file 
"""

import onionGpio
import time
import os
# from random import randint

# Initialize input GPIO at a given pin 
pin = 1
pir = onionGpio.OnionGpio(pin)
pir_status  = pir.setInputDirection()
print "[*] PIR sensor is initialized"

while True:
	occupancy_read = int(pir.getValue())	
# 	occupancy_read = randint(0, 1)
	
	try:
		# Read motion history
		f = open('motion_history.txt', 'r')
		motion_history = f.read()
		f.close()
		
		# Update and write motion history
		if len(motion_history) >= 10:
			motion_history = str(occupancy_read) + motion_history[:-1]
		else: 		
			motion_history = str(occupancy_read) + motion_history
			
		f = open('motion_history.txt', 'w+')
		f.write(motion_history)
		f.close()
		
	except IOError:
		print "[*] New file created"	
		f = open('motion_history.txt', 'w+')
		f.write(str(occupancy_read))
		f.close()		
	time.sleep(0.5)	