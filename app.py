from flask import Flask, request
import psutil
import json
from subprocess import Popen

ACTIONS = {
    "shutdown": ['shutdown','-s','-f','-t','0'],
    "hibernate": ['shutdown','-h'],
    "logoff": ['logoff'],
    "reboot": ['shutdown','-r','-f','-t','0']
}

def fetchSystemDetails():
    systemDetails = []

    _battery = {}
    _battery["tab"] = "Battery"
    battery = psutil.sensors_battery()
    _battery["battery%"] = round(battery.percent, 2)
    _battery["chargerPlugged"] = (False, True)[battery.power_plugged]
    _battery["dischargeTimeMins"] = round(
        battery.secsleft/60, 2) if not _battery["chargerPlugged"] else -0
    systemDetails.append(_battery)

    _ram = {}
    _ram["tab"] = "RAM"
    _ram["used%"] = round(psutil.virtual_memory().percent, 2)
    # _ram["free%"] = round(100 - psutil.virtual_memory().percent,2)
    # _ram["total"] = f"{round(psutil.virtual_memory().total/1024**3,2) } GB"
    # _ram["used"] = f"{round(psutil.virtual_memory().used/1024**3,2) } GB"
    _ram["free"] = f"{round(psutil.virtual_memory().free/1024**3,2) } GB"
    systemDetails.append(_ram)

    _cpu = {}
    _cpu["tab"] = "CPU"
    _cpu["cpuCores"] = psutil.cpu_count(logical=False)
    _cpu["cpuLogicalCores"] = psutil.cpu_count()
    _cpu["cpuUsageTotal%"] = round(sum(psutil.cpu_percent(1, True))/8, 2)
    _cpu["cpuUsage%"] = psutil.cpu_percent(1, True)
    # cpusUsage as text
    # _cpu["cpuUsage"] = ", ".join(f"{cu}%"for cu in psutil.cpu_percent(1, True)).strip()

    systemDetails.append(_cpu)

    _diskUsage = []
    for disk in psutil.disk_partitions():
        diskDetails = psutil.disk_usage(disk.mountpoint)
        _diskUsage.append({
            "tab": f"Disk {disk.mountpoint}",
            # "total": f"{round(diskDetails.total / (1024.0 ** 3),2)} GB",
            # "used": f"{round(diskDetails.used / (1024.0 ** 3),2)} GB",
            "used%": round(diskDetails.percent, 2),
            "free": f"{round(diskDetails.free / (1024.0 ** 3),2)} GB",
            # "free%": round(100-diskDetails.percent,2)
        })
    systemDetails += _diskUsage

    # with open("stats.json",'w') as f:
    #     systemDetails = json.dump(systemDetails,f,indent="\t")

    return systemDetails


def mapActionToCommand(action):
    return ACTIONS.get(action)
    # return "echo hello"

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

def execCmd(endpoint):
    Popen(mapActionToCommand(endpoint.lower()))
    return f'''{endpoint.upper()} : Command executed successfully'''
@app.route('/')
def index():
    systemDetails = fetchSystemDetails()
    details = json.dumps(systemDetails, indent="  ")
    return f'''
    <title>SysMon</title>
    <meta http-equiv="refresh" content="30">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <a href="/Hibernate" target="_blank">Hibernate</a>|
    <a href="/Logout" target="_blank">Logout</a>|
    <a href="/Shutdown" target="_blank">Shutdown</a>|
    <a href="/Reboot" target="_blank">Reboot</a>
    <br>
    <pre>{details}</pre>
    '''

@app.route('/Shutdown')
def Shutdown():
    return execCmd(request.endpoint)

@app.route('/Hibernate')
def Hibernate():
    return execCmd(request.endpoint)

@app.route('/Logout')
def Logout():
    return execCmd(request.endpoint)

@app.route('/Reboot')
def Reboot():
    return execCmd(request.endpoint)

app.run(host="0.0.0.0", port=80, debug=True, threaded=True)
