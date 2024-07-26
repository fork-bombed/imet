from imet.server.api import imetapi

with imetapi.create_thread(suspended=True) as hthread:
    print(hthread)
    success = imetapi.resume_thread(hthread)
    print(success)