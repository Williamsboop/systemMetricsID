from Classes.sys_info import SYS_SPECS

def main() -> int:
    
    sys = SYS_SPECS()

    print(sys.ram)
    print(sys.cpu)
    # print(sys.gpus)
    
    return 0

if __name__ == "__main__":
    main()