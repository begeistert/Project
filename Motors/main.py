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
print('Servo motors')
# Free PWM pins are 15, 4, 22, 23, 12, 13, 32 and 33
servo_pins = (33, 32, 15)
servo_motors = []

for pin in servo_pins:
    pwm = PWM(Pin(pin), freq=50)
    pwm.duty(0)
    servo_motors.append(pwm)

# DC Motor
print('DC Motor')

motor_drivers = []

standby = Pin(23, Pin.OUT)
standby.value(1)

motor = L298(5, 4, 22)
pump = L298(13, 12, None)

motor_drivers.append(motor)
motor_drivers.append(pump)
motor.speed(1023)
pump.speed(1023)

print('Define microdot app')

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
    def run_motor(m, t_on: float, direction: int):
        if isinstance(m, L298):
            if direction == 1:
                m.forward()
            elif direction == -1:
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
    return 'OK'


@app.route("/status")
def status(request):
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
