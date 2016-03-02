import os
import json
import pytest
from volttrontesting.utils.platformwrapper import PlatformWrapper

PRINT_LOG_ON_SHUTDOWN = True

def print_log(volttron_home):
    if PRINT_LOG_ON_SHUTDOWN:
        with open(volttron_home+"/volttron.log") as fin:
            print(fin.read())


def get_rand_port(ip=None):
    from random import randint
    port = randint(5000, 6000)
    while is_port_open(ip, port):
        port = randint(5000, 6000)
    return port


def is_port_open(ip, port):
    import socket
    if not ip:
        ip = '127.0.0.1'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    return result == 0


@pytest.fixture(scope="module")
def instance1_config():
    port = get_rand_port()
    return {"vip-address": "tcp://127.0.0.1:{}".format(port)}


@pytest.fixture(scope="module")
def instance2_config():
    port = get_rand_port()
    return {"vip-address": "tcp://127.0.0.1:{}".format(port)}


def build_wrapper(vip_address, **kwargs):
    wrapper = PlatformWrapper()
    print('BUILD_WRAPPER: {}'.format(vip_address))
    wrapper.startup_platform(vip_address=vip_address, **kwargs)
    return wrapper


@pytest.fixture(scope="module")
def volttron_instance1(request, instance1_config):
    wrapper = build_wrapper(instance1_config['vip-address'])

    def cleanup():
        print('Shutting down instance: {}'.format(wrapper.volttron_home))
        wrapper.shutdown_platform(True)
    request.addfinalizer(cleanup)
    return wrapper


@pytest.fixture(scope="module")
def volttron_instance2(request, instance2_config):
    print("building instance 2")
    wrapper = build_wrapper(instance2_config['vip-address'])

    def cleanup():
        print('Shutting down instance: {}'.format(wrapper.volttron_home))
        wrapper.shutdown_platform(True)
    request.addfinalizer(cleanup)
    return wrapper


@pytest.fixture(scope="function")
def volttron_instance1_encrypt(request):
    print("building instance 1 (using encryption)")
    address = "tcp://127.0.0.1:{}".format(get_rand_port()) 
    wrapper = build_wrapper(address, encrypt=True)

    def cleanup():
        print('Shutting down instance: {}'.format(wrapper.volttron_home))
        print_log(wrapper.volttron_home)
        wrapper.shutdown_platform(True)
    request.addfinalizer(cleanup)
    return wrapper

@pytest.fixture(scope="function")
def volttron_instance2_encrypt(request):
    print("building instance 2 (using encryption)")
    address = "tcp://127.0.0.1:{}".format(get_rand_port())
    wrapper = build_wrapper(address, encrypt=True)

    def cleanup():
        print('Shutting down instance: {}'.format(wrapper.volttron_home))
        print_log(wrapper.volttron_home)
        wrapper.shutdown_platform(True)
    request.addfinalizer(cleanup)
    return wrapper

@pytest.fixture
def volttron_instance1_web(request):
    print("building instance 1 (using web)")
    address = "tcp://127.0.0.1:{}".format(get_rand_port())
    web_address = "127.0.0.1:{}".format(get_rand_port())
    wrapper = build_wrapper(address, encrypt=True,
                            bind_web_address=web_address)

    def cleanup():
        print('Shutting down instance: {}'.format(wrapper.volttron_home))
        print_log(wrapper.volttron_home)
        wrapper.shutdown_platform(True)
    request.addfinalizer(cleanup)
    return wrapper

@pytest.fixture
def volttron_instance2_web(request):
    print("building instance 2 (using web)")
    address = "tcp://127.0.0.2:{}".format(get_rand_port())
    web_address = "127.0.0.2:{}".format(get_rand_port())
    wrapper = build_wrapper(address, encrypt=True,
                            bind_web_address=web_address)

    def cleanup():
        print('Shutting down instance: {}'.format(wrapper.volttron_home))
        print_log(wrapper.volttron_home)
        wrapper.shutdown_platform(True)
    request.addfinalizer(cleanup)
    return wrapper