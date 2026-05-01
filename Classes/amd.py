from debugger import Logger
import ctypes

# Constants
DXGI_MEMORY_SEGMENT_GROUP_LOCAL = 0
DXGI_ADAPTER_FLAG_SOFTWARE = 2

VENDOR_AMD    = 0x1002
VENDOR_NVIDIA = 0x10DE
VENDOR_INTEL  = 0x8086

class DXGI_QUERY_VIDEO_MEMORY_INFO(ctypes.Structure):
    _fields_ = [
        ("Budget", ctypes.c_uint64),
        ("CurrentUsage", ctypes.c_uint64),
        ("AvailableForReservation", ctypes.c_uint64),
        ("CurrentReservation", ctypes.c_uint64),
    ]

class DXGI_ADAPTER_DESC2(ctypes.Structure):
    _fields_ = [
        ("Description", ctypes.c_wchar * 128),
        ("VendorId", ctypes.c_uint),
        ("DeviceId", ctypes.c_uint),
        ("SubSysId", ctypes.c_uint),
        ("Revision", ctypes.c_uint),
        ("DedicatedVideoMemory", ctypes.c_size_t),
        ("DedicatedSystemMemory", ctypes.c_size_t),
        ("SharedSystemMemory", ctypes.c_size_t),
        ("AdapterLuid", ctypes.c_byte * 8),
        ("Flags", ctypes.c_uint),
        ("GraphicsPreemptionGranularity", ctypes.c_int),
        ("ComputePreemptionGranularity", ctypes.c_int),
    ]

IID_IDXGIFactory1 = (ctypes.c_byte * 16)(
    0x78, 0xae, 0x0a, 0x77, 0x6f, 0xf2, 0xba, 0x4d,
    0xa8, 0x29, 0x25, 0x3c, 0x83, 0xd1, 0xb3, 0x87
)

IID_IDXGIAdapter3 = (ctypes.c_byte * 16)(
    0xA4, 0x67, 0x59, 0x64, 0x92, 0x13, 0x10, 0x43,
    0xA7, 0x98, 0x80, 0x53, 0xCE, 0x3E, 0x93, 0xFD
)

@Logger
def _vtable_fn(obj, slot, restype, *argtypes):
    vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))
    fn_ptr = ctypes.cast(vtable[0], ctypes.POINTER(ctypes.c_void_p))[slot]
    return ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(fn_ptr)

@Logger
def _release(obj):
    if obj:
        _vtable_fn(obj, 2, ctypes.c_ulong)(obj)

@Logger
def _query_interface(obj, iid, out):
    return _vtable_fn(
        obj, 0, ctypes.c_long, ctypes.POINTER(ctypes.c_byte * 16), ctypes.POINTER(ctypes.c_void_p)
    )(obj, iid, out)

@Logger
def get_dxgi_gpu_info() -> dict:
    ctypes.windll.ole32.CoInitialize(None)
    factory = ctypes.c_void_p()

    hr = ctypes.windll.dxgi.CreateDXGIFactory1(
        ctypes.byref(IID_IDXGIFactory1), ctypes.byref(factory)
    )

    if hr != 0:
        ctypes.windll.ole32.CoUninitialize()
        return {}

    enum_adapters = _vtable_fn(
        factory, 12, ctypes.c_long, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)
    )

    gpus = {}
    index = 0
    while True:
        adapter1 = ctypes.c_void_p()
        if enum_adapters(factory, index, ctypes.byref(adapter1)) != 0:
            break

        adapter3 = ctypes.c_void_p()
        qi_hr = _query_interface(adapter1, IID_IDXGIAdapter3, ctypes.byref(adapter3))
        _release(adapter1)

        if qi_hr != 0:
            index += 1
            continue

        desc = DXGI_ADAPTER_DESC2()
        _vtable_fn(adapter3, 10, ctypes.c_long, ctypes.POINTER(DXGI_ADAPTER_DESC2))(adapter3, ctypes.byref(desc))

        mem_info = DXGI_QUERY_VIDEO_MEMORY_INFO()
        _vtable_fn(adapter3, 14, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(DXGI_QUERY_VIDEO_MEMORY_INFO))(
            adapter3, 0, DXGI_MEMORY_SEGMENT_GROUP_LOCAL, ctypes.byref(mem_info)
        )

        # --- REFINED DISCRETE FILTER ---
        is_hardware = (desc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) == 0
        has_min_vram = desc.DedicatedVideoMemory > (2 * 1024 * 1024 * 1024)
        
        name_lower = desc.Description.lower()
        is_not_labeled_integrated = not any(x in name_lower for x in ["graphics", "integrated", "uhd"])

        if is_hardware and desc.VendorId in (VENDOR_AMD, VENDOR_NVIDIA, VENDOR_INTEL):
            if has_min_vram or (is_not_labeled_integrated and desc.DedicatedVideoMemory > 0):
                gpus[index] = {
                    "name": desc.Description,
                    "totalMem": desc.DedicatedVideoMemory // (1024 ** 3),
                    "freeMem": max(0, mem_info.Budget - mem_info.CurrentUsage) // (1024 ** 3),
                }

        _release(adapter3)
        index += 1

    _release(factory)
    ctypes.windll.ole32.CoUninitialize()
    return gpus