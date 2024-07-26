from imet.server.api import winapi
import ctypes
from ctypes import wintypes
import contextlib


class IMETException(Exception):
    def __init__(self, message):
        super().__init__(message)


@contextlib.contextmanager
def open_process(pid: int):
    handle = winapi.OpenProcess(
        winapi.PROCESS_ALL_ACCESS,
        False,
        wintypes.DWORD(pid)
    )
    if not handle:
        raise IMETException(f"OpenProcess failed to retrieve a handle for pid {pid}")
    try:
        yield handle
    finally:
        winapi.CloseHandle(handle)


def get_process_name(handle: int) -> str:
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


def enum_processes():
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