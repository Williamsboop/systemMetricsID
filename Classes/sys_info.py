from dataclasses import dataclass, field
import psutil
from gpu_handlers import GPUS

@dataclass
class RAM_INFO:
    total:int|None = field(init=False, default=None)
    
    def __post_init__(self) -> None:
        if _ram := int(psutil.virtual_memory().total / (1024**3)):
            self.total = _ram

@dataclass
class CPU_INFO:
    cores:int|None = psutil.cpu_count(logical=False)
    threads:int|None = psutil.cpu_count(logical=True)
    min_speed: float|None = field(init=False, default=None)
    max_speed: float|None = field(init=False, default=None)
    
    def __post_init__(self) -> None:
        if _freq := psutil.cpu_freq():
            self.min_speed = _freq.min
            self.max_speed  = _freq.max                
@dataclass
class SYS_SPECS:
    cpu: CPU_INFO = field(default_factory=CPU_INFO)
    ram: RAM_INFO = field(default_factory=RAM_INFO)
    gpus: GPUS = field(default_factory=GPUS)
    
if __name__ == "__main__":
    sys = SYS_SPECS()
    print(sys.ram)
    print(sys.cpu)
    print(sys.gpus)