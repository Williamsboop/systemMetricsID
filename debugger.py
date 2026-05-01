from dataclasses import dataclass, field
from typing import Any, Callable
import functools
import inspect

@dataclass
class Logger:
    active: bool = field(init=False, default=True)
    lvl:int = field(init=False, default=int(1))
    func: Callable = field(repr=False)

    def __post_init__(self) -> None:
        self._file:     str = inspect.getfile(self.func)
        self._instance: Any = None
        self._owner:    Any = None

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self
        self._instance = instance
        self._owner    = owner
        return functools.partial(self.__call__, instance)

    @property
    def _debug_message(self) -> str | None:
        
        
        
        if self.lvl < 2 and self.func.__name__.startswith("_"):
            return None

        if self._owner:
            locale = inspect.getfile(self._owner).replace("\\", "/").split("/")[-1]
            return (
                f"\nDEBUG: Function Running: {self._owner.__name__}.{self.func.__name__}()"
                f"\n\t| LOCALE -> {locale}"
            )

        locale = self._file.replace("\\", "/").split("/")[-1]
        return (
            f"\nDEBUG: Function Running: {self.func.__name__}()"
            f"\n\t| LOCALE -> {locale}"
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.active and (message := self._debug_message):
            display_args = tuple(a for a in args if a is not self._instance)
            debug = f"{message}\n\t| PARAMS -> {display_args}" if display_args else message
            debug += "\n\t¯"
            print(debug)

        return self.func(*args, **kwargs)
    
    def __str__(self) -> str:
        return (
            f"Logger — function decorator for debug tracing.\n"
            f"  Wraps:        {self.func.__name__}()\n"
            f"  Source:       {self._file.replace(chr(92), '/').split('/')[-1]}\n"
            f"  Debug active: {self.active}\n"
            f"  Debug level:  {self.lvl} "
            f"({'private functions hidden' if self.lvl > 2 else 'all functions shown'})\n"
        )
    
if __name__ == "__main__":
    @Logger
    def example(): pass
    print(example)