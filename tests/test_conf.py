
import pytest

from confect import (Conf, FrozenConfGroupError, FrozenConfPropError,
                     UnknownConfError)


def test_declare_group():
    conf = Conf()
    conf.declare_group('dummy', x=3, y='some string')
    assert conf.dummy.x == 3
    assert conf.dummy.y == 'some string'

    conf = Conf()
    with conf.declare_group('dummy') as dummy:
        dummy.x = 5
        dummy.y = 6
    assert conf.dummy.x == 5


def test_access_conf(conf):
    assert conf.dummy.x == 3
    assert conf.dummy.y == 'some string'


def test_conf_frozen(conf):
    with pytest.raises(FrozenConfPropError):
        conf.dummy.x = 5

    with pytest.raises(FrozenConfGroupError):
        conf.dummy = {'x': 5}

    with pytest.raises(FrozenConfGroupError):
        conf.unknown = {'x': 5}


def test_unknown_conf(conf):
    with pytest.raises(UnknownConfError):
        conf.dummy.some_prop

    with pytest.raises(UnknownConfError):
        conf.unknown_group


def test_mutable_env(conf):
    assert conf.dummy.x == 3
    with conf.mutate_locally():
        conf.dummy.x = 5
        assert conf.dummy.x == 5
    assert conf.dummy.x == 3

    with conf.mutate_locally():
        with pytest.raises(FrozenConfGroupError):
            conf.dummy = {'y': 4}


def test_getitem(conf):
    assert conf.dummy.x == 3
    assert conf['dummy']['x'] == 3


def test_setitem(conf):
    with pytest.raises(FrozenConfPropError):
        conf['dummy']['x'] = 5

    with pytest.raises(FrozenConfGroupError):
        conf['dummy'] = {'x': 5}
