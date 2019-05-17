"""
	File name: rpi_sense.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Requests readings from Omega sensing modules.
	Updates occupancy and illuminance files every 0.1 seconds.
"""

# Import required modules
import numpy as np
import time
from datetime import datetime as dt
import subprocess
from multiprocessing.connection import Client
import traceback
from office_sensing import OfficeSensing
	
# Visualize illuminance on each sensor
def print_illuminance(R):
	print "\nIlluminance readings from light sensors:"
	print " ", "-"*15
	print "  |     LIGHT   |"
	print " ", "-"*15
	print "  | ", int(round(R[1])), " | ", int(round(R[3])), " |"
	print " ", "-"*15
	print "  | ", int(round(R[0])), " | ", int(round(R[2])), " |"
	print " ", "-"*15
	
# Visualize occupancy on each sensor
def print_occupancy(occupancy):
	print "\n  Occupancy matrix:"
	print "   ", "_"*11
	print "   ", "| {}  |  {} |".format(occupancy[1], occupancy[3])
	print "   ", "_"*11
	print "   ", "| {}  |  {} |".format(occupancy[0], occupancy[2])
	print "   ", "_"*11
	print "\n"

def sense(sensors):	
	# Connect to the optimizer process
	subprocess.call('python2 rpi_optimize.py &', shell=True)
	address_optimizer = ('localhost', 6000)
	conn = Client(address_optimizer, authkey='secret password')
	print "[*] Sensing process connected to optimizer"

	t1 = time.time()	
	try: 
		while True:
			# Get sensor readings
			R, occupancy = sensors.get_sensor_readings()			
			cur_illum_str = " ".join([str(R_val) for R_val in R])
			cur_occup_str = " ".join([str(occup_val) for occup_val in occupancy])
		
			t2 = time.time()
			if t2-t1>3:
				print "\n", "*" * 40
				t = dt.now()
				print t.hour, ":", t.minute, ":", t.second, ":", t.microsecond, "\n"
				print_illuminance(R)	
				print_occupancy(occupancy)
				t1 = t2
				
			# Update illuminance file:
			f_illum = open('cur_illum.txt', 'w+')
			f_illum.write(cur_illum_str)
			f_illum.close()			
			
			# Update occupancy file
			try:
				# If occupancy file already exists, compare current occupancy with the previous one
				f_occup = open('cur_occup.txt', 'r')
				prev_occup_str = f_occup.read()
				f_occup.close()
			
				if prev_occup_str == cur_occup_str:
					time.sleep(0.1)
				else:
					# Update occupancy 
					f_occup = open('cur_occup.txt', 'w+')
					f_occup.write(cur_occup_str)				
					f_occup.close()
					
					# Send "Optimize" command to optimizer
					conn.send('Optimize')
					print "\n", "#" * 50, "\n", "#" * 50
					print "\nOCCUPANCY CHANGES: START NEW OPTIMIZATION\n"
					t = dt.now()
					print t.hour, ":", t.minute, ":", t.second, ":", t.microsecond, "\n"
					print_occupancy(occupancy)
					print "#" * 50, "\n", "#" * 50, "\n"
			except IOError:
				# If occupancy file does not exist, create it, and start optimization process
				print "CREATE cur_occup.txt"
				f_occup = open('cur_occup.txt', 'w+')
				f_occup.write(cur_occup_str)	
				f_occup.close()
				conn.send('Optimize')
			
	except Exception, e: # Stop sensing modules if there is an error
		sensors.stop_sens_modules()
		print "Error Message:\n", str(e)
		traceback.print_exc()
		# Close connection with optimizer
		conn.send('Close')
		conn.close()
		subprocess.call('rm cur_occup.txt', shell=True)
	except KeyboardInterrupt:
		print "\nScript Interrupted"
		sensors.stop_sens_modules()
		# Close connection with optimizer
		conn.send('Close')
		conn.close()
		subprocess.call('rm cur_occup.txt', shell=True)

addresses = [("192.168.50.188", 1234), # Omega-F13D
			("192.168.50.179", 1234),  # Omega-F075   
			("192.168.50.158", 1234),  # Omega-F11F
			("192.168.50.168", 1234)]  # Omega-F129
			
light_callibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
sensors = OfficeSensing(addresses, light_callibration_const)
sense(sensors)