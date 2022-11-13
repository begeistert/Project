import requests
from time import sleep

hosts = ('http://sensors.ita', 'http://motors.ita')
current_position = 0  # 0 for plastic, 1 for wood and 2 for metal
start = False
stop = False
old_value = False



def position(pos: int) -> int:
    global current_position

    steps = 0
    if current_position == 0:
        if pos == 1:
            steps = -1_100
        elif pos == 2:
            steps = 1_100
    elif current_position == 1:
        if pos == 0:
            steps = 1_100
        elif pos == 2:
            steps = -1_100
    elif current_position == 2:
        if pos == 0:
            steps = -1_100
        elif pos == 1:
            steps = 1_100

    current_position = pos

    return steps


def status():
    result = True
    for host in hosts:
        try:
            r = requests.get(f'{host}/')
            result = result and r.status_code == 200
            if r.status_code == 200:
                print(f'{host} = Working')
            else:
                print(f'{host} = Failing')
            print(r.text)
        except Exception as e:
            print(e)

    return result


def process():
    # Start the process
    # Enable the lights with a post to the sensors.ita
    print('Starting process')
    print('Alert')
    requests.post(f'{hosts[0]}/relay/0?enable=1')
    requests.post(f'{hosts[0]}/relay/4?enable=1')
    if stop:
        return
    sleep(3)
    print('Disable alert')
    requests.post(f'{hosts[0]}/relay/0?enable=0')
    requests.post(f'{hosts[0]}/relay/4?enable=0')
    if stop:
        return
    sleep(5)
    print('Know if is metal')
    is_metal = int(requests.get(f'{hosts[0]}/metal').json()['is_metal'])
    is_wood = False
    is_plastic = False
    if not is_metal:
        print('Get colors')
        colours = requests.get(f'{hosts[0]}/colour').json()
        red = colours['red']
        green = colours['green']
        blue = colours['blue']
        # Wood -> Green > 20, Red < 20, Blue < 20
        is_wood = green > 20 > blue and red < 20
        is_plastic = not is_wood

    if stop:
        return
    print('Choose the path of the cube')
    requests.post(f'{hosts[0]}/relay/{3 if is_metal else 2 if is_plastic else 1}?enable=1')
    # enable the servomotor giving an angle
    requests.post(f'{hosts[1]}/servo/{2 if is_metal else 1 if is_plastic else 0}?angle=90')
    # enable the motor for 5 seconds
    requests.post(f'{hosts[1]}/motors/0?time=15&direction=1')
    # enable the stepper motor for 5 seconds
    requests.post(f'{hosts[1]}/stepper/0?steps=700000&speed=5000')
    # read the piezo sensor and give a time out of 15 seconds
    if stop:
        return
    sleep(20)
    print('Stop the stepper motor')
    # enable the motor for 5 seconds in reverse
    requests.post(f'{hosts[1]}/motors/0?time=15&direction=-1')
    requests.post(f'{hosts[1]}/stop')
    if stop:
        return

    result = False
    steps = 0

    if is_metal:
        print('Is metal')
        requests.post(f'{hosts[1]}/stepper/3?steps=18000&speed=20000')
        if stop:
            return
        sleep(1)
        requests.post(f'{hosts[1]}/stepper/3?steps=-18000&speed=20000')
        sleep(1)
        requests.post(f'{hosts[0]}/relay/3?enable=0')
        result = True
        steps = position(2)
    elif is_wood:
        print('Is wood')
        requests.post(f'{hosts[1]}/stepper/1?steps=15000&speed=1000')
        if stop:
            return
        sleep(16)
        requests.post(f'{hosts[1]}/stepper/1?steps=-15000&speed=1000')
        if stop:
            return
        sleep(16)
        requests.post(f'{hosts[0]}/relay/1?enable=0')
        result = True
        steps = position(1)
    elif is_plastic:
        print('Is plastic')
        requests.post(f'{hosts[1]}/stepper/2?steps=-20000&speed=4000')
        if stop:
            return
        sleep(6)
        requests.post(f'{hosts[1]}/motors/1?time=0.1&direction=1')
        sleep(1)
        requests.post(f'{hosts[1]}/stepper/2?steps=20000&speed=4000')
        if stop:
            return
        sleep(6)
        requests.post(f'{hosts[0]}/relay/2?enable=0')
        result = True
        steps = position(0)

    if stop:
        return
    print('Choose the segment')
    requests.post(f'{hosts[1]}/stepper/4?steps={steps}&speed=2000')
    requests.post(f'{hosts[0]}/release')

    return 'OK' if result else 'FAIL'


def send_stop():
    global stop

    requests.post(f'{hosts[1]}/stop')
    requests.post(f'{hosts[0]}/stop')
    stop = False


process()

while True:
    process()
