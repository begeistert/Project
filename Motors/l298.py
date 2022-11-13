from machine import Pin, PWM


class L298:

    def __init__(self, en, in1, in2=None, freq=1000):
        self.freq = freq
        self._speed = 0
        self.p_en = PWM(Pin(en, Pin.OUT), freq=self.freq, duty=self._speed)
        self.p_in1 = Pin(in1, Pin.OUT)
        if in2 is not None:
            self.p_in2 = Pin(in2, Pin.OUT)
            self.p_in2(0)
        else:
            self.p_in2 = None
        self.p_in1(0)

    def stop(self):
        self.p_en.duty(0)
        self.p_in1(0)
        if self.p_in2 is not None:
            self.p_in2(0)

    def forward(self):
        if self.p_in2 is not None:
            self.p_in2(0)
        self.p_en.duty(self._speed)
        self.p_in1(1)

    def reverse(self):
        self.p_in1(0)
        self.p_en.duty(self._speed)
        if self.p_in2 is not None:
            self.p_in2(1)

    def speed(self, speed=None):
        if speed is None:
            return self._speed
        else:
            self._speed = min(1023, max(0, speed))
