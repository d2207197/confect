

import datetime as dt
import re

import confect


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
        g.some_prop = confect.property(
            dt.timedelta(days=3), simple_timedelta_parser)


def test_declare_custom_parser2():
    conf = confect.new_conf()

    from enum import Enum

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    with conf.declare_group('dummy') as cg:
        cg.a_number = 3
        cg.some_string = 'some string'

        cg.color = confect.property(
            default=Color.RED,
            parser=lambda s: getattr(Color, s.upper())
        )

    assert conf.dummy.a_number == 3
    assert conf.dummy.some_string == 'some string'
    assert conf.dummy.color == Color.RED


def test_parse_arg():
    pass
