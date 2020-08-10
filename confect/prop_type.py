import ast
import datetime as dt
import json
from .error import ParseError

__all__ = [
    "of_value",
    "of_type",
    "PropertyType",
    "String",
    "Bytes",
    "Integer",
    "Float",
    "Bool",
    "Date",
    "DateTime",
    "List",
    "Tuple",
    "Dict",
    "DatePDL",
    "DateTimePDL",
    "make_prop_type",
]

from abc import ABC, abstractmethod, abstractproperty

try:
    import click
except ImportError as e:
    pass


class PropertyType(ABC):
    def __new__(cls, *args, **kwargs):
        if args or kwargs:
            return super().__new__(cls)

        # reuse existing PropertyType instance
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    @abstractmethod
    def name(self):
        """Name of this Confect Property Type"""

    @property
    @abstractmethod
    def python_type(self):
        """Python type of this property"""

    @abstractmethod
    def parse(self, s):
        """Parse string from environment variable or CLI argument into Python type

        Parameters
        --------------------
        s : str
            string to parse

        Returns
        --------------------
        Any
            instance of `python_type`
        """

    @classmethod
    def prop_types(cls):
        for prop_type in cls.__subclasses__:
            if hasattr(prop_type, "name"):
                yield prop_type

    _click_param_type_cache = None

    @property
    def click_param_type(self):
        """instance of click.ParamType for parse"""
        if self._click_param_type_cache is None:
            self._click_param_type_cache = self._make_click_param_type()

        return self._click_param_type_cache

    def _make_click_param_type(self):
        cap_name = self.name.capitalize()

        def convert(self_, value, param, ctx):
            if isinstance(value, str):
                return self.parse(value)
            return value

        self._click_param_type = type(
            f"{cap_name}ParamType",
            (click.ParamType,),
            dict(name=self.name, convert=convert),
        )()
        return self._click_param_type

    @classmethod
    def all_prop_type_cls(cls):
        for subcls in cls.__subclasses__():
            if isinstance(subcls.name, str):
                yield subcls
            else:
                yield from subcls.all_prop_type_cls()


class String(PropertyType):
    name = "str"
    python_type = str

    def parse(self, s):
        return s

    @property
    def click_param_type(self):

        return click.STRING


def make_prop_type(python_type, parser):
    name = python_type.__name__.capitalize()

    def parse(self, s):
        return parser(s)

    return type(
        name,
        (PropertyType,),
        {"parse": parse, "name": name, "python_type": python_type},
    )


class Bytes(PropertyType):
    name = "bytes"
    python_type = bytes

    def __init__(self, encoding=None):
        self._encoding = encoding

    def parse(self, s):
        if self._encoding is None:
            return s.encode()
        else:
            return s.encode(self._encoding)


class PythonLiteralParserBase(PropertyType):
    def parse(self, s):
        try:
            value = ast.literal_eval(s)
        except ValueError as exc:
            raise ParseError(
                f'Failed to parse string as {self.python_type!r}: "{s}"'
            ) from exc
        if not isinstance(value, self.python_type):
            raise ParseError(
                f"Parsed value is not instance of {self.python_type!r}: {value!r}"
            )
        return value


class Bool(PropertyType):
    name = "bool"
    python_type = bool

    def parse(self, s):
        if s.lower() in ("1", "t", "true", "y", "yes"):
            return True
        elif s.lower() in ("0", "f", "false", "n", "no"):
            return False
        else:
            raise ParseError(
                f"Bool value should be one of '1', 't', 'true', 'y', 'yes' for True, and '0', 'f', 'false', 'n', 'no' for False: {s!r}"
            )

    @property
    def click_param_type(self):
        return click.BOOL


class Integer(PythonLiteralParserBase):
    name = "int"
    python_type = int

    @property
    def click_param_type(self):
        return click.INT


class Float(PythonLiteralParserBase):
    name = "float"
    python_type = float

    @property
    def click_param_type(self):
        return click.FLOAT


class Tuple(PropertyType):
    name = "tuple"
    python_type = tuple

    def parse(self, s):
        return tuple(json.load(s))


class JsonParserBase(PropertyType):
    def parse(self, s):
        value = json.load(s)
        if not isinstance(value, self.python_type):
            raise ParseError("unable")


class List(JsonParserBase):
    name = "list"
    python_type = list


class Dict(JsonParserBase):
    name = "dict"
    python_type = dict


class Date(PropertyType):
    name = "date"
    python_type = dt.date

    def parse(self, s):
        return dt.datetime.strptime(s, "%Y-%m-%d").date()


class DateTime(PropertyType):
    name = "datetime"
    python_type = dt.datetime

    def parse(self, s):
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        for fmt in formats:
            try:
                return dt.datetime.strptime(s, fmt)
            except ValueError as e:
                continue

        raise ParseError(f"Unable to parse datetime string: {s!r}")


try:
    import pendulum as pdl

    class DatePDL(PropertyType):
        """pendulum.Date"""

        name = "date"
        python_type = pdl.Date

        def parse(self, s):
            return pdl.parse(s).date()

    class DateTimePDL(PropertyType):
        """pendulum.DateTime"""

        name = "datetime"
        python_type = pdl.DateTime

        def parse(self, s):
            return pdl.parse(s)


except ModuleNotFoundError:
    pass


def of_value(value):
    for prop_type_cls in PropertyType.all_prop_type_cls():
        if type(value) == prop_type_cls.python_type:
            return prop_type_cls()


def of_type(python_type):
    for prop_type_cls in PropertyType.all_prop_type_cls():
        if python_type == prop_type_cls.python_type:
            return prop_type_cls()
