from microdot import Microdot
from hcsr04 import HCSR04
from tcs34725 import TCS34725
from piezo import Piezo
from machine import Pin
import network
import _thread
import time

ap = wlan = network.WLAN(network.STA_IF)
print(ap.ifconfig())

# Create the HC-SR04 object
distance_sensor = HCSR04(trigger_pin=33, echo_pin=25)

# Create the TCS34725 object
tcs = TCS34725(scl=Pin(27), sda=Pin(32))

# Create three piezo objects
piezo1 = Piezo(36)
piezo2 = Piezo(39)
piezo3 = Piezo(34)

piezos = [piezo1, piezo2, piezo3]

for piezo_e in piezos:
    piezo_e.calibrate()

metal_sensor = Pin(26, Pin.IN)

emergency = Pin(5, Pin.IN)
emergency_old = False

relay_pins = (4, 14, 22, 12, 23, 19)
relays = []

for pin in relay_pins:
    relay = Pin(pin, Pin.OUT)
    relay.value(True)
    relays.append(relay)

# Create web app

app = Microdot()


@app.route("/")
def index():
    return "Hello World!"


"""
@app.route("/distance")
def distance(request):
    d = distance_sensor.distance_cm()
    return f'{d}'
"""


@app.get("/colour")
def color(request):
    red, green, blue = tcs.rgb
    return {'red': red, 'green': green, 'blue': blue}


@app.get("/metal")
def is_metal(request):
    metal = metal_sensor.value()
    return {'is_metal': metal}


@app.get("/piezo/<int:identifier>")
def is_metal(request, identifier):
    piezo = piezos[identifier]
    value = piezo.touch_begins()
    print('Piezo {0} value: {1}'.format(identifier, value))
    return {'value': value}
    return {'id': identifier, 'touch': value}


@app.post("/relay/<identifier>")
def motors(request, identifier):
    print('Data received')
    print('Enable: {0}'.format(request.args['enable']))
    print('ID: {0}'.format(identifier))
    identifier = int(identifier)
    enable = True if int(request.args['enable']) else False
    if identifier > len(relays):
        return 'FAIL'
    # Servo control here
    relays[identifier].value(not enable)
    return 'OK'


def start_server():
    print('Starting microdot app')
    try:
        app.run(port=80)
    except:
        print('The server has fallen')
        app.shutdown()


def emergency_shutdown():
    global emergency_old

    send = False
    stop = False
    while True:
        if not emergency.value() and emergency_old:
            stop = not stop
            send = True
        elif emergency.value() and not emergency_old:
            time.sleep(0.5)

        if send:
            import requests

            requests.post('http://process.ita/stop?stop={0}'.format(1 if stop else 0))
            send = False
        emergency_old = emergency.value()


_thread.start_new_thread(emergency_shutdown, ())

while True:
    start_server()
"""
from seven_segments import ComposableSevenSegments, IC74LS47
from microdot import Microdot
import network
import _thread

wlan = network.WLAN(network.STA_IF)
print('network config:', wlan.ifconfig())

app = Microdot()

driver = IC74LS47(5, 22, 23, 17, 21, 19, 18)
displays = ComposableSevenSegments(3, display_select=(15, 2, 4), driver=driver)


@app.route("/")
def index():
    return "Hello World!"


@app.route("/display")
def distance(request):
    print('Data received')
    number = int(request.args['number'])
    displays.number = number
    return f'OK'


_thread.start_new_thread(displays.show, ())

while True:
    try:
        app.run(port=80)
    except:
        print('An error has ocurred')
"""
