from machine import Pin
from time import sleep


class IC74LS47:
    def __init__(self, d, c, b, a, not_lt=0, not_rbo=0, not_bi=0):
        self.D = Pin(d, Pin.OUT)
        self.C = Pin(c, Pin.OUT)
        self.B = Pin(b, Pin.OUT)
        self.A = Pin(a, Pin.OUT)
        self.notLT = Pin(not_lt, Pin.OUT) if not_lt is not 0 else None
        self.notRBO = Pin(not_rbo, Pin.OUT) if not_rbo is not 0 else None
        self.notBI = Pin(not_bi, Pin.OUT) if not_bi is not 0 else None

    def on(self):
        if self.notLT is not None:
            self.notLT.on()
        if self.notRBO is not None:
            self.notRBO.on()
        if self.notBI is not None:
            self.notBI.on()

    def off(self):
        if self.notLT is not None:
            self.notLT.off()
        if self.notRBO is not None:
            self.notRBO.off()
        if self.notBI is not None:
            self.notBI.off()

    def lamp_test(self):
        if self.notLT is not None:
            self.notLT.off()
        if self.notRBO is not None:
            self.notRBO.on()

        sleep(0.5)

        if self.notLT is not None:
            self.notLT.on()

    def set(self, value):
        self.D.value(value & 0x08 is not 0)
        self.C.value(value & 0x04 is not 0)
        self.B.value(value & 0x02 is not 0)
        self.A.value(value & 0x01 is not 0)


class SevenSegments:
    def __init__(self, a=0, b=0, c=0, d=0, e=0, f=0, g=0, driver: IC74LS47 = None):
        self.__number = 0
        if isinstance(driver, IC74LS47):
            self.driver = driver
        else:
            self.driver = IC74LS47(d, c, b, a, not_lt=0, not_rbo=0, not_bi=0)

    def on(self):
        self.driver.on()

    def off(self):
        self.driver.off()

    def lamp_test(self):
        self.driver.lamp_test()

    @property
    def number(self):
        return self.__number

    @number.setter
    def number(self, value):
        self.__number = value
        if self.driver is not None:
            self.driver.set(value)
        else:
            self.__set_number(value)

    def set(self, value):
        self.driver.set(value)

    def __set_number(self, number):
        if number is 0:
            self.driver.set(0x0F)
        elif number is 1:
            self.driver.set(0x06)
        elif number is 2:
            self.driver.set(0x0B)
        elif number is 3:
            self.driver.set(0x0D)
        elif number is 4:
            self.driver.set(0x06)
        elif number is 5:
            self.driver.set(0x0D)
        elif number is 6:
            self.driver.set(0x0F)
        elif number is 7:
            self.driver.set(0x07)
        elif number is 8:
            self.driver.set(0x0F)
        elif number is 9:
            self.driver.set(0x0D)
        else:
            self.driver.set(0x00)

    def set_letter(self, letter):
        if letter is 'A':
            self.driver.set(0x0E)
        elif letter is 'B':
            self.driver.set(0x0F)
        elif letter is 'C':
            self.driver.set(0x09)
        elif letter is 'D':
            self.driver.set(0x0F)
        elif letter is 'E':
            self.driver.set(0x0B)
        elif letter is 'F':
            self.driver.set(0x0B)
        elif letter is 'G':
            self.driver.set(0x0F)
        elif letter is 'H':
            self.driver.set(0x0E)
        elif letter is 'I':
            self.driver.set(0x06)
        elif letter is 'J':
            self.driver.set(0x0E)
        elif letter is 'K':
            self.driver.set(0x0E)
        elif letter is 'L':
            self.driver.set(0x08)


class ComposableSevenSegments:
    def __init__(self, amount, **kwargs):
        self.__amount = amount
        self.__number = 0
        self.__temp = 0
        driver = kwargs.get('driver', None)
        if isinstance(driver, IC74LS47):
            self.driver = driver
        else:
            a = kwargs.get('a', 0)
            b = kwargs.get('b', 0)
            c = kwargs.get('c', 0)
            d = kwargs.get('d', 0)
            self.driver = IC74LS47(d, c, b, a, not_lt=0, not_rbo=0, not_bi=0)
        self.enable_pins = []
        args = kwargs.get('display_select', None)
        for i in range(len(args)):
            arg = args[i]
            if isinstance(arg, Pin):
                self.enable_pins.append(arg)
            else:
                self.enable_pins.append(Pin(arg, Pin.OUT))
        self.controllers = []
        for i in range(0, amount):
            self.controllers.append(SevenSegments(driver=self.driver))

    def test(self):
        for pin in self.enable_pins:
            pin.on()
            self.driver.lamp_test()
            pin.off()

    def show(self):
        self.driver.on()
        while True:
            value = self.__temp
            digits = [
                value % 10,
                (value % 100 - value % 10) // 10,
                (value % 1000 - value % 100) // 100
            ]
            for i in range(0, self.__amount):
                self.controllers[i].number = digits[i]
                self.enable_pins[i].on()
                sleep(0.001)
                self.enable_pins[i].off()
                sleep(0.001)
            self.__temp = self.__number

    async def run_async(self, lock):
        while True:
            await lock.acquire()
            value = self.__temp
            digits = [
                value % 10,
                (value % 100 - value % 10) // 10,
                (value % 1000 - value % 100) // 100
            ]
            lock.release()
            for i in range(0, self.__amount):
                self.controllers[i].number = digits[i]
                self.enable_pins[i].on()
                sleep(0.001)
                self.enable_pins[i].off()
                sleep(0.001)
            self.__temp = self.__number

    @property
    def number(self):
        return self.__number

    @number.setter
    def number(self, value):
        self.__number = value
