
import datetime as dt
import os
import re
from enum import Enum

import pendulum as pdl
import pytest

import confect


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


def test_declare_custom_parser1():

    def simple_timedelta_parser(s):
        '''A simple timedelta parser

        It reads a string in '<amount><unit>' format,
        and return timedelta object.

        Available units
        - d: days
        - h: hours
        - m: minutes
        - s: seconds
        - ms: milliseconds

        >>> simple_timedelta_parser('-3d')
        datetime.timedelta(-3)

        >>> simple_timedelta_parser('5h')
        datetime.timedelta(0, 18000)

        '''
        amount, unit = re.fullmatch(r'([+-]?\d+)(\w+)', s).groups()
        amount = int(amount)
        UNIT_MAP = {
            'd': 'days',
            'h': 'hours',
            'm': 'minutes',
            's': 'seconds',
            'ms': 'microseconds'
        }
        unit = UNIT_MAP[unit]

        return dt.timedelta(**{unit: amount})

    conf = confect.new_conf()

    with conf.declare_group('yo') as g:
        g.some_prop = conf.prop(
            dt.timedelta(days=3), simple_timedelta_parser)


def test_declare_custom_parser2():
    conf = confect.new_conf()

    with conf.declare_group('dummy') as cg:
        cg.a_number = 3
        cg.some_string = 'some string'

        cg.color = conf.prop(
            default=Color.RED,
            parser=lambda s: getattr(Color, s.upper())
        )

    assert conf.dummy.a_number == 3
    assert conf.dummy.some_string == 'some string'
    assert conf.dummy.color == Color.RED


@pytest.fixture
def conf():
    conf = confect.new_conf()

    with conf.declare_group('dummy') as cg:
        cg.a_number = 3
        cg.some_string = 'some string'
        cg.some_day = dt.date(2018, 8, 3)
        cg.some_time = dt.datetime(2018, 8, 3, 10, 3, tzinfo=dt.timezone.utc)

        cg.color = conf.prop(
            default=Color.RED,
            parser=lambda s: getattr(Color, s.upper())
        )

    return conf


def test_parse_prop(conf):
    assert conf.dummy.a_number == 3
    assert conf.parse_prop('dummy', 'a_number', '32') == 32
    assert conf.parse_prop('dummy', 'some_string', '32') == '32'
    assert conf.parse_prop('dummy', 'some_day',
                           '2017-06-30') == dt.date(2017, 6, 30)
    assert (conf.parse_prop('dummy', 'some_time',
                            '2017-06-30T08:22') ==
            dt.datetime(2017, 6, 30, 8, 22, tzinfo=dt.timezone.utc))
    assert (conf.parse_prop('dummy', 'some_time', '2017-06-30T08:22+0800') ==
            pdl.datetime(2017, 6, 30, 8, 22, tz=+8))
    assert conf.parse_prop('dummy', 'color', 'red') == Color.RED


def test_load_envvar(conf):
    assert conf.dummy.a_number == 3
    assert conf.dummy.some_string == 'some string'
    assert conf.dummy.color == Color.RED
    assert conf.dummy.some_day == dt.date(2018, 8, 3)

    os.environ['proj_X__dummy__a_number'] = '15'
    os.environ['proj_X__dummy__some_string'] = 'other string'
    os.environ['proj_X__dummy__color'] = 'green'
    os.environ['proj_X__dummy__some_day'] = '2018-09-03'

    conf.load_envvars('proj_X')

    assert conf.dummy.a_number == 15
    assert conf.dummy.some_string == 'other string'
    assert conf.dummy.color == Color.GREEN
    assert conf.dummy.some_day == dt.date(2018, 9, 3)
