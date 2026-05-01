from dataclasses import dataclass, field
import psutil
import subprocess
from .gpu_handlers import GPUS

@dataclass
class RAM_INFO:
    total:int|None = field(init=False, default=None)
    free:int|None = field(init=False, default=None)
    approx_speed:int|None = field(init=False, default=None)
    
    def __post_init__(self) -> None:
        if _ram := psutil.virtual_memory():
            self.total = int(_ram.total / (1024**3))
            self.free = int(_ram.available / (1024**3))
        
        def avg(data:list[int]) -> int|None:
            if not data:
                return None
            else:
                return int(sum(data) / len(data))
        
        _speed_data = subprocess.check_output("wmic memorychip get speed", shell=True).decode()
        if (avg_speed := avg([int(s.strip()) for s in _speed_data.split('\n') if s.strip() and s.strip().isdigit()])) != None:
            self.approx_speed = avg_speed
        else:
            self.approx_speed = None            
     
    def __str__(self) -> str:
        title = "\n|                    RAM INFO                    |\n".replace(" ", "-")
        l1 = F"\tThis PC has {self.total} GBs of RAM.\n"
        l2 = F"\twith {self.free} GBs free.\n"
        l3 = F"\tThe approximate speed is ~{self.approx_speed} Mhz.\n"
        
        if self.approx_speed:
            return title + l1 + l2 + l3
        else:
            return title + l1 + l2

@dataclass
class CPU_INFO:
    cores:int|None = psutil.cpu_count(logical=False)
    threads:int|None = psutil.cpu_count(logical=True)
    base_speed: float|None = field(init=False, default=None)
    
    def __post_init__(self) -> None:
        if _freq := psutil.cpu_freq():
            self.base_speed  = _freq.max / 1000
            
    def __str__(self) -> str:
        title = "\n|                    CPU INFO                    |\n".replace(" ", "-")
        l1 = F"\tThe CPU in this PC has {self.cores} core(s)\n"
        l2 = F"\tand {self.threads} thread(s).\n"
        l3 = F"\tIt has a base speed of ~{self.base_speed:.1f} Ghz.\n"
        return title + l1 + l2 + l3
                  
@dataclass
class SYS_SPECS:
    cpu: CPU_INFO = field(default_factory=CPU_INFO)
    ram: RAM_INFO = field(default_factory=RAM_INFO)
    gpus: GPUS = field(default_factory=GPUS)
    
    def __str__(self) -> str:
        
        l1 = str(self.ram)
        l2 = str(self.cpu)
        l3 = str(self.gpus)
        return l1 + l2 + l3