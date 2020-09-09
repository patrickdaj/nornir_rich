import os

from nornir import InitNornir
from nornir.core.state import GlobalState

from nornir_rich.plugins.processors import RichResults

import pytest


global_data = GlobalState()


@pytest.fixture(scope="session", autouse=True)
def nornir(request):
    """Initializes nornir"""
    dir_path = os.path.dirname(os.path.realpath(__file__))

    nornir = InitNornir(config_file=dir_path + '/test_data/config.yaml')
    nornir.data = global_data
    nornir.processors.append(RichResults())
    return nornir


@pytest.fixture(scope="function", autouse=True)
def reset_data():
    global_data.reset_failed_hosts()
