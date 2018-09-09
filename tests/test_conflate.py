import sys
import textwrap

import pytest

from confect import (Conf, FrozenConfGroupError, FrozenConfPropError,
                     UnknownConfError, __version__)


def test_version():
    assert __version__ == '0.1.0'


@pytest.fixture(scope='function')
def dummy_conf():
    the_conf = Conf()
    the_conf.add_group('dummy', x=3, y='some string')
    return the_conf


def test_add_group():
    the_conf = Conf()
    the_conf.add_group('dummy', x=3, y='some string')
    assert the_conf.dummy.x == 3
    assert the_conf.dummy.y == 'some string'

    the_conf = Conf()
    with the_conf.add_group('dummy') as dummy:
        dummy.x = 5
        dummy.y = 6
    assert the_conf.dummy.x == 5


def test_access_conf(dummy_conf):
    assert dummy_conf.dummy.x == 3
    assert dummy_conf.dummy.y == 'some string'


def test_conf_frozen(dummy_conf):
    with pytest.raises(FrozenConfPropError):
        dummy_conf.dummy.x = 5

    with pytest.raises(FrozenConfGroupError):
        dummy_conf.dummy = {'x': 5}


def test_unknown_conf(dummy_conf):
    with pytest.raises(UnknownConfError):
        dummy_conf.dummy.some_prop

    with pytest.raises(UnknownConfError):
        dummy_conf.unknown_group


def test_mutable_env(dummy_conf):
    assert dummy_conf.dummy.x == 3
    with dummy_conf.local_env():
        dummy_conf.dummy.x = 5
        assert dummy_conf.dummy.x == 5
    assert dummy_conf.dummy.x == 3

    with dummy_conf.local_env():
        with pytest.raises(FrozenConfGroupError):
            dummy_conf.dummy = {'y': 4}


@pytest.fixture(scope='session')
def conf_file(tmpdir_factory):
    p = tmpdir_factory.getbasetemp().join('conf.py')
    p.write(textwrap.dedent('''
        from confect import c
        c.dummy.x = 5
        c.dummy.y = 'other string'
        '''))
    print(p.read())
    return p


def test_load_conf_file(dummy_conf, conf_file):
    assert dummy_conf.dummy.x == 3
    assert dummy_conf.dummy.y == 'some string'
    dummy_conf.load_conf_file(conf_file)
    assert dummy_conf.dummy.x == 5
    assert dummy_conf.dummy.y == 'other string'


def test_load_conf_module(dummy_conf, conf_file):
    assert dummy_conf.dummy.x == 3
    assert dummy_conf.dummy.y == 'some string'
    sys.path.append(str(conf_file.dirpath()))
    dummy_conf.load_conf_module('conf')
    assert dummy_conf.dummy.x == 5
    assert dummy_conf.dummy.y == 'other string'
