from dataclasses import dataclass, field
from typing import Any, Callable
import functools

@dataclass
class Logger:
    debug_active:bool = field(init=False, default=True)
    func:Callable = field(repr=False)
    
    def __post_init__(self) -> None:
        if not self.func.__name__.startswith("_"):
            self.debug_message = F"DEBUG: Function Running: {self.func.__name__}()"
        else:
            self.debug_message = None
    
    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self
        return functools.partial(self.__call__, instance)
    
    def __call__(self, *args:Any, **kwargs:Any) -> Any:
        if self.debug_active and self.debug_message:
            if args:
                debug:str = F"{self.debug_message}\n\tparams >>> {args}"
            else:
                debug = self.debug_message
            print(debug)
        else:
            pass
        return self.func(*args, **kwargs)