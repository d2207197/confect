
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

    conf = confect.Conf()

    with conf.declare_group('yo') as g:
        g.some_prop = conf.prop(
            dt.timedelta(days=3), parser=simple_timedelta_parser)


def test_declare_custom_parser2():
    conf = confect.Conf()

    with conf.declare_group('dummy') as cg:
        cg.a_int = 3
        cg.some_string = 'some string'

        cg.color = conf.prop(
            default=Color.RED,
            parser=lambda s: getattr(Color, s.upper())
        )

    assert conf.dummy.a_int == 3
    assert conf.dummy.some_string == 'some string'
    assert conf.dummy.color == Color.RED


@pytest.fixture
def conf():
    conf = confect.Conf()

    with conf.declare_group('dummy') as cg:
        cg.a_int = 3
        cg.a_float = 3.14
        cg.some_bytes = b'oeu'
        cg.some_string = 'some string'
        cg.some_day = dt.date(2018, 8, 3)
        cg.some_time = dt.datetime(2018, 8, 3, 10, 3)
        cg.some_time_tz = dt.datetime(2018, 8, 3, 10, 3, tzinfo=dt.timezone.utc)
        cg.a_list = [1, 3]
        cg.a_tuple = (2, 4)
        cg.a_dict = {'A': 'a', 'B': 'b'}
        cg.some_time_pdl = pdl.datetime(2018, 8, 9, 10, 3, 1)
        cg.some_day_pdl = pdl.date(2018, 8, 9)

        cg.color = conf.prop(
            default=Color.RED,
            parser=lambda s: getattr(Color, s.upper())
        )

    return conf

def test_prop_type(conf):
    assert conf.get_prop('dummy', 'a_int').prop_type == confect.prop_type.Integer()
    assert conf.get_prop('dummy', 'a_float').prop_type == confect.prop_type.Float()
    assert conf.get_prop('dummy', 'some_bytes').prop_type == confect.prop_type.Bytes()
    assert conf.get_prop('dummy', 'some_string').prop_type == confect.prop_type.String()
    assert conf.get_prop('dummy', 'some_day').prop_type == confect.prop_type.Date()
    assert conf.get_prop('dummy', 'some_time').prop_type == confect.prop_type.DateTime()
    assert conf.get_prop('dummy', 'some_time_tz').prop_type == confect.prop_type.DateTime()
    assert conf.get_prop('dummy', 'a_list').prop_type == confect.prop_type.List()
    assert conf.get_prop('dummy', 'a_tuple').prop_type == confect.prop_type.Tuple()
    assert conf.get_prop('dummy', 'a_dict').prop_type == confect.prop_type.Dict()
    assert conf.get_prop('dummy', 'some_time_pdl').prop_type == confect.prop_type.DateTimePDL()
    assert conf.get_prop('dummy', 'some_day_pdl').prop_type == confect.prop_type.DatePDL()

def test_parse_prop(conf):
    assert conf.dummy.a_int == 3
    assert conf.parse_prop('dummy', 'a_int', '32') == 32
    assert conf.parse_prop('dummy', 'some_string', '32') == '32'
    assert conf.parse_prop('dummy', 'some_day',
                           '2017-06-30') == dt.date(2017, 6, 30)
    assert (conf.parse_prop('dummy', 'some_time',
                            '2017-06-30T08:22') ==
            dt.datetime(2017, 6, 30, 8, 22))
    assert (conf.parse_prop('dummy', 'some_time', '2017-06-30T08:22+0800') ==
            pdl.datetime(2017, 6, 30, 8, 22, tz=+8))
    assert conf.parse_prop('dummy', 'color', 'red') == Color.RED


def test_load_envvar(conf):
    assert conf.dummy.a_int == 3
    assert conf.dummy.some_string == 'some string'
    assert conf.dummy.color == Color.RED
    assert conf.dummy.some_day == dt.date(2018, 8, 3)

    os.environ['proj_X__dummy__a_int'] = '15'
    os.environ['proj_X__dummy__some_string'] = 'other string'
    os.environ['proj_X__dummy__color'] = 'green'
    os.environ['proj_X__dummy__some_day'] = '2018-09-03'

    conf.load_envvars('proj_X')

    assert conf.dummy.a_int == 15
    assert conf.dummy.some_string == 'other string'
    assert conf.dummy.color == Color.GREEN
    assert conf.dummy.some_day == dt.date(2018, 9, 3)
