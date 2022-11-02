from machine import ADC, Pin


class Piezo:
    def __init__(self, pin):
        self.sensor = ADC(Pin(pin, Pin.IN))
        self.calibration_value = 0
        self.calibrate()

    def calibrate(self):
        self.calibration_value = self.sensor.read_u16()

    def touch_begins(self):
        return self.sensor.read_u16() != self.calibration_value
