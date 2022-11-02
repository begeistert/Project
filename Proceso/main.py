import requests
from time import sleep

hosts = ('http://sensors.ita', 'http://motors.ita')


def status():
    for host in hosts:
        try:
            r = requests.get(f'{host}/')
            if r.status_code == 200:
                print(f'{host} = Working')
            else:
                print(f'{host} = Failing')
            print(r.text)
        except Exception as e:
            print(e)


def process():
    # Start the process
    # Enable the lights with a post to the sensors.ita
    requests.post(f'{hosts[0]}/relay/0?enable=1')
    requests.post(f'{hosts[0]}/relay/4?enable=1')
    sleep(3)
    requests.post(f'{hosts[0]}/relay/0?enable=0')
    requests.post(f'{hosts[0]}/relay/4?enable=0')
    sleep(10)
    is_metal = int(requests.get(f'{hosts[0]}/metal').json()['is_metal'])
    is_wood = False
    is_plastic = False
    if not is_metal:
        colours = requests.get(f'{hosts[0]}/colour').json()
        red = colours['red']
        green = colours['green']
        blue = colours['blue']
        # Wood -> Green > 20, Red < 20, Blue < 20
        is_wood = green > 20 > blue and red < 20
        is_plastic = not is_wood

    requests.post(f'{hosts[0]}/relay/{3 if is_metal else 2 if is_plastic else 1}?enable=1')
    # enable the servomotor giving an angle
    requests.post(f'{hosts[1]}/servo/{2 if is_metal else 1 if is_plastic else 0}?angle=90')
    # enable the motor for 5 seconds
    requests.post(f'{hosts[1]}/motors/0?time=15&direction=-1')
    # enable the stepper motor for 5 seconds
    requests.post(f'{hosts[1]}/stepper/0?steps=7000&speed=1000')
    # read the piezo sensor and give a time out of 15 seconds
    cube_in_place = requests.get(f'{hosts[0]}/piezo/{2 if is_metal else 0}', timeout=15).json()['value']
    # enable the motor for 5 seconds in reverse
    requests.post(f'{hosts[1]}/motors/0?time=15&direction=1')
    requests.post(f'{hosts[1]}/servo/{2 if is_metal else 0}?angle=180')

    result = False

    if is_metal and cube_in_place:
        requests.post(f'{hosts[1]}/stepper/3?steps=18000&speed=20000')
        sleep(5)
        requests.post(f'{hosts[1]}/stepper/3?steps=-18000&speed=20000')
        result = True
    elif is_wood and cube_in_place:
        requests.post(f'{hosts[0]}/relay/1?enable=1')
        requests.post(f'{hosts[1]}/stepper/1?steps=15000&speed=1000')
        sleep(5)
        requests.post(f'{hosts[1]}/stepper/1?steps=-15000&speed=1000')
        requests.post(f'{hosts[0]}/relay/1?enable=0')
        result = True
    elif is_plastic and cube_in_place:
        requests.post(f'{hosts[1]}/stepper/2?steps=-20000&speed=4000')
        requests.post(f'{hosts[0]}/relay/5?enable=1')
        sleep(0.001)
        requests.post(f'{hosts[0]}/relay/5?enable=0')
        requests.post(f'{hosts[1]}/stepper/2?steps=20000&speed=4000')
        result = True

    return 'OK' if result else 'FAIL'


status()
process()
