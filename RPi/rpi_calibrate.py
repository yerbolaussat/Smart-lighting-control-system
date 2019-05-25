"""
File name: rpi_calibrate_and_start.py
Author: Yerbol Aussat
Python Version: 2.7

Process that initializes and calibrates the system (extracts matrix A)
"""

from office_sensing import OfficeSensing
from ceiling_actuation import CeilingActuation
import numpy as np
from pandas import DataFrame


def calibrate(actuators, sensors, step=0.35, B=0.65, wait_time=2, initial_calibration=True):
	if initial_calibration:
		print "*" * 25, "\n", "Initial Calibration."
		# Start with setting all bulbs to dimming level of 0.8
		dim_calibr = [0.8]*8
		actuators.set_dimming(dim_calibr, wait_time)

	# Initial light sensor readings (for all bulbs at dimming of 0.8)
	R, _ = sensors.get_sensor_readings()
	print "\nR:", R
	n_modules = len(R)

	# Get current dimming levels on bulbs
	dim_levels = actuators.get_dim_levels()
	if not dim_levels: return
		
	# Apply calibration routine to each bulb j one by one
	A = np.zeros(shape=(4, 8))
	for j in range(8):
		print "\n", "-"*40, "\nBULB:", j
		# Compare dimming level with the pivot
		S = step if dim_levels[j] > B else -step
		actuators.change_dim_on_bulb(j, -S, wait_time)		
		R_prime, _ = sensors.get_sensor_readings()
		print " => R_prime:", R_prime
		A[:, j] = np.array([abs(R_prime[i] - R[i]) / step for i in range(n_modules)])
		actuators.change_dim_on_bulb(j, S, wait_time)

	# Update matrices A and E
	d = np.array(dim_levels)
	R = np.array(R)
	E = R - A.dot(d)
	np.save('illum_gain.npy', A)
	np.save('env_gain.npy', E)

	print '-'*38
	print "Illuminance Contributon Matrix:"
	print DataFrame(A)
	print "\nVector E (Environment contribution):\n", E
	print "Calibration is completed\n", "*" * 40


if __name__ == '__main__':
	addresses = [("192.168.50.188", 1234),  # Omega-F13D
	             ("192.168.50.179", 1234),  # Omega-F075
	             ("192.168.50.158", 1234),  # Omega-F11F
	             ("192.168.50.168", 1234)]  # Omega-F129
	light_calibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
	phue_bridge_ip_address = '192.168.0.3'
	ceiling_actuation = CeilingActuation(phue_bridge_ip_address)
	office_sensing = OfficeSensing(addresses, light_calibration_const)

	# Calibrate
	try:
		calibrate(ceiling_actuation, office_sensing, step=0.35, B=0.65, wait_time=2, initial_calibration=True)
	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()
	except Exception, e:  # Stop sensing modules if there is an error
		office_sensing.stop_sens_modules()
		print "Error Message:\n", str(e)
	office_sensing.stop_sens_modules()
