from microdns import MicroDNSSrv

if MicroDNSSrv.Create({"sensors.ita": "192.168.4.3", "motors.ita": "192.168.4.4"}):
    print("MicroDNSSrv started.")
else:
    print("Error to starts MicroDNSSrv...")
