from dataclasses import dataclass, field
from GPUtil import getGPUs
from typing import Any

@dataclass
class GPU_BASE:
    gpus:dict =  field(init=False, default_factory=dict)
    
    def hasGPU(self) -> bool:
        return len(self.gpus) > 0

@dataclass
class NVIDIA_GPUS(GPU_BASE):
    brand:str = "NVIDIA"
    _gpus:Any = field(init=False, repr=False, default_factory=lambda:getGPUs())
    
    def __post_init__(self) -> None:
        super().__init__()
        for gpu in self._gpus:
            self.gpus[gpu.id]  = {"name": gpu.name,
                                  "totalMem": int(gpu.memoryTotal / 1024),
                                  "freeMem": int(gpu.memoryFree / 1024)}
    
    def refreshMemory(self) -> None:
        for gpu in getGPUs():
            if gpu.id in self.gpus:
                self.gpus[id]['freeMem'] = int(gpu.memoryFree / 1024)

@dataclass
class AMD_GPUS(GPU_BASE):
    brand:str = "AMD"
    pass

@dataclass
class GPU_INFO:
    pass