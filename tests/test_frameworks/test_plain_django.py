# coding: utf-8
import time
import pytest

from test_frameworks.common import start_server
from test_frameworks.api_test_functions import *


# Common tests from api_test_function will be tested using django app
@pytest.fixture(scope="module")
def server(request):
    proc = start_server("django")
    request.addfinalizer(proc.exterminate)
    # Wait while server is setting up
    time.sleep(0.5)
    return proc
