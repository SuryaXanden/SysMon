from flask import Flask, request, jsonify
import psutil
import json
from subprocess import Popen

ACTIONS = {
    "shutdown": ['shutdown', '-s', '-f', '-t', '0'],
    "hibernate": ['shutdown', '-h'],
    "logoff": ['logoff'],
    "reboot": ['shutdown', '-r', '-f', '-t', '0'],
    "lock": ['rundll32', 'user32.dll,LockWorkStation'],
    "off": ["powershell", "-Command", '(Add-Type -MemberDefinition "[DllImport(""user32.dll"")]`npublic static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);" -Name "Win32SendMessage" -Namespace Win32Functions -PassThru)::SendMessage(0xffff, 0x0112, 0xF170, 2)']
}
# constants
HOST = "0.0.0.0"
PORT = 80
DEBUG = True
THREADED = True


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
    cpuUsage = psutil.cpu_percent(1, True)
    _cpu["cpuUsageTotal%"] = round(
        (sum(cpuUsage)/(100*_cpu["cpuCores"]))*100, 2)
    _cpu["cpuUsage%"] = cpuUsage
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

    return systemDetails


def mapActionToCommand(action):
    return ACTIONS.get(action)


def execCmd(endpoint):
    Popen(mapActionToCommand(endpoint.lower()))
    return f'''{endpoint.upper()} command is executed successfully'''


if __name__ == "__main__":
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False

    @app.route('/')
    def index():
        systemDetails = fetchSystemDetails()
        details = json.dumps(systemDetails, indent="  ")
        return f'''
        <title>SysMon</title>
        <meta http-equiv="refresh" content="30">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <pre>{details}</pre>
        '''

    @app.route('/json')
    def _json():
        return jsonify(fetchSystemDetails())

    @app.route('/Shutdown')
    @app.route('/Hibernate')
    @app.route('/Logout')
    @app.route('/Reboot')
    @app.route('/Lock')
    @app.route('/Off')
    def actions():
        execCmd((request.path)[1:])
        return '''
        <script>
        window.onbeforeunload = e => {
            e.preventDefault();
            e.returnValue = '';
        }
        </script>
        ''' + f"""{(request.path)[1:].upper()} executed successfully."""

    @app.route('/remote')
    def remote():
        systemDetails = fetchSystemDetails()
        details = json.dumps(systemDetails, indent="  ")
        return f'''
        <title>SysMon</title>
        <meta http-equiv="refresh" content="30">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        |<a href="/Off" target="_blank"><b>&#x260D; </b>TOS</a>
        |<a href="/Lock" target="_blank"><b>&#x262F; </b>Lock</a>
        |<a href="/Hibernate" target="_blank"><b>&#x273E; </b>Hibernate</a>
        <br>
        |<a href="/Logout" target="_blank"><b>&#x26E2; </b>Logout</a>
        |<a href="/Shutdown" target="_blank"><b>&#x2620; </b>Shutdown</a>
        |<a href="/Reboot" target="_blank"><b>&#x267A; </b>Reboot</a>
        <br>
        <br>
        <pre>{details}</pre>
        '''

    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=THREADED)
