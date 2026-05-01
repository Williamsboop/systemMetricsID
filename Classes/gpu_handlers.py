from debugger import Logger
from dataclasses import dataclass, field
from GPUtil import getGPUs as get_gpus
from .amd import get_dxgi_gpu_info
from typing import Any

@dataclass
class GPU_BASE:
    brand:str = field(init=False, default="")
    info:dict =  field(init=False, default_factory=dict)

    @Logger 
    def has_gpu(self) -> bool:
        return len(self.info) > 0

@dataclass
class NVIDIA_GPUS(GPU_BASE):
    _gpus:Any = field(init=False, repr=False, default_factory=lambda:get_gpus())
    
    def __post_init__(self) -> None:
        for gpu in self._gpus:
            self.info[gpu.id]  = {"name": gpu.name,
                                  "totalMem": int(gpu.memoryTotal / 1024),
                                  "freeMem": int(gpu.memoryFree / 1024)}
    
    @Logger
    def refreshMemory(self) -> None:
        for gpu in get_gpus():
            if gpu.id in self.info:
                self.info[gpu.id]['freeMem'] = int(gpu.memoryFree / 1024)

@dataclass
class AMD_GPUS(GPU_BASE):
    def __post_init__(self) -> None:
        self.info = get_dxgi_gpu_info()
        
    def refreshMemory(self) -> None:
        snap = get_dxgi_gpu_info()
        for id, data in snap.items():
            if id in self.info:
                self.info[id]["freeMem"] = data["freeMem"]

@dataclass
class GPUS:
    root:AMD_GPUS|NVIDIA_GPUS = field(init=False)
    
    def __post_init__(self) -> None:
        nvidia = NVIDIA_GPUS()
        if nvidia.has_gpu():
            self.root = nvidia
            self.root.brand = "NVIDIA"
            return
        self.root = AMD_GPUS()
        self.root.brand = "AMD"
        
    def __str__(self) -> str:
        title = "\n|                    GPU INFO                    |\n\n".replace(" ", "-")
        l1 = F"\t• This PC has {len(self.root.info)} discrete card(s).\n"
        l2 = F"\t• The brand of the main card is {self.root.brand}.\n"
        l3 = F"\t• The total memory available on\n\t  this card is {self.root.info[0]['totalMem']}GB.\n"
        return title + l1 + l2 + l3