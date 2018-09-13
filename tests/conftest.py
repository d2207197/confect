import textwrap

import pytest

from confect import Conf


@pytest.fixture(scope='function')
def conf():
    conf = Conf()

    conf.declare_group(
        'dummy',
        x=3,
        y='some string')

    with conf.declare_group('yummy') as g:
        g.kind = 'seafood'
        g.name = 'fish'
        g.weight = 10
    return conf


@pytest.fixture(scope='session')
def conf1_file(tmpdir_factory):
    p = tmpdir_factory.getbasetemp().join('conf1.py')
    p.write(textwrap.dedent('''
        from confect import c
        c.dummy.x = 5
        c.dummy.y = 'other string'
        '''))
    print(p.read())
    return p


@pytest.fixture(scope='session')
def conf2_file(tmpdir_factory):
    p = tmpdir_factory.getbasetemp().join('conf2.py')
    p.write(textwrap.dedent('''
        from confect import c
        c.dummy.x = 6

        c.yummy.name = 'octopus'
        '''))
    print(p.read())
    return p