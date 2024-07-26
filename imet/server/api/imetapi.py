from imet.server.api import winapi
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
        print(f"Process handle: {handle}")
        yield handle
    finally:
        print(f"Handle closed: {handle}")
        winapi.CloseHandle(handle)