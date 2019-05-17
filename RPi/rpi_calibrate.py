"""
	File name: rpi_calibrate_and_start.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that initializes and calibrates the system (extracts matrix A)
"""
from sensing_module import SensingModule
from office_sensing import OfficeSensing
from ceiling_actuation import CeilingActuation
import numpy as np
from pandas import DataFrame

def calibrate(actuators, sensors, step=0.35, B=0.65, wait_time = 2, type = "Calibration"):
	print "*" * 40, "\n", type
	
	if type == "Initial Calibration":
		# Start with setting all bulbs to dimming level of 0.8
		print "INITIAL CALIBRATION"
		dim_calibr = [0.8]*8
		actuators.set_dimming(dim_calibr, wait_time)

	# Initial light sensor readings (for all bulbs at dimming of 0.8)
	R, _ = sensors.get_sensor_readings()
	n_modules = len(R)
	
	print "\nR:", R
	
	# Get current dimming levels on bulbs
	dim_levels = actuators.get_dim_levels()
	if not dim_levels: return
		
	# Initialize A as 8x4 matrix
	A = [[None for _ in range(n_modules)] for _ in range(8)] 	

	# Apply calibration routine to each bulb j one by one
	for j in range(8):
		print "\n", "-"*20, "\nBULB:", j
		# Compare dimming level with the pivot
		S = step if dim_levels[j] > B else -step
		actuators.change_dim_on_bulb(j, -S, wait_time)		
		R_prime, _ = sensors.get_sensor_readings()
		print "R_prime:", R_prime
		A[j] = [abs(R_prime[i] - R[i]) / step for i in range(n_modules)]
		actuators.change_dim_on_bulb(j, S, wait_time)
	
	# Update matrices A and E
	A = np.matrix(map(list,zip(*A)))
	d = np.array(dim_levels)
	R = np.array(R)
	E = R - A.dot(d)
	np.save('illum_gain.npy', A)
	np.save('env_gain.npy', E[0])

	print '-'*38
	print "Illuminance Contributon Matrix:"
	print DataFrame(A)
	print "\nVector E (Environment contribution):\n", E
	print "Calibration is completed\n", "*" * 40

addresses = [("192.168.50.188", 1234), # Omega-F13D
			("192.168.50.179", 1234),  # Omega-F075   
			("192.168.50.158", 1234),  # Omega-F11F
			("192.168.50.168", 1234)]  # Omega-F129
			
light_callibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]

# Initialize actuators and sensors
# addresses = [("192.168.50.168", 1234)]  # Omega-F129
# light_callibration_const = [0.513906092956]
phue_bridge_ip_address = '192.168.0.3'
actuators = CeilingActuation(phue_bridge_ip_address)
sensors = OfficeSensing(addresses, light_callibration_const)

# Calibrate
try:
	calibrate(actuators, sensors, step=0.35, B=0.65, wait_time = 2, type = "Initial Calibration")
except Exception, e: # Stop sensing modules if there is an error
	sensors.stop_sens_modules()
	print "Error Message:\n", str(e)
	traceback.print_exc()
except KeyboardInterrupt:
	print "\nScript Interrupted"
	sensors.stop_sens_modules()
sensors.stop_sens_modules()