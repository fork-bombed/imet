"""
Sample name: enum_processes
Description: Enumerate processes using EnumProcess
"""


from imet.server.api import winapi, imetapi, payloads


def emulate():
    processes = imetapi.enum_processes()
    for pid in processes:
        try:
            with imetapi.open_process(pid) as handle:
                process_name = imetapi.get_process_name(handle)
                print(f"[{pid}] {process_name}")
        except:
            pass
