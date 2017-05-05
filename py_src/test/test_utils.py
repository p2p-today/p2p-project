from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime
from functools import partial
from os import remove
from random import (random, randint)
from subprocess import check_output
from sys import (platform, version_info)
from time import sleep

from pytest import mark
from typing import (Any, Callable, Dict, Tuple, Union)

from .. import utils

if version_info >= (3, ):
    xrange = range


def identity(in_func, out_func, data):
    # type: (Union[partial, Callable], Union[partial, Callable], Any) -> None
    assert data == out_func(in_func(data))


def try_identity(in_func, out_func, data_gen, iters):
    # type: (Callable, Callable, Callable, int) -> None
    for _ in xrange(iters):
        identity(in_func, out_func, data_gen())


@mark.run(order=1)
def test_pack_value(benchmark, iters=1000):
    # type: (Any, int) -> None
    def data_gen():
        # type: () -> Tuple[Tuple, Dict]
        return (partial(utils.pack_value, 128 // 8), utils.unpack_value,
                randint(0, 2**128 - 1)), {}

    benchmark.pedantic(identity, setup=data_gen, rounds=iters)


@mark.run(order=1)
def test_intersect(benchmark, iters=200):
    # type: (Any, int) -> None
    max_val = 2**12 - 1

    def test(
        pair1,  # type: Tuple[int, int]
        pair2,  # type: Tuple[int, int]
        cross1,  # type: Tuple[int, int]
        cross2  # type: Tuple[int, int]
    ):  # type: (...) -> None
        if max(cross1) < min(cross2):
            assert (utils.intersect(
                range(*pair1),
                range(*pair2)) == tuple(range(max(cross1), min(cross2))))
        else:
            assert utils.intersect(range(*pair1), range(*pair2)) == ()

    def setup():
        # type: () -> Tuple[Tuple, Dict]
        pair1 = sorted((randint(0, max_val), randint(0, max_val)))
        pair2 = sorted((randint(0, max_val), randint(0, max_val)))
        cross1 = (pair1[0], pair2[0])
        cross2 = (pair1[1], pair2[1])
        return (pair1, pair2, cross1, cross2), {}

    benchmark.pedantic(test, setup=setup, rounds=iters)


@mark.run(order=1)
def test_getUTC(iters=20):
    # type: (int) -> None
    while iters:
        nowa, nowb = (datetime.utcnow() - datetime(1970, 1, 1)), utils.getUTC()
        # 1 second error margin
        assert nowa.days * 86400 + nowa.seconds in xrange(nowb - 1, nowb + 2)
        sleep(random())
        iters -= 1


@mark.run(order=1)
def test_lan_ip():
    # type: () -> None
    if platform[:5] in ('linux', 'darwi'):
        lan_ip_validation_linux()
    elif platform[:3] in ('win', 'cyg'):
        lan_ip_validation_windows()
    else:  # pragma: no cover
        raise Exception(
            "Unrecognized patform; don't know what command to test against")


def lan_ip_validation_linux():
    # type: () -> None
    # command pulled from http://stackoverflow.com/a/13322549
    command = ("ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | "
               "grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'")
    output = check_output(command, universal_newlines=True, shell=True)
    assert utils.get_lan_ip() in output


def lan_ip_validation_windows():
    # type: () -> None
    # command pulled from http://stackoverflow.com/a/17634009
    command = ('for /f "delims=[] tokens=2" %%a in (\'ping %computername%'
               ' -4 -n 1 ^| findstr "["\') do (echo %%a)')
    test_file = open('test.bat', 'w')
    test_file.write(command)
    test_file.close()
    output = check_output(['test.bat'])
    assert utils.get_lan_ip().encode() in output
    remove('test.bat')
