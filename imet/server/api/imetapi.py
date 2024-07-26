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