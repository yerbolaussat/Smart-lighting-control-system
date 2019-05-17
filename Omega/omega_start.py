"""
	File name: omega_start.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that sends sensor readings (light and occupancy) to Raspberry Pi, whenever it requests them 
"""

import subprocess
import time

subprocess.call('rm motion_history.txt', shell=True)
subprocess.call('kill $(pgrep -f omega_motion_tracker.py)', shell=True)
subprocess.call('python omega_motion_tracker.py &', shell=True)
time.sleep(1)
subprocess.call('python omega_responder.py', shell=True)

