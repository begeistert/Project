# This file is executed on every boot (including wake-boot from deepsleep)
# import esp\n
# esp.osdebug(None)
# import webrepl
# webrepl.start()\n

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('CLASSMATE')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    wlan.ifconfig(('192.168.4.4', '255.255.255.0', '192.168.4.1', '0.0.0.0'))


do_connect()
