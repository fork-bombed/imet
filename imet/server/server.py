from imet.server.api import imetapi

with imetapi.open_process(14040) as handle:
    print(handle)

