"""
	File name: rpi_sense.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that requests readings from Omega sensing modules
"""

# Import required modules
import numpy as np
import time
import datetime as dt
from office_sensing import OfficeSensing

def sense(sensors):	
	try: 
		while True:
		
			# Get sensor readings
			R, occupancy = sensors.get_sensor_readings()
			cur_illum_str = " ".join([str(R_val) for R_val in R])
			cur_occup_str = " ".join([str(occup_val) for occup_val in occupancy])
		
			# Update illuminance file:
			f_illum = open('cur_illum.txt', 'w+')
			f_illum.write(cur_illum_str)
			f_illum.close()			
		
			# Update occupancy file
			try:
				f_occup = open('cur_occup.txt', 'r')
				prev_occup_str = f_occup.read()
				f_occup.close()
			
				if prev_occup_str == cur_occup_str:
					time.sleep(0.1)
				else:
	# 				subprocess.call('kill $(pgrep -f rpi_optimize.py)')
					f_occup = open('cur_occup.txt', 'w+')
					f_occup.write(cur_occup_str)				
					f_occup.close()
	# 				subprocess.call('python rpi_optimize.py &', shell=True)
				
					print "OCCUPANCY CHANGED"
		
			except IOError:
				f_occup = open('cur_occup.txt', 'w+')
				f_occup.write(cur_occup_str)				
	# 			subprocess.call('python rpi_optimize.py &', shell=True)
				f_occup.close()			
				print "OCCUPANCY FILE CREATED"
				
	except Exception, e: # Stop sensing modules if there is an error
		sensors.stop_sens_modules()
		print "Error Message:\n", str(e)
		traceback.print_exc()

	except KeyboardInterrupt:
		print "\nScript Interrupted"
		sensors.stop_sens_modules()
			
addresses = [("192.168.50.168", 1234)]  # Omega-F129
light_callibration_const = [0.513906092956]
sensors = OfficeSensing(addresses, light_callibration_const)
sense(sensors)