from dataclasses import dataclass, field
import psutil
import GPUtil
from typing import Any

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
class GPUS_INFO:
    _gpus:Any = field(init=False, repr=False, default_factory=lambda:GPUtil.getGPUs())
    gpus:dict =  field(init=False, default_factory=dict)
    
    def __post_init__(self) -> None:
        for gpu in self._gpus:
            self.gpus[gpu.id]  = {"name": gpu.name,
                                  "totalMem": int(gpu.memoryTotal / 1024),
                                  "freeMem": int(gpu.memoryFree / 1024)}
            
    def hasGPU(self) -> bool:
        return len(self.gpus) > 0
    
    def refreshMemory(self) -> None:
        _snap = GPUtil.getGPUs()
        
        for gpu in _snap:
            id = gpu.id
            if id in self.gpus:
                self.gpus[id]['freeMem'] = int(gpu.memoryFree / 1024)
                
@dataclass
class SYS_SPECS:
    cpu: CPU_INFO = field(default_factory=CPU_INFO)
    ram: RAM_INFO = field(default_factory=RAM_INFO)
    gpus: GPUS_INFO = field(default_factory=GPUS_INFO)
    
    def __repr__(self) -> str:
        return """

        """
    