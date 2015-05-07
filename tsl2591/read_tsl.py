'''
This code is basically an adaptation of the Arduino_TSL2591 library from 
adafruit: https://github.com/adafruit/Adafruit_TSL2591_Library

for configuring I2C in a raspberry 
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c

datasheet: 
http://ams.com/eng/Products/Light-Sensors/Light-to-Digital-Sensors/TSL25911

'''
import smbus
import time

TSL2591_VISIBLE = 2  # channel 0 - channel 1
TSL2591_INFRARED = 1  # channel 1
TSL2591_FULLSPECTRUM = 0  # channel 0

TSL2591_ADDR = 0x29
TSL2591_READBIT = 0x01
TSL2591_COMMAND_BIT = 0xA0  # bits 7 and 5 for 'command normal'
TSL2591_CLEAR_BIT = 0x40  # Clears any pending interrupt (write 1 to clear)
TSL2591_WORD_BIT = 0x20  # 1 = read/write word (rather than byte)
TSL2591_BLOCK_BIT = 0x10  # 1 = using block read/write
TSL2591_ENABLE_POWERON = 0x01
TSL2591_ENABLE_POWEROFF = 0x00
TSL2591_ENABLE_AEN = 0x02
TSL2591_ENABLE_AIEN = 0x10
TSL2591_CONTROL_RESET = 0x80
TSL2591_LUX_DF = 408.0
TSL2591_LUX_COEFB = 1.64  # CH0 coefficient
TSL2591_LUX_COEFC = 0.59  # CH1 coefficient A
TSL2591_LUX_COEFD = 0.86  # CH2 coefficient B

TSL2591_REGISTER_ENABLE = 0x00
TSL2591_REGISTER_CONTROL = 0x01
TSL2591_REGISTER_THRESHHOLDL_LOW = 0x02
TSL2591_REGISTER_THRESHHOLDL_HIGH = 0x03
TSL2591_REGISTER_THRESHHOLDH_LOW = 0x04
TSL2591_REGISTER_THRESHHOLDH_HIGH = 0x05
TSL2591_REGISTER_INTERRUPT = 0x06
TSL2591_REGISTER_CRC = 0x08
TSL2591_REGISTER_ID = 0x0A
TSL2591_REGISTER_CHAN0_LOW = 0x14
TSL2591_REGISTER_CHAN0_HIGH = 0x15
TSL2591_REGISTER_CHAN1_LOW = 0x16
TSL2591_REGISTER_CHAN1_HIGH = 0x17
TSL2591_INTEGRATIONTIME_100MS = 0x00
TSL2591_INTEGRATIONTIME_200MS = 0x01
TSL2591_INTEGRATIONTIME_300MS = 0x02
TSL2591_INTEGRATIONTIME_400MS = 0x03
TSL2591_INTEGRATIONTIME_500MS = 0x04
TSL2591_INTEGRATIONTIME_600MS = 0x05

TSL2591_GAIN_LOW = 0x00  # low gain (1x)
TSL2591_GAIN_MED = 0x10  # medium gain (25x)
TSL2591_GAIN_HIGH = 0x20  # medium gain (428x)
TSL2591_GAIN_MAX = 0x30  # max gain (9876x)


class Tsl2591():
    def __init__(
                 self,
                 i2c_bus=1,
                 sensor_address=0x29,
                 integration=TSL2591_INTEGRATIONTIME_100MS,
                 gain=TSL2591_GAIN_LOW
                 ):
        self.bus = smbus.SMBus(i2c_bus)
        self.sendor_address = sensor_address
        self.integration_time = integration
        self.gain = gain
        self.set_timing(self.integration_time)
        self.set_gain(self.gain)
        self.disable()  # to be sure

    def set_timing(self, integration):
        self.enable()
        self.integration_time = integration
        self.bus.write_byte_data(
                    self.sendor_address,
                    TSL2591_COMMAND_BIT | TSL2591_REGISTER_CONTROL,
                    self.integration_time | self.gain
                    )
        self.disable()

    def get_timing(self):
        return self.timing

    def set_gain(self, gain):
        self.enable()
        self.gain = gain
        self.bus.write_byte_data(
                    self.sendor_address,
                    TSL2591_COMMAND_BIT | TSL2591_REGISTER_CONTROL,
                    self.integration_time | self.gain
                    )
        self.disable()

    def get_gain(self):
        return self.gain

    def calculate_lux(self, full, ir):
        # Check for overflow conditions first
        if ((full == 0xFFFF) | (ir == 0xFFFF)):
            return 0
            
        case_integ = {
            TSL2591_INTEGRATIONTIME_100MS : 100.,
            TSL2591_INTEGRATIONTIME_200MS : 200.,
            TSL2591_INTEGRATIONTIME_300MS : 300.,
            TSL2591_INTEGRATIONTIME_400MS : 400.,
            TSL2591_INTEGRATIONTIME_500MS : 500.,
            TSL2591_INTEGRATIONTIME_600MS : 600.,
            }
        if self.integration_time in case_integ.keys():
            atime = case_integ[self.integration_time]
        else:
            atime = 100.

        case_gain = {
            TSL2591_GAIN_LOW : 1.,
            TSL2591_GAIN_MED : 25.,
            TSL2591_GAIN_HIGH : 428.,
            TSL2591_GAIN_MAX : 9876.,
            }
        if self.gain in case_gain.keys():
            again = case_gain[self.gain]
        else:
            again = 1.

        # cpl = (ATIME * AGAIN) / DF
        cpl = (atime * again) / TSL2591_LUX_DF
        lux1 = (full - (TSL2591_LUX_COEFB * ir)) / cpl

        lux2 = ((TSL2591_LUX_COEFC * full) - (TSL2591_LUX_COEFD * ir)) / cpl

        # The highest value is the approximate lux equivalent
        return max([lux1, lux2])

    def enable(self):
        self.bus.write_byte_data(
                    self.sendor_address,
                    TSL2591_COMMAND_BIT | TSL2591_REGISTER_ENABLE,
                    TSL2591_ENABLE_POWERON | TSL2591_ENABLE_AEN | TSL2591_ENABLE_AIEN
                    )  # Enable

    def disable(self):
        self.bus.write_byte_data(
                    self.sendor_address,
                    TSL2591_COMMAND_BIT | TSL2591_REGISTER_ENABLE,
                    TSL2591_ENABLE_POWEROFF
                    )

    def get_full_luminosity(self):
        self.enable()
        time.sleep(0.120*self.integration_time+1)  # not sure if we need it "// Wait x ms for ADC to complete"
        ir = self.bus.read_word_data(
                    self.sendor_address,TSL2591_COMMAND_BIT | TSL2591_REGISTER_CHAN1_LOW
                    )
        full = self.bus.read_word_data(
                    self.sendor_address,TSL2591_COMMAND_BIT | TSL2591_REGISTER_CHAN0_LOW
                    )
        self.disable()
        return full, ir

    def get_luminosity(self, channel):
        full, ir = self.get_full_luminosity()
        if (channel == TSL2591_FULLSPECTRUM):
            # Reads two byte value from channel 0 (visible + infrared)
            full
        elif (channel == TSL2591_INFRARED):
            # Reads two byte value from channel 1 (infrared)
            return ir
        elif (channel == TSL2591_VISIBLE):
            # Reads all and subtracts out just the visible!
            return full - ir
        # unknown channel!
        return 0



#if __name__ == '__main__':
#
#    tsl = tsl2591.Tsl2591()  # initialize
#    full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
#    lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
#    print lux, full, ir
