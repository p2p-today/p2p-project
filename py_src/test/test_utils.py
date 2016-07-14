from __future__ import print_function
from __future__ import absolute_import

import datetime
import os
import random
import sys
import time

from .. import utils

if sys.version_info[0] > 2:
    xrange = range

def test_intersect(iters=200):
    max_val = 2**12 - 1
    for _ in xrange(iters):
        pair1 = sorted([random.randint(0, max_val), random.randint(0, max_val)])
        pair2 = sorted([random.randint(0, max_val), random.randint(0, max_val)])
        cross1 = [pair1[0], pair2[0]]
        cross2 = [pair1[1], pair2[1]]
        if max(cross1) < min(cross2):
            assert utils.intersect(range(*pair1), range(*pair2)) == \
                                list(range(max(cross1), min(cross2)))
        else:
            assert utils.intersect(range(*pair1), range(*pair2)) == []

def test_getUTC(iters=20):
    while iters:
        nowa, nowb = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1), utils.getUTC()
        assert nowa.days * 86400 + nowa.seconds in xrange(nowb-1, nowb+2)  # 1 second error margin
        time.sleep(random.random())
        iters -= 1

def test_lan_ip():
    if sys.platform[:5] in ('linux', 'darwi'):
        lan_ip_validation_linux()
    elif sys.platform[:3] in ('win', 'cyg'):
        lan_ip_validation_windows()
    else:  # pragma: no cover
        raise Exception("Unrecognized patform; don't know what command to test against")

def lan_ip_validation_linux():
    import subprocess
    # command pulled from http://stackoverflow.com/a/13322549
    command = """ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'"""
    if sys.version_info >= (2, 7):
        output = subprocess.check_output(command, universal_newlines=True, shell=True)
    else:  # fix taken from http://stackoverflow.com/a/4814985
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]
    assert utils.get_lan_ip() in output

def lan_ip_validation_windows():
    import subprocess
    # command pulled from http://stackoverflow.com/a/17634009
    command = """for /f "delims=[] tokens=2" %%a in ('ping %computername% -4 -n 1 ^| findstr "["') do (echo %%a)"""
    test_file = open('test.bat', 'w')
    test_file.write(command)
    test_file.close()
    if sys.version_info >= (2, 7):
        output = subprocess.check_output(['test.bat'])
    else:  # fix taken from http://stackoverflow.com/a/4814985
        output = subprocess.Popen(['test.bat'], stdout=subprocess.PIPE).communicate()[0]
    assert utils.get_lan_ip().encode() in output
    os.remove('test.bat')

def test_file_dict(iters=1000):
    d = utils.file_dict()
    for _ in xrange(iters):
        test_key = os.urandom(random.randint(0,17))
        test_val = os.urandom(random.randint(0,17))
        d[test_key] = test_val
        assert d[test_key] == test_val
        assert test_val in d.values()