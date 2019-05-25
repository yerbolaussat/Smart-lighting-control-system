from OmegaExpansion import onionI2C
import time
import traceback
from enum import Enum


class TSL2561:
	class Light(Enum):
		Full_Spectrum = 0
		Infrared = 1
		Visible = 2

	def __init__(self):
		self.i2c = onionI2C.OnionI2C()
		self.i2c.writeByte(0x39, 0x00 | 0x80, 0x03)
		self.i2c.writeByte(0x39, 0x01 | 0x80, 0x02)
		time.sleep(0.5) # not sure if this is necessary?
		self.previous_value = 0

	def read_value(self, light_type):
		try:
			data = self.i2c.readBytes(0x39, 0x0C | 0x80, 2)
			data1 = self.i2c.readBytes(0x39, 0x0E | 0x80, 2)
			ch0 = data[1] * 256 + data[0]
			ch1 = data1[1] * 256 + data1[0]
			if light_type == TSL2561.Light.Full_Spectrum:
				self.previous_value = ch0
				return ch0
			elif light_type == TSL2561.Light.Infrared:
				self.previous_value = ch1
				return ch1
			elif light_type == TSL2561.Light.Visible:
				self.previous_value = ch0 - ch1
				return ch0 - ch1
			raise ValueError('Light Type {} is not supported!'.format(light_type))
		
		# If error occurred (such as I2C transaction error), return previpus light value
		except Exception, e:
			print "Error Message:\n", str(e)
			# traceback.print_exc() 
			return self.previous_value
			