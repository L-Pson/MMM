#import screeninfo
import pathlib
import os
import xml.etree.ElementTree as ET
import tempfile
import time
import psutil   
import sys 
import re
from readenv import readenv

MultiMonitorTool = readenv("MultiMonitorTool_path")
nircmd = readenv("nircmd_path")
configs_path = pathlib.Path(__file__).parent.resolve() / "configs"

class Monitors(list):
    class Monitor:
        def __init__(self, item, parent):
            self.parent = parent
            for subitem in item:
                key = subitem.tag.replace("-", "_")
                val = subitem.text

                if subitem.text == "Yes":
                    val = True
                elif subitem.text=="No":
                    val=False

                

                setattr(self, key,val)

        def make_primary(self):
            _=os.system(f"start {MultiMonitorTool} /SetPrimary {self}")
            self.parent.refresh()

        def make_active(self):
            cmd = f"start {MultiMonitorTool} /enable {self}"
            os.system(cmd)
            self.parent.refresh()

        def make_inactive(self):
            os.system(f"start {MultiMonitorTool} /disable {self}")
            self.parent.refresh()

        def __str__(self):
            return self.name

        def __eq__(self, __o: object) -> bool:
            return self.name == __o.name

    adapter_map = {
        "wall_mounted_acer": r"MONITOR\ACR0312\{4d36e96e-e325-11ce-bfc1-08002be10318}\0002",
        "EVanlak_headless_1": r"MONITOR\TCT0270\{4d36e96e-e325-11ce-bfc1-08002be10318}\0001",
        "EVanlak_headless_2": r"MONITOR\TCT0270\{4d36e96e-e325-11ce-bfc1-08002be10318}\0004",
    }

    def __init__(self):
        self.refresh()
    def refresh(self):
        with tempfile.TemporaryDirectory() as dir:
            # os.system(f"start {MultiMonitorTool} /scomma monitor_list_third.csv")
            os.system(f"cd {dir} && start {MultiMonitorTool} /sxml monitor_list.xml")
            tree = None
            i = 0
            while tree is None:
                try:
                    with open(f'{dir}\monitor_list.xml', 'rb') as xml_file:
                        tree = ET.parse(xml_file)
                except:
                    time.sleep(1/1000)
                i += 1
                if i >= 500:
                    raise Exception(f"Timed out whilst waiting for 'start {MultiMonitorTool} /sxml monitor_list.xml'.")

        monitors = []
        for child in tree.getroot():
            monitors.append(Monitors.Monitor(child, self))
        super().__init__(monitors)

    @property
    def monitor_attributes(self):
        return dir(self[0])

    
    def get_monitor(self, monitor_string) -> Monitor:
        name_of_interest = self.adapter_map[monitor_string]
        for monitor in self:
            if monitor.monitor_id == name_of_interest:
                return monitor

    def get_monitor_from_attr(self, attr, val) -> Monitor:
        for monitor in self:
            if getattr(monitor,attr) == val:
                return monitor

    @property
    def primary_monitor(self):
        for monitor in self:
            if monitor.primary:
                return monitor



class Monitor_Scenario:
    scenarios_dict = {
        "wall_mounted_only": configs_path / "wall_mounted.cfg",
        "wall_mounted_and_work_laptop": configs_path / "wall_mounted_and_work_laptop.cfg",
        "all": configs_path / "all.cfg",
    }
    def __init__(self, monitors, scenario_string):
        self.config_path = self.scenarios_dict[scenario_string]
        self._cfg = None
        self.primary_monitor = self._get_primary_monitor()
        self.monitors_to_activate = self.get_monitors_to_activate()
        self.monitors = monitors

    @staticmethod
    def _parse_config_file(path: pathlib.Path):
        with open(path,'r') as f:
            contents = f.readlines()
        cfg = {}
        current_monitor = None
        attributes = {}
        for line in contents:
            line = line.replace("\n", "")
            if re.search("\[Monitor[0-9]\]", line):
                cfg[current_monitor] = attributes
                attributes = {}
                current_monitor = line
            else:
                key, val = line.split("=")
                attributes[key] = val
            
            cfg[current_monitor] = attributes
        del cfg[None]
        return cfg

    @property
    def cfg(self):
        if self._cfg is None:
            self._cfg = self._parse_config_file(self.config_path)
        return self._cfg                

    def _get_primary_monitor(self):
        for monitor, cfg in self.cfg.items():
            if cfg["PositionX"] == '0' and cfg["PositionY"] == '0':
                return monitor

    def get_monitors_to_activate(self) -> list[Monitors.Monitor]:
        monitor_ids = []

        for monitor, cfg in self.cfg.items():
            if int(cfg["Width"]) != 0:
                monitor_ids.append(monitor)
        return monitor_ids
        

    def execute(self):

        def process_monitor(monitor: Monitors.Monitor):
            monitor.make_active()
            if monitor.monitor_id == self.cfg[self.primary_monitor]["MonitorID"]:
                monitor.make_primary()

        for monitor in monitors:
            process_monitor(monitor)

        time.sleep(2.5)

        monitors_to_make_active = []
        for monitor in monitors:
            for monitor_to_activate in self.monitors_to_activate:
                if monitor.monitor_id == self.cfg[monitor_to_activate]["MonitorID"]:
                    monitors_to_make_active.append(monitor)
        
        for monitor in monitors:
            if monitor in monitors_to_make_active:
                pass
            else:
                monitor.make_inactive()


        
        path = '/'.join([self.config_path.drive + "/"] + [f'"{i}"' for i in self.config_path.parts][1:-1])
        

        cmd = f"cd {path} && start {MultiMonitorTool} /LoadConfig {self.config_path.name}"
        _ = os.system(cmd)


class Moonlight_Connection:
    process_name = "nvstreamer.exe"

    @classmethod
    @property
    def active(cls) -> bool:
        return cls.process is not None    

    @classmethod
    def kill(cls) -> None:
        if cls.active:
            cls.process.kill()


    @classmethod
    @property
    def process(cls):
        for proc in psutil.process_iter():
            if proc.name() == cls.process_name:
                return proc

        
def moonlight_secondary_monitor(args = []) -> None:
    step = int(args[0])
    scenario_string = args[1]
    scenario = Monitor_Scenario(monitors, scenario_string)

    if len(args[2:]) > 0:
        default_string = args[2]
    else:
        default_string = "wall_mounted_only"
    default = Monitor_Scenario(monitors,default_string)





    if step == 1:
        scenario.execute()
        time.sleep(1)
        monitors.get_monitor("EVanlak_headless_1").make_primary()
        
    elif step == 2:
        time.sleep(5)

        
        while Moonlight_Connection.active:
            time.sleep(1)   

    
        
        default.execute()

    



                

def main():
    pass


    
if __name__=="__main__":
    monitors = Monitors()
    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) == 2:
        globals()[sys.argv[1]]()
    else:
        globals()[sys.argv[1]](sys.argv[2:])







