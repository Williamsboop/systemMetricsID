from debugger import Logger
from Classes.sys_info import SYS_SPECS

Logger.active = False
Logger.lvl = 1

@Logger
def main() -> int:
    
    local_sys = SYS_SPECS()
    print(local_sys)
    local_sys.gpus.root.refreshMemory()
    
    return 0

if __name__ == "__main__":
    main()