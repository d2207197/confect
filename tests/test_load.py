import sys

import pytest

from confect import (Conf, ConfGroupExistsError, FrozenConfPropError,
                     UnknownConfError)


def test_load_file(conf, conf1_file):
    with pytest.raises(FileNotFoundError):
        conf.load_file('somewhere/doesnot/exist')

    assert conf.dummy.x == 3
    assert conf.dummy.y == 'some string'
    conf.load_file(conf1_file)
    assert conf.dummy.x == 5
    assert conf.dummy.y == 'other string'


def test_load_multiple_file(conf, conf1_file, conf2_file):
    assert conf.dummy.x == 3
    assert conf.dummy.y == 'some string'
    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'fish'
    assert conf.yummy.weight == 10
    conf.load_file(conf1_file)
    assert conf.dummy.x == 5
    assert conf.dummy.y == 'other string'
    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'fish'
    assert conf.yummy.weight == 10
    conf.load_file(conf2_file)
    assert conf.dummy.x == 6
    assert conf.dummy.y == 'other string'
    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'octopus'
    assert conf.yummy.weight == 10


def test_load_multiple_file2(conf, conf1_file, conf2_file):
    assert conf.dummy.x == 3
    assert conf.dummy.y == 'some string'
    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'fish'
    assert conf.yummy.weight == 10
    conf.load_file(conf2_file)
    assert conf.dummy.x == 6
    assert conf.dummy.y == 'some string'
    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'octopus'
    assert conf.yummy.weight == 10
    conf.load_file(conf1_file)
    assert conf.dummy.x == 5
    assert conf.dummy.y == 'other string'
    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'octopus'
    assert conf.yummy.weight == 10


def test_load_conf_before_declare(conf1_file, conf2_file):
    conf = Conf()
    conf.load_file(conf1_file)

    with pytest.raises(UnknownConfError):
        conf.dummy.x

    with pytest.raises(UnknownConfError):
        conf.dummy.y

    with pytest.raises(UnknownConfError):
        conf.yummy.kind

    with pytest.raises(UnknownConfError):
        conf.yummy.other

    with conf.declare_group('dummy') as g:
        g.x = 3

    assert conf.dummy.x == 5

    with pytest.raises(UnknownConfError):
        conf.dummy.y

    with pytest.raises(ConfGroupExistsError):
        with conf.declare_group('dummy') as g:
            g.y = 'some string'

    with conf.declare_group('yummy') as g:
        g.kind = 'seafood'
        g.name = 'fish'

    assert conf.yummy.kind == 'seafood'
    assert conf.yummy.name == 'fish'


def test_load_module(conf, conf1_file):

    with pytest.raises(ImportError):
        conf.load_module('conf')

    assert conf.dummy.x == 3
    assert conf.dummy.y == 'some string'
    sys.path.append(str(conf1_file.dirpath()))
    conf.load_module('conf1')
    assert conf.dummy.x == 5
    assert conf.dummy.y == 'other string'


def test_declare_group_after_load_conf(conf1_file):
    conf = Conf()
    conf.load_file(conf1_file)

    with pytest.raises(UnknownConfError):
        conf.dummy.x
        conf.dummy.y

    with conf.declare_group('dummy') as dummy:
        dummy.x = 3
        dummy.y = 'some string'

    assert conf.dummy.x == 5
    assert conf.dummy.y == 'other string'

    with pytest.raises(FrozenConfPropError):
        conf.dummy.x = 5
