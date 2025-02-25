"""Module with some helpers for tests."""
import os
import sys
import threading
import time
from socket import socket

from pyof.v0x01.common.header import Header
from pyof.v0x01.symmetric.hello import Hello

from kytos.core import Controller
from kytos.core.config import KytosConfig

__all__ = ('do_handshake', 'new_controller', 'new_client',
           'new_handshaked_client')


def do_handshake(client: socket):
    """Get a client socket and do the handshake of it.

    This method receives a client socket that simulates a switch on the
    network and does the OpenFlow handshake process with a running controller
    on the network.

    Args:
        client (socket): a socket object connected to the controller.

    Returns:
        The client with the handshake process done.

    """
    # -- STEP 1: Send Hello message
    client.send(Hello(xid=3).pack())

    # -- STEP 2: Wait for Hello response
    binary_packet = b''
    while len(binary_packet) < 8:
        binary_packet = client.recv(8)
    header = Header()
    header.unpack(binary_packet)

    # -- STEP 3: Wait for features_request message
    binary_packet = b''
    # len() < 8 here because we just expect a Hello as response
    while len(binary_packet) < 8:
        binary_packet = client.recv(8)
    header = Header()
    header.unpack(binary_packet)

    # -- STEP 4: Send features_reply to the controller
    basedir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(basedir, 'raw')
    message = None
    with open(os.path.join(raw_dir, 'features_reply.cap'), 'rb') as file:
        message = file.read()
    client.send(message)

    return client


def get_config():
    """Exclude unittest args from Config argparser."""
    argv_backup = None
    # If cli command was like "python -m unittest"
    if sys.argv[0].split()[-1] == 'unittest':
        argv_backup = sys.argv
        sys.argv = sys.argv[:1]
    config = KytosConfig()
    if argv_backup:
        # Recover original argv
        sys.argv = argv_backup
    return config


def new_controller(options=None):
    """Instantiate a Kytos Controller.

    Args:
        options (KytosConfig.options): options generated by KytosConfig

    Returns:
        controller: Running Controler

    """
    if options is None:
        options = get_config().options['daemon']
    controller = Controller(options)
    controller.start()
    time.sleep(0.1)
    return controller


def new_client(options=None):
    """Create and returns a socket client.

    Args:
        options (KytosConfig.options): options generated by KytosConfig

    Returns:
        client (socket): Client connected to the Kytos controller before
            handshake

    """
    if options is None:
        options = get_config().options['daemon']
    client = socket()
    client.connect((options.listen, options.port))
    return client


def new_handshaked_client(options=None):
    """Create and returns a socket client.

    Args:
        options (KytosConfig.options): options generated by KytosConfig

    Returns:
        client (socket): Client connected to the Kytos controller with
            handshake done

    """
    if options is None:
        options = get_config().options['daemon']
    client = new_client(options)
    return do_handshake(client)


def test_concurrently(times):
    """
    Decorator to test concurrently many times.

    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.

    E.g., some views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.
    E.g.:
        def test_method(self):
        from tests.helpers import test_concurrently
        @test_concurrently(10)
        def toggle_call_your_method_here():
            print('This is a test')

        toggle_call_your_method_here()
    """
    def test_concurrently_decorator(test_func):
        """Decorator thread execution."""
        def wrapper(*args, **kwargs):
            """Thread wrapper."""
            exceptions = []

            def call_test_func():
                """Call the test method."""
                try:
                    test_func(*args, **kwargs)
                except Exception as _e:
                    exceptions.append(_e)
                    raise
            threads = []
            for _ in range(times):
                threads.append(threading.Thread(target=call_test_func))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            if exceptions:
                raise Exception("test_concurrently intercepted "
                                f"{len(exceptions)} exceptions: {exceptions}")
        return wrapper
    return test_concurrently_decorator
