"""
File name: simulation.py
Author: Yerbol Aussat
Python Version: 2.7

Simulation to determine nergy consumption
"""

from datetime import datetime as dt
import inspect
import os
import time
import numpy as np
from scipy.optimize import linprog
import random
import argparse


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
SIMULATION_DATA_FILE_NAME = currentdir + "/sim_data_3.csv"
ILLUM_GAIN_MTX_FILE_NAME = parentdir + '/RPi/illum_gain.npy'

# CONSTANTS:
# LED bulbs Power vs dimming level relationship params:
# Coefficients of "power vs dimming" best fit line:
SLOPE = 7.13707690629  # in Watts
ON_OFF_POWER = 1.58187308841  # in Watts
PHUE_PHANTOM_POWER = 0.605  # in Watts

# Power consumed when LED bulbs is on:
POWER_LED = SLOPE + ON_OFF_POWER

# Power consumed when CFL bulbs is on:
POWER_CFL = 20.075  # in Watts

# Power consumed when Inacndescent bulbs is on:
POWER_INC = 54.12  # in Watts

# Old values:
# SLOPE = 3.86706205178
# ON_OFF_POWER = 1.04678541344
# PHUE_PHANTOM_POWER = 0.605


# Get power required to reach target illuminance with environmental illuminance contribution E
def get_optimal_power(target_illum, E):
	a_pow = SLOPE
	c = [a_pow] * 8

	# Target for each sensor
	target_no_env = [target_illum[i] - E[i] for i in range(len(E))]
	target_no_env = np.negative(target_no_env)

	# Solve optimization program
	bounds = [(0.0, 1.0) for _ in range(8)]
	res = linprog(c, A_ub=A, b_ub=target_no_env, bounds=bounds, method='simplex', options={"disp": False})

	power = 0
	if res.success:
		d_opt = res.x
		d_opt = d_opt.tolist()
		num_bulbs_on = 0
		for dim_val in d_opt:
			if dim_val > 0.0001:
				num_bulbs_on += 1
		power = res.fun + num_bulbs_on * ON_OFF_POWER + (8-num_bulbs_on) * PHUE_PHANTOM_POWER
	else:
		print "OPTIMIZATION IS UNSUCCESSFUL"
	return power


def time_simulated(minutes):
	days = minutes / 1440
	minutes %= 1440
	hours = minutes / 60
	minutes %= 60
	return "{}{}{}".format("" if days == 0 else "{} days ".format(days),
	                       "" if hours == 0 else "{} hours ".format(hours),
	                       "{} minutes ".format(minutes))


def get_start_and_end_times():
	start_and_end_times = {}
	with open(SIMULATION_DATA_FILE_NAME) as fp:
		fp.readline()
		line = fp.readline()
		occup_history = []

		while line:
			min_from_midnight, day_of_exp, _, _, _, occup1, _, occup2, _, occup3, \
			_, occup4 = line.split(",")

			occup_vals = map(int, [occup1, occup2, occup3, occup4])

			if len(occup_history) >= 20:
				occup_history.pop()
			occup_history.insert(0, max(occup_vals))

			if any(occup_vals):
				day_of_exp = int(day_of_exp)
				min_from_midnight = int(min_from_midnight)

				if min_from_midnight > 5*60:
					if day_of_exp not in start_and_end_times:
						start_and_end_times[day_of_exp] = [min_from_midnight, -1]
					else:
						if sum(occup_history) >= 6:
							start_and_end_times[day_of_exp][1] = min_from_midnight

			line = fp.readline()
	return start_and_end_times


def simulate(illum1, occup1, illum2, occup2, illum3, occup3, illum4, occup4,
             occupancy_detection, daylight_harvesting, bulb_type):

	global total_energy
	global mins_occupied
	global mins_unoccupied
	global day_of_exp
	global min_from_midnight

	# Systems with daylight harvesting:
	if daylight_harvesting:
		occup_vals = map(int, [occup1, occup2, occup3, occup4])

		# If no occupancy detection, system should be running from start time to end time for that day
		if not occupancy_detection:
			start_t, end_t = start_and_end_times[day_of_exp] if day_of_exp in start_and_end_times else (-1, -1)
			occup_vals = [1]*4 if start_t <= min_from_midnight <= end_t else [0]*4

		target_illum = np.array([200 if occup_vals[i] == 1 else 0 for i in range(len(occup_vals))])
		illum_vals = [float(illum1), float(illum2) * (1 + random.uniform(0, 0.05)),
		              float(illum3), float(illum4) * (1 + random.uniform(0, 0.05))]
		env_gain_vals = np.array(illum_vals)

		if any(occup_vals):
			mins_occupied += 1
		else:
			mins_unoccupied += 1
		power = get_optimal_power(target_illum, env_gain_vals)
		total_energy += power / 1000 / 60

	# Systems without daylight harvesting
	else:
		occup_vals = map(int, [occup1, occup2, occup3, occup4])
		# If no occupancy detection, system should be running from start time to end time for that day
		if not occupancy_detection:
			start_t, end_t = start_and_end_times[day_of_exp] if day_of_exp in start_and_end_times else (-1, -1)
			occup_vals = [1]*4 if start_t <= min_from_midnight <= end_t else [0]*4

		if bulb_type.lower() == "led":
			if any(occup_vals):
				total_energy += 8 * POWER_LED / 1000 / 60
				mins_occupied += 1
			else:
				total_energy += 8 * PHUE_PHANTOM_POWER / 1000 / 60
				mins_unoccupied += 1
		elif bulb_type.lower() == "cfl":
			if any(occup_vals):
				total_energy += 8 * POWER_CFL / 1000 / 60
				mins_occupied += 1
			else:
				mins_unoccupied += 1
		elif bulb_type.lower() == "inc":
			if any(occup_vals):
				total_energy += 6 * POWER_INC / 1000 / 60
				mins_occupied += 1
			else:
				mins_unoccupied += 1


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Simulation parameters.')
	parser.add_argument('-d', '--daylight-harvesting', action='store_true')
	parser.add_argument('-o', '--occupancy-detection', action='store_true')
	parser.add_argument('-b', '--bulb-type', default='led', type=str)
	parser.add_argument('-n', default=90, type=int) # number of days
	args = parser.parse_args()

	print "{:<35} {:<25}".format("Simulation script started.", dt.now().strftime("%H:%M:%S.%f"))

	# global variables:
	A = np.load(ILLUM_GAIN_MTX_FILE_NAME)
	A = np.negative(A)  # To get the right format for optimization
	total_energy = 0
	mins_occupied, mins_unoccupied = 0, 0
	start_and_end_times = get_start_and_end_times()

	t_start = time.time()
	if args.bulb_type != 'led' and args.daylight_harvesting:
		print "Daylight harvesting is only supported by LED bulbs"
		exit()

	with open(SIMULATION_DATA_FILE_NAME) as fp:
		line = fp.readline()
		line = fp.readline()
		count = 0
		while line:
			if count == 1440*args.n:
				break
			min_from_midnight, day_of_exp, _, _, illum1, occup1, illum2, occup2, illum3, occup3, \
			illum4, occup4 = line.split(",")
			day_of_exp = int(day_of_exp)
			min_from_midnight = int(min_from_midnight)
			simulate(illum1, occup1, illum2, occup2, illum3, occup3, illum4, occup4,
			         args.occupancy_detection, args.daylight_harvesting, args.bulb_type)
			line = fp.readline()
			if count % 1000 == 0:
				print "\n{} simulated".format(time_simulated(count))
				print "\tEnergy consumption: {} kW h".format(total_energy)
				print "\tTime elapsed: {} sec".format(time.time() - t_start)
			count += 1

		print "\n\n", "*" * 40
		print "Final Result:"
		print "{} simulated".format(time_simulated(count))
		print "\tEnergy consumption: {} kW h".format(total_energy)
		print "\tTime elapsed: {} sec".format(time.time() - t_start)
		if mins_unoccupied + mins_occupied > 0:
			print "\tFraction Occupied: {}".format(float(mins_occupied) / (mins_unoccupied + mins_occupied))
