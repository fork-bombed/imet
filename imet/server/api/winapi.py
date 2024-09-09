import ctypes
from ctypes import wintypes


kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


SIZE_T = ctypes.c_size_t
LPCTSTR = ctypes.c_char_p
MAX_PATH = 260
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
MEM_DECOMMIT = 0x00004000
MEM_RELEASE = 0x00008000
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40
EXECUTE_IMMEDIATELY = 0x0
PROCESS_ALL_ACCESS = 0x000F0000 | 0x00100000 | 0xFFF
CREATE_SUSPENDED = 0x00000004
CONTEXT_ALL = 0x10007F

TH32CS_SNAPHEAPLIST = 0x00000001
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
TH32CS_SNAPALL = (TH32CS_SNAPHEAPLIST | TH32CS_SNAPPROCESS | TH32CS_SNAPTHREAD | TH32CS_SNAPMODULE)
TH32CS_INHERIT = 0x80000000

THREAD_ALL_ACCESS = 0x001F03FF
THREAD_TERMINATE = 0x0001
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_SET_CONTEXT = 0x0010
THREAD_QUERY_INFORMATION = 0x0040
THREAD_SET_INFORMATION = 0x0020
THREAD_SET_THREAD_TOKEN = 0x0080
THREAD_IMPERSONATE = 0x0100
THREAD_DIRECT_IMPERSONATION = 0x0200


class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD)
    ]


class _SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.LPBOOL)
    ]



LPSECURITY_ATTRIBUTES = ctypes.POINTER(_SECURITY_ATTRIBUTES)
LPTHREAD_START_ROUTINE = ctypes.WINFUNCTYPE(wintypes.DWORD, wintypes.LPVOID)


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


class _CONTEXT(ctypes.Structure):
    _fields_ = [
        ("P1Home", wintypes.DWORD64),
        ("P2Home", wintypes.DWORD64),
        ("P3Home", wintypes.DWORD64),
        ("P4Home", wintypes.DWORD64),
        ("P5Home", wintypes.DWORD64),
        ("P6Home", wintypes.DWORD64),

        ("ContextFlags", wintypes.DWORD),
        ("MxCsr", wintypes.DWORD),

        ("SegCs", wintypes.WORD),
        ("SegDs", wintypes.WORD),
        ("SegEs", wintypes.WORD),
        ("SegFs", wintypes.WORD),
        ("SegGs", wintypes.WORD),
        ("SegSs", wintypes.WORD),
        ("EFlags", wintypes.DWORD),

        # General-purpose registers
        ("Dr0", wintypes.DWORD64),
        ("Dr1", wintypes.DWORD64),
        ("Dr2", wintypes.DWORD64),
        ("Dr3", wintypes.DWORD64),
        ("Dr6", wintypes.DWORD64),
        ("Dr7", wintypes.DWORD64),
        ("Rax", wintypes.DWORD64),
        ("Rcx", wintypes.DWORD64),
        ("Rdx", wintypes.DWORD64),
        ("Rbx", wintypes.DWORD64),
        ("Rsp", wintypes.DWORD64),
        ("Rbp", wintypes.DWORD64),
        ("Rsi", wintypes.DWORD64),
        ("Rdi", wintypes.DWORD64),
        ("R8", wintypes.DWORD64),
        ("R9", wintypes.DWORD64),
        ("R10", wintypes.DWORD64),
        ("R11", wintypes.DWORD64),
        ("R12", wintypes.DWORD64),
        ("R13", wintypes.DWORD64),
        ("R14", wintypes.DWORD64),
        ("R15", wintypes.DWORD64),
        ("Rip", wintypes.DWORD64),

        ("Xmm0", wintypes.M128A * 2),
        ("Xmm1", wintypes.M128A * 2),
        ("Xmm2", wintypes.M128A * 2),
        ("Xmm3", wintypes.M128A * 2),
        ("Xmm4", wintypes.M128A * 2),
        ("Xmm5", wintypes.M128A * 2),
        ("Xmm6", wintypes.M128A * 2),
        ("Xmm7", wintypes.M128A * 2),
        ("Xmm8", wintypes.M128A * 2),
        ("Xmm9", wintypes.M128A * 2),
        ("Xmm10", wintypes.M128A * 2),
        ("Xmm11", wintypes.M128A * 2),
        ("Xmm12", wintypes.M128A * 2),
        ("Xmm13", wintypes.M128A * 2),
        ("Xmm14", wintypes.M128A * 2),
        ("Xmm15", wintypes.M128A * 2),

        ("DebugControl", wintypes.DWORD64),
        ("LastBranchToRip", wintypes.DWORD64),
        ("LastBranchFromRip", wintypes.DWORD64),
        ("LastExceptionToRip", wintypes.DWORD64),
        ("LastExceptionFromRip", wintypes.DWORD64),
    ]


class M128A(ctypes.Structure):
    _fields_ = [
        ("Low", wintypes.ULONGLONG),
        ("High", wintypes.LONGLONG)
    ]


LPCONTEXT = ctypes.POINTER(_CONTEXT)


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
    (wintypes.HANDLE, LPSECURITY_ATTRIBUTES, SIZE_T, wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD),
    wintypes.HANDLE
)
def CreateRemoteThread(hProcess, lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId):
    return kernel32.CreateRemoteThread(hProcess, lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.HMODULE, ctypes.c_char_p, wintypes.DWORD),
    wintypes.BOOL
)
def GetModuleBaseNameA(hProcess, hModule, lpBaseName, nSize):
    return psapi.GetModuleBaseNameA(hProcess, hModule, lpBaseName, nSize)


@msdn_wrap(
    (wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, wintypes.LPDWORD),
    wintypes.BOOL
)
def EnumProcessModules(hProcess, lphModule, cb, lpcbNeeded):
    return psapi.EnumProcessModules(hProcess, lphModule, cb, lpcbNeeded)


@msdn_wrap(
    (ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)),
    wintypes.BOOL
)
def EnumProcesses(lpidProcess, cb, lpcbNeeded):
    return psapi.EnumProcesses(lpidProcess, cb, lpcbNeeded)


@msdn_wrap(
    (LPSECURITY_ATTRIBUTES, SIZE_T, LPTHREAD_START_ROUTINE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)),
    wintypes.HANDLE
)
def CreateThread(lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId):
    return kernel32.CreateThread(lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId)


@msdn_wrap(
    (wintypes.HANDLE,),
    wintypes.DWORD
)
def ResumeThread(hThread):
    return kernel32.ResumeThread(hThread)


@msdn_wrap(
    (wintypes.HANDLE,),
    wintypes.DWORD
)
def SuspendThread(hThread):
    return kernel32.SuspendThread(hThread)


@msdn_wrap(
    (wintypes.HANDLE, LPCONTEXT),
    wintypes.BOOL
)
def GetThreadContext(hThread, lpContext):
    return kernel32.GetThreadContext(hThread, lpContext)


@msdn_wrap(
    (wintypes.HANDLE, LPCONTEXT),
    wintypes.BOOL
)
def SetThreadContext(hThread, lpContext):
    return kernel32.SetThreadContext(hThread, lpContext)


@msdn_wrap(
    (wintypes.DWORD, wintypes.DWORD),
    wintypes.HANDLE
)
def CreateToolhelp32Snapshot(dwFlags, th32ProcessID):
    return kernel32.CreateToolhelp32Snapshot(dwFlags, th32ProcessID)


@msdn_wrap(
    (wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)),
    wintypes.BOOL
)
def Thread32First(hSnapshot, lpte):
    return kernel32.Thread32First(hSnapshot, lpte)


@msdn_wrap(
    (wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)),
    wintypes.BOOL
)
def Thread32Next(hSnapshot, lpte):
    return kernel32.Thread32Next(hSnapshot, lpte)


@msdn_wrap(
    (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD),
    wintypes.HANDLE
)
def OpenThread(dwDesiredAccess, bInheritHandle, dwThreadId):
    return kernel32.OpenThread(dwDesiredAccess, bInheritHandle, dwThreadId)


@msdn_wrap(
    (wintypes.HANDLE, wintypes.LPVOID, SIZE_T, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)),
    wintypes.BOOL
)
def VirtualProtectEx(hProcess, lpAddress, dwSize, flNewProtect, lpflOldProtect):
    return kernel32.VirtualProtectEx(hProcess, lpAddress, dwSize, flNewProtect, lpflOldProtect)
