import datetime as dt
import json
from collections import OrderedDict

import pendulum as pdl

__all__ = ['of_value', 'register']

TYPE_PARSER_MAP = OrderedDict([
    (str, lambda s: s),
    (int, lambda s: int(s)),
    (float, lambda s: float(s)),
    (bytes, lambda s: s.encode()),
    (dt.datetime, lambda s: pdl.parse(s)),
    (dt.date, lambda s: pdl.parse(s).date()),
    (tuple, lambda s: tuple(json.load(s))),
    (dict, lambda s: json.loads(s)),
    (list, lambda s: json.loads(s)),
])


class register():
    '''A function or decorator to register new parsers for some type

    # >>> from decimal import Decimal

    # >>> @parser.register(Decimal)
    # ... def decimal_parser(s):
    # ...     return Decimal(s)

    # >>> type_parser(Decimal, Decimal)

    # >>> @register
    '''

    def __init__(self, type_, parser=None):
        self.type_ = type_
        if parser is not None:
            TYPE_PARSER_MAP[self.type_] = parser

    def __call__(self, parser):
        TYPE_PARSER_MAP[self.type_] = parser


def of_value(value):
    for type_, parser in TYPE_PARSER_MAP.items():
        if isinstance(value, type_):
            return parser
