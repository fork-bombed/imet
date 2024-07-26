import ctypes
from ctypes import wintypes


kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


SIZE_T = ctypes.c_size_t
LPCTSTR = ctypes.c_char_p
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
MEM_DECOMMIT = 0x00004000
MEM_RELEASE = 0x00008000
PAGE_READWRITE = 0x04
EXECUTE_IMMEDIATELY = 0x0
PROCESS_ALL_ACCESS = 0x000F0000 | 0x00100000 | 0xFFF


class _SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ('nLength', wintypes.DWORD),
        ('lpSecurityDescriptor', wintypes.LPVOID),
        ('bInheritHandle', wintypes.LPBOOL)
    ]


LPSECURITY_ATTRIBUTES = ctypes.POINTER(_SECURITY_ATTRIBUTES)


def msdn_wrap(args, res, error_check=True):
    def decorator(func):
        func.argtypes = args
        func.restype = res
        def wrapper(*func_args):
            result = func(*func_args)
            if error_check and not result:
                raise ctypes.WinError()
            return result
        return wrapper
    return decorator


@msdn_wrap(
    (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD),
    wintypes.HANDLE
)
def OpenProcess(dwDesiredAccess, bInheritHandle, dwProcessId):
    return kernel32.OpenProcess(dwDesiredAccess, bInheritHandle, dwProcessId)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.LPVOID, SIZE_T, wintypes.DWORD, wintypes.DWORD),
    wintypes.LPVOID
)
def VirtualAllocEx(hProcess, lpAddress, dwSize, flAllocationType, flProtect):
    return kernel32.VirtualAllocEx(hProcess, lpAddress, dwSize, flAllocationType, flProtect)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, SIZE_T, ctypes.POINTER(SIZE_T)),
    wintypes.BOOL
)
def WriteProcessMemory(hProcess, lpBaseAddress, lpBuffer, nSize, lpNumberOfBytesWritten):
    return kernel32.WriteProcessMemory(hProcess, lpBaseAddress, lpBuffer, nSize, lpNumberOfBytesWritten)


@msdn_wrap(
    (LPCTSTR,),
    wintypes.HANDLE
)
def GetModuleHandleA(lpModuleName):
    return kernel32.GetModuleHandleA(lpModuleName)


@msdn_wrap(
    (wintypes.LPCSTR,),
    wintypes.HANDLE
)
def LoadLibraryA(lpLibFileName):
    return kernel32.LoadLibraryA(lpLibFileName)


@msdn_wrap(
    (wintypes.HANDLE,),
    wintypes.BOOL
)
def CloseHandle(hObject):
    return kernel32.CloseHandle(hObject)


@msdn_wrap(
    (wintypes.HANDLE, LPCTSTR),
    wintypes.LPVOID
)
def GetProcAddress(hModule, lpProcName):
    return kernel32.GetProcAddress(hModule, lpProcName)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.DWORD),
    wintypes.BOOL
)
def TerminateThread(hThread, dwExitCode):
    return kernel32.TerminateThread(hThread, dwExitCode)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.DWORD),
    wintypes.DWORD,
    error_check=False
)
def WaitForSingleObject(hHandle, dwMilliseconds):
    return kernel32.WaitForSingleObject(hHandle, dwMilliseconds)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.LPVOID, SIZE_T, wintypes.DWORD),
    wintypes.BOOL
)
def VirtualFreeEx(hProcess, lpAddress, dwSize, dwFreeType):
    return kernel32.VirtualFreeEx(hProcess, lpAddress, dwSize, dwFreeType)


@msdn_wrap(
    (wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, wintypes.LPDWORD),
    wintypes.BOOL
)
def EnumProcessModules(hProcess, lphModule, cb, lpcbNeeded):
    return psapi.EnumProcessModules(hProcess, lphModule, cb, lpcbNeeded)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.HMODULE, ctypes.c_char_p, wintypes.DWORD),
    wintypes.BOOL
)
def GetModuleBaseNameA(hProcess, hModule, lpBaseName, nSize):
    return psapi.GetModuleBaseNameA(hProcess, hModule, lpBaseName, nSize)


@msdn_wrap(
    (wintypes.HANDLE, LPSECURITY_ATTRIBUTES, SIZE_T, wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD),
    wintypes.HANDLE
)
def CreateRemoteThread(hProcess, lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId):
    return kernel32.CreateRemoteThread(hProcess, lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId)