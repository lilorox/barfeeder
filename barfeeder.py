#!/usr/bin/env python
import i3ipc
import json
import math
import os
import signal
import time
from datetime import datetime
from queue import Queue
from random import random
from subprocess import Popen, PIPE
from threading import Thread

colors = {
    "background": "#ff282828",
    "foreground": "#ffebdbb2",
    "cursor": "#fffff000",
    "light red": "#fffb4934",
    "dark red": "#ffcc241d",
    "light magenta": "#ffd3869b",
    "dark magenta": "#ffb16286",
    "light blue": "#ff83a598",
    "dark blue": "#ff458588",
    "light cyan": "#ff8ec07c",
    "dark cyan": "#ff689d6a",
    "light yellow": "#fffabd2f",
    "dark yellow": "#ffd79921",
    "light green": "#ffb8bb26",
    "dark green": "#ff98971a",
    "light white": "#fffbf1c7",
    "dark white": "#ffdbae93",
    "light black": "#ff665c54",
    "dark black": "#ff1d2021",
}
icons = {
    "battery": {
        "discharging": [
            "",
            "",
            "",
            "",
            "",
        ],
        "charging": ""
    },
    "date": "",
    "time": "",
    "cpu": "",
    "memory": "",
    "disk": "",
    "network": {
        "upspeed": "",
        "downspeed": "",
        "wifi_ssid": ""
    },
}

class StatusThread(Thread):
    def __init__(self, source_id, queue):
        super().__init__()
        self.id = source_id
        self.q = queue


class DummyThread(StatusThread):
    def run(self):
        i = 0
        while True:
            self.q.put({ 
                "id": self.id,
                "output": i
            })
            time.sleep(0.5 + 0.5 * random())
            i += 1


class DateTimeThread(StatusThread):
    def __init__(self, source_id, queue,
            timeout=3):
        super().__init__(source_id, queue)
        self.timeout = timeout

    def format_output(self, current_date, current_time):
        return (
            "%%{B%s T2}   %s %%{T1} %s"
            "%%{T2}%s  %%{T1}%s   %%{F- B-}"
        ) % (
            colors["light black"],
            icons["date"],
            current_date,
            icons["time"],
            current_time
        )

    def run(self):
        previous_date = ""
        previous_time = ""
        while True:
            now = datetime.now()
            current_date = now.strftime('%d-%m-%Y')
            current_time = now.strftime('%H:%M')

            if previous_date != current_date or previous_time != current_time:
                self.q.put({
                    "id": self.id,
                    "output": self.format_output(current_date, current_time)
                })
            previous_date = current_date
            previous_time = current_time
            time.sleep(self.timeout)


class BatteryThread(StatusThread):
    def __init__(self, source_id, queue,
            timeout=3,
            sys_capa_file="/sys/class/power_supply/BAT0/capacity",
            sys_ac_file="/sys/class/power_supply/AC/online"):
        super().__init__(source_id, queue)
        self.timeout = timeout
        self.sys_capa_file = sys_capa_file
        self.sys_ac_file = sys_ac_file

    def format_output(self, capacity, ac_status):
        icon = ""
        fg_color = colors["foreground"]
        bg_color = colors["light black"]
        if ac_status == "C":
            icon = icons["battery"]["charging"]
        else:
            index = math.floor(capacity * len(icons["battery"]["discharging"]) / 100)
            icon = icons["battery"]["discharging"][index]

        if capacity < 10:
            fg_color = colors["light red"]
            bg_color = colors["light red"]
        elif capacity < 25:
            fg_color = colors["light yellow"]
        elif capacity >= 98:
            fg_color = colors["light green"]

        return "%%{+u U%s B%s} %%{F%s T2} %s %%{T1}%s%%  %%{-u B-}" % (
            fg_color,
            bg_color,
            colors["foreground"],
            icon,
            capacity
        )

    def run(self):
        current_capa = ""
        previous_capa = ""
        current_ac = ""
        previous_ac = ""
        while True:
            with open(self.sys_capa_file, 'r') as f:
                current_capa = f.read().rstrip()
                previous_capa = current_capa

            with open(self.sys_ac_file, 'r') as f:
                current_ac = f.read().rstrip()
                previous_ac = current_ac

            if previous_capa != current_capa and previous_ac != current_ac:
                self.q.put({
                    "id": self.id,
                    "output": self.format_output(current_capa, current_ac)
                })
            time.sleep(self.timeout)


class I3Thread(StatusThread):
    def __init__(self, source_id, queue,
            timeout=3):
        super().__init__(source_id, queue)
        self.timeout = timeout
        self.setup_i3_connection()

    def __del__(self):
        self.quit()
        super().__del__()

    def quit(self):
        self.i3.main_quit()

    def setup_i3_connection(self):
        self.i3 = i3ipc.Connection()
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)

        callback = lambda i3conn, event: self.on_ws_change(i3conn, event)
        self.i3.on('workspace::focus', callback)
        self.on_ws_change(self.i3, None)

    def get_state(self, workspace, event=None):
        if workspace.focused:
            if event is None or workspace.name == event.current.name:
                return "focused"
            else:
                return "active"
        if workspace.urgent:
            return "urgent"
        else:
            return "inactive"

    def on_ws_change(self, i3conn, event):
        out = "%%{F%s B%s T1}" % (
            colors["foreground"],
            colors["background"]
        )

        active_outputs = [
            output['name']
            for output in i3conn.get_outputs()
            if output['active']
        ]
        for ws in i3conn.get_workspaces():
            if not ws.output in active_outputs:
                continue
            state = self.get_state(ws, event)
            if state == "focused":
                out += "%%{+u B%s U%s T1}   %s   %%{-u B%s F%s}" %(
                    colors["light black"],
                    colors["light red"],
                    ws.name,
                    colors["background"],
                    colors["foreground"]
                )
            else:
                out += "%%{F%s T1}   %s   " % (
                    colors["light black"],
                    ws.name,
                )

        self.q.put({
            "id": self.id,
            "output": out
        })

    def run(self):
        self.i3.main()
        while True:
            time.sleep(self.timeout)


class ConkyThread(StatusThread):
    def format_output(self, raw_output):
        elements = json.loads(raw_output)
        output = ""
        if "cpu" in elements:
            output += "%%{T2}  %s  %%{T1}%s%% %%{F- B-}" % (
                icons["cpu"],
                elements["cpu"]
            )
        if "mem" in elements:
            #output += "%%{F%s T3}  %%{T2}%s %s" % (
            output += "%%{T2}  %s  %%{T1}%s%% %%{F- B-}" % (
                icons["mem"],
                elements["mem"]
            )
        if "disks" in elements:
            for disk in elements["disks"]:
                output += "%%{T2}  %s  %%{T1}%s %s%% %%{F- B-}" % (
                    icons["disk"],
                    disk,
                    elements["disks"][disk]
                )
        if "interfaces" in elements:
            for intf in elements["interfaces"]:
                intf_output = intf
                if "downspeed" in elements["interfaces"][intf]:
                    intf_output += " down=%s" % elements["interfaces"][intf]["downspeed"]
                if "upspeed" in elements["interfaces"][intf]:
                    intf_output += " up=%s" % elements["interfaces"][intf]["upspeed"]
                output.append("interface %s" % intf_output)
        return output

    def run(self):
        conky_config = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "conkyrc"
            )
        )
        with Popen(["conky", "-c", conky_config], stdout=PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                self.q.put({
                    "id": self.id,
                    "output": self.format_output(line)
                })


status_queue = Queue()
source_threads = {
    "i3": I3Thread("i3", status_queue),
    "battery": BatteryThread("battery", status_queue),
    "datetime": DateTimeThread("datetime", status_queue),
    "conky": ConkyThread("conky", status_queue),
}
statuses = {
    "i3": "",
    "battery": "",
    "datetime": "",
    "conky": "",
}


def main():
    for source, worker in source_threads.items():
        print("Setup worker %s" % source)
        worker.setDaemon(True)
        worker.start()

    while True:
        obj = status_queue.get()
        # Process info
        statuses[obj["id"]] = obj["output"]
        print((
            "%%{U%s l}%s "
            "%%{r}%s%s%s"
            ) % (
                colors["light red"],
                statuses["i3"],
                statuses["conky"],
                statuses["battery"],
                statuses["datetime"]
            )
        )
        status_queue.task_done()

if __name__ == "__main__":
    main()
