VERSION = 0.2
HOST = "0.0.0.0"
PORT = 13337



import os


def get_project_root() -> str:
    """
    Returns the absolute path to the root of the project.
    """
    return os.path.abspath(os.path.dirname(__file__))