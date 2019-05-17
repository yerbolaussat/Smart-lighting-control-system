"""
	File name: rpi_calibrate_and_start.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that calibrates initializes and calibrates the system (extracts matrix A)
"""
import subprocess
subprocess.call('python rpi_calibrate.py', shell=True)
subprocess.call('python rpi_sense.py', shell=True)
