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

emergency = Pin(5, Pin.IN, Pin.PULL_UP)
emergency_old = True

relay_pins = (4, 14, 22, 12, 23)
relays = []

for pin in relay_pins:
    relay = Pin(pin, Pin.OUT)
    relay.value(True)
    relays.append(relay)

stop = False

# Create web app

app = Microdot()


@app.route("/")
def index():
    return "Hello World!"


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
    # piezo.calibrate()
    t = time.time()
    positive_count = 0
    while time.time() - t < 30:
        # time.sleep(0.001)
        # piezo.calibrate()
        value = piezo.touch_begins()
        print(value)
        if value:
            positive_count += 1
            if positive_count > 150:
                return {'value': True}
    return {'value': False}


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


@app.post("/stop")
def emergency_stop(request):
    for r in relays:
        r.value(True)
    return 'OK'


@app.get("/status")
def motors(request):
    return 'OK'


@app.post("/release")
def motors(request):
    global stop

    stop = False
    return 'OK'


def start_server():
    print('Starting microdot app')
    try:
        app.run(port=80)
    except:
        print('The server has fallen')
        app.shutdown()


def emergency_shutdown():
    global emergency_old, stop

    send = False
    stop = True
    while True:
        if emergency.value() and not emergency_old:
            print('Event detected')
            stop = not stop
            send = True
            time.sleep(0.5)

        if send:
            import urequests as requests

            if not stop:
                print('Sending init')
                try:
                    requests.post('http://process.ita/start')
                except:
                    print('Failed to send init')
            else:
                print('Sending stop')
                try:
                    requests.post('http://process.ita/stop')
                except:
                    print('Failed to send stop')
            send = False
        emergency_old = emergency.value()


_thread.start_new_thread(emergency_shutdown, ())

while True:
    start_server()
