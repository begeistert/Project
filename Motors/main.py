"""
test tcs34725 using tcs345725 class library

import sys
from time import sleep
from machine import Pin, I2C

from tcs34725 import *                                  # class library


def main():
    print("Starting tcs34725_test program")
    if sys.platform == "pyboard":                       # test with PyBoard
        tcs = TCS34725(scl=Pin("B6"), sda=Pin("B7"))    # instance of TCS34725 on pyboard
    else:                                               # test with ESP32 board
        tcs = TCS34725(scl=Pin(18), sda=Pin(19))         # instance of TCS34725 on ESP32
    if not tcs.isconnected:                             # terminate if not connected
        print("Terminating...")
        sys.exit()
    tcs.gain = TCSGAIN_LOW
    tcs.integ = TCSINTEG_HIGH
    tcs.autogain = True                                 # use autogain!

    color_names = ("Clear", "Red", "Green", "Blue")

    print(" Clear   Red Green  Blue    gain  >")
    try:
        while True:                                     # forever
            colors = tcs.colors                   # obtain all counts
            counts = list(colors)                 # convert to list
            clear = colors[0]                     # clear
            print(" {:5d}".format(clear), end="")
            red = int(pow((int((colors[1] / clear) * 256) / 255), 2.5) * 255)           # red
            print(" {:5d}".format(red), end="")
            green = int(pow((int((colors[2] / clear) * 256) / 255), 2.5) * 255)  # red
            print(" {:5d}".format(green), end="")
            blue = int(pow((int((colors[3] / clear) * 256) / 255), 2.5) * 255)  # red
            print(" {:5d}".format(blue), end="")
            # not sure if this method to find the dominant color always works
            largest = max(counts[1:])                   # largest count of RGB
            avg = sum(counts[1:]) // 3                  # average of color counts
            if largest > avg * 3 // 2:                  # largest 50% over average
                color = color_names[counts.index(largest)]
            else:
                color = "-"
            print("    ({:2d})  {:s}" .format(tcs.gain_factor, color))
            sleep(5)                                    # interval between reads

    except KeyboardInterrupt:
        print("Closing down!")

    except Exception as err:
        print("Exception:", err)

    tcs.close()

main()

"""

# imports

import time
import _thread
import steppers
from microdot import Microdot
from machine import Pin, PWM
import network
from utime import sleep
from l298 import L298

ap = wlan = network.WLAN(network.STA_IF)
print(ap.ifconfig())

print('Motor 1')
m1 = steppers.A4899(26,  # step
                    17,  # direction
                    enable=21,  # enable pin
                    sleep=False,  # start in sleep mode
                    sps=200,  # steps-per-second
                    )

print('Motor 2')
m2 = steppers.A4899(25,  # step
                    2,  # direction
                    enable=21,  # enable pin
                    sleep=False,  # start in sleep mode
                    sps=200,  # steps-per-second
                    )

print('Motor 3')
m3 = steppers.A4899(27,  # step
                    0,  # direction
                    enable=21,  # enable pin
                    sleep=False,  # start in sleep mode
                    sps=200,  # steps-per-second
                    )

print('Motor 4')
m4 = steppers.A4899(18,  # step
                    19,  # direction
                    enable=21,  # enable pin
                    sleep=False,  # start in sleep mode
                    sps=200,  # steps-per-second
                    )

print('Motor 5')
m5 = steppers.A4899(14,  # step
                    16,  # direction
                    enable=21,  # enable pin
                    sleep=False,  # start in sleep mode
                    sps=200,  # steps-per-second
                    )

stepper_drivers = [m1, m2, m3, m4, m5]

for stepper in stepper_drivers:
    stepper.sleepis = 1
    stepper.step(0, 0)

# Servo motors region

# Free PWM pins are 15, 4, 22, 23, 12, 13, 32 and 33
servo_pins = (33, 32, 15)
servo_motors = []

for pin in servo_pins:
    pwm = PWM(Pin(pin), freq=50)
    pwm.duty(0)
    servo_motors.append(pwm)

# DC Motor

motor_drivers = []

standby = Pin(23, Pin.OUT)
standby.value(1)

motor = L298(5, 4, 22)

motor_drivers.append(motor)
motor.speed(1023)

# Servo motors region
"""relay_pins = (4, 13, 22, 12, 23, 15)
relays = []

for pin in relay_pins:
    relay = Pin(pin, Pin.OUT)
    relay.value(False)
    relays.append(relay) """

app = Microdot()


@app.route("/")
def index():
    return "Hello World!"


@app.post("/stepper/<identifier>")
def stepper(request, identifier):
    print('Data received')
    print('Steps: {0}'.format(request.args['steps']))
    print('Speed: {0}'.format(request.args['speed']))
    print('ID: {0}'.format(identifier))
    identifier = int(identifier)
    steps = int(request.args['steps'])
    speed = int(request.args['speed'])
    if identifier > len(stepper_drivers):
        return 'FAIL'
    if stepper_drivers[identifier].running:
        return 'ALREADY RUNNING'
    _thread.start_new_thread(stepper_drivers[identifier].step, (steps, speed))
    # stepper_drivers[identifier].step(steps, speed)
    return 'OK'


@app.post("/servo/<identifier>")
def servos(request, identifier):
    def map_val(x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    print('Data received')
    print('angle: {0}'.format(request.args['angle']))
    print('ID: {0}'.format(identifier))
    identifier = int(identifier)
    angle = int(request.args['angle'])
    if identifier > len(servo_motors) or angle > 180 or angle < 0:
        return 'FAIL'
    # Servo control here
    _thread.start_new_thread(servo_motors[identifier].duty, (map_val(angle, 0, 180, 40, 115),))
    # _thread.start_new_thread(servo_motors[identifier].duty(map_val(angle, 0, 180, 20, 120)))
    return 'OK'


@app.post("/motors/<identifier>")
def motors(request, identifier):
    def run_motor(m, t_on: float, dir: int):
        if isinstance(m, L298):
            if dir == 1:
                m.forward()
            elif dir == -1:
                m.reverse()
            sleep(t_on)
            m.stop()

    print('Data received')
    print('Time: {0}'.format(request.args['time']))
    print('Direction: {0}'.format(request.args['direction']))
    print('ID: {0}'.format(identifier))
    identifier = int(identifier)
    if identifier > len(motor_drivers):
        return 'FAIL'
    _thread.start_new_thread(run_motor, (motor_drivers[identifier], float(request.args['time']),
                                         int(request.args['direction']),))
    return 'OK'


"""""@app.post("/relay/<identifier>")
def motors(request, identifier):
    print('Data received')
    print('Enable: {0}'.format(request.args['enable']))
    print('ID: {0}'.format(identifier))
    identifier = int(identifier)
    enable = True if int(request.args['enable']) else False
    if identifier > len(servo_motors):
        return 'FAIL'
    # Servo control here
    relays[identifier].value(enable)
    return 'OK' """


@app.post("/stop")
def stop(request):
    def map_val(x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    print('Stop all process')
    for s in stepper_drivers:
        if s.running:
            s.stop = True
    for servo in servo_motors:
        servo.duty(map_val(180, 0, 180, 20, 120))
    for r in relays:
        r.value(False)
    return 'OK'


def start_server():
    print('Starting microdot app')
    try:
        app.run(port=80)
    except:
        print('The server has fallen')
        app.shutdown()


while True:
    start_server()
