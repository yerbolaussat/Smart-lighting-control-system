# Import libraries
from tsl2561 import TSL2561
import onionGpio
import time

# Initialize Readers
tsl = TSL2561()
pir = onionGpio.OnionGpio(1)
pir_status  = pir.setInputDirection()
print "Readers are initialized"
while True:
	visible_light_read = tsl.read_value(TSL2561.Light.Visible)
	occupancy_read = int(pir.getValue())	
	combined_string = '{} {}'.format(str(visible_light_read), str(occupancy_read))
	print "    Light:", visible_light_read
	print "    Motion:", occupancy_read
	print "\n"
	time.sleep(1)