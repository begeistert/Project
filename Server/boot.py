# This file is executed on every boot (including wake-boot from deepsleep)
# import esp\n
# esp.osdebug(None)
# import webrepl
# webrepl.start()\n

import network

ap = network.WLAN(network.AP_IF)
ap.config(essid='CLASSMATE')
ap.config(max_clients=10)
ap.active(True)
