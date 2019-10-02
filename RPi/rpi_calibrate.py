"""
File name: rpi_calibrate_and_start.py
Author: Yerbol Aussat
Python Version: 2.7

Process that initializes and calibrates the system (extracts illuminance gains matrix A).

Note:
- IP addresses, port numbers and calibration constants of "per-desk" sensing modules should be specified in the
SENS_MODULE_CONFIG_FILE_NAME file.
- IP adress of the Philips Hue bridge should be specified in PHUE_IP_ADDRESS.
"""

from office_sensing import OfficeSensing
from ceiling_actuation import CeilingActuation
import numpy as np
from pandas import DataFrame
import argparse
import time

# Constants
SENS_MODULE_CONFIG_FILE_NAME = 'sensing_module_list.txt'
PHUE_IP_ADDRESS = '192.168.0.2'
ILLUM_GAIN_MTX_FILE_NAME = 'illum_gain.npy'  # File name where illuminance gains matrix is stored persistently.
ENV_GAIN_FILE_NAME = 'env_gain.npy'  # File name where environmental illuminance gains are stored persistently.


# Calibration process.
def calibrate(sensors, actuators=None, step=0.35, B=0.65, wait_time=2, initial_calibration=False):
	if not actuators:
		actuators = CeilingActuation(PHUE_IP_ADDRESS)
	n_sensors = len(sensors.sens_modules)

	# NOTE: "8" is hardcoded below, which means that the system supports at most 8 bulbs. This was done because if
	# other Philips Hue bulbs (not belonging to the system) were connected to the bridge at the moment of
	# calibration, they were integrated into the system too (which is undesired). Fixing this should ne added to TODO.
	n_bulbs = min(8, len(actuators.lights))
	calibtation_start = time.time()
	if initial_calibration:
		print "*" * 25, "\n", "Initial Calibration."
		# Start with setting all bulbs to dimming level of 0.8.
		dim_calibr = [0.8] * n_bulbs
		actuators.set_dimming(dim_calibr, wait_time)
	else:
		print "*" * 25, "\n", "Calibration."

	# Initial light sensor readings (for all bulbs at dimming of 0.8).
	R, _ = sensors.get_sensor_readings()
	print "\nR:", R

	# Get current dimming levels on bulbs.
	dim_levels = actuators.get_dim_levels()
	if not dim_levels:
		return
		
	# Apply calibration routine to each bulb j one by one.
	A = np.zeros(shape=(n_sensors, n_bulbs))
	for j in range(n_bulbs):
		print "\n", "-"*40, "\nBULB:", j
		# Compare dimming level with the pivot
		S = step if dim_levels[j] > B else -step
		actuators.change_dim_on_bulb(j, -S, wait_time)		
		R_prime, _ = sensors.get_sensor_readings()
		print " => R_prime:", R_prime
		A[:, j] = np.array([abs(R_prime[i] - R[i]) / step for i in range(n_sensors)])
		actuators.change_dim_on_bulb(j, S, 0)  # Wait time here is 0 since we don't measure illuminance after this step.
	time.sleep(wait_time)

	# Update matrices A and E
	d = np.array(dim_levels)
	R = np.array(R)
	E = R - A.dot(d)
	if not initial_calibration:
		A_prev = np.load(ILLUM_GAIN_MTX_FILE_NAME)
		if A.shape[0] > A_prev.shape[0]:
			# We get here only when we integrate new sensing modules into the system.
			A[:A_prev.shape[0], :] = A_prev

		# Keeping previous environmental illuminance gain values (for "old" sensing modules) when integrating new
		# sensing modules helps to achieve seamless integration. (The effect of this is particularly apparent
		# when A is not very accurate.)
		E_prev = np.load(ENV_GAIN_FILE_NAME)
		if E.shape[0] > E_prev.shape[0]:
			# We get here only when we integrate new sensing modules into the system.
			E[:E_prev.shape[0]] = E_prev

	np.save(ILLUM_GAIN_MTX_FILE_NAME, A)
	np.save(ENV_GAIN_FILE_NAME, E)
	print '-'*38
	print "Illuminance Contributon Matrix:"
	print DataFrame(A)
	print "\nVector E (Environment contribution):\n", E
	print "Duration of calibration: ", time.time() - calibtation_start
	print "Calibration is completed\n", "*" * 40


# Get configs for sensing modules from the SENS_MODULE_CONFIG_FILE_NAME file.
def get_sens_module_config():
	address_list = []
	light_calibration = []
	with open(SENS_MODULE_CONFIG_FILE_NAME) as f:
		line = f.readline()
		while line:
			ip, port, calibr_const = line.split(',')
			address_list.append((ip, int(port)))
			light_calibration.append(float(calibr_const))
			line = f.readline()
	return address_list, light_calibration


# Note: the code below is used only if we want to calibrate the system without running it afterwards.
# Otherwise, calibration is initiated by rpi_sense.py.
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Calibration parameters')
	parser.add_argument('-i', '--initial_calibration', action='store_true')
	args = parser.parse_args()
	addresses, light_calibration_const = get_sens_module_config()
	office_sensing = OfficeSensing(addresses, light_calibration_const)
	ceiling_actuation = CeilingActuation(PHUE_IP_ADDRESS)

	# Calibrate
	try:
		calibrate(office_sensing, ceiling_actuation, step=0.35, B=0.65,
		          wait_time=2, initial_calibration=args.initial_calibration)
	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()
	except Exception, e:  # Stop sensing modules if there is an error
		office_sensing.stop_sens_modules()
		print "Error Message:\n", str(e)
	office_sensing.stop_sens_modules()
