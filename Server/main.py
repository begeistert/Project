from microdns import MicroDNSSrv
from microdot import Microdot
from socket import getaddrinfo
import json

if MicroDNSSrv.Create({"sensors.ita": "192.168.4.3", "motors.ita": "192.168.4.4"}):
    print("MicroDNSSrv started.")
else:
    print("Error to starts MicroDNSSrv...")

app = Microdot()

emergency_stop = False
manual_mode = False


@app.route("/")
def index(request):
    return "Hello World!"


@app.route("/start")
def start(request):
    if manual_mode:
        return "Manual mode is on"
    return "Starting the process"


@app.route("/stop")
def stop(request):
    global emergency_stop

    emergency_stop = True
    return "Stopping all processes - See the logs"


@app.route("/history")
def history(request):
    h = json.loads('history.json')
    return h


@app.route("/status")
def status(request):
    domains = ["sensors.ita", "motors.ita"]
    s = ''
    for domain in domains:
        try:
            ip = getaddrinfo(domain, 80)[0][-1][0]
            s += f'{domain} = {ip}'
            print("IP: ", ip)
        except Exception as e:
            s += f'{domain} = Not found'
            print("Error: ", e)
    return s


@app.route("/logs/<int:identifier>")
def logs(request, identifier):
    file = open(f'logs/{identifier}', 'r')
    return file.read()


@app.route("/manual")
def manual(request):
    return "Manual..."


@app.route("/date")
def date(request):

    return "Date..."



while True:
    pass
