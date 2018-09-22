import ast
import datetime as dt
import json

__all__ = ['of_value', 'PropertyType']


class PropertyType():
    def __init__(self, type_, parser, name=None, click_param_type=None):
        self.type_ = type_
        self.parser = parser
        if name is None:
            name = type_.__name__

        self.name = name

        if click_param_type is None:
            try:
                import confect.click
                click_param_type = confect.click.get_click_param_type(
                    type_, parser, name)

            except ModuleNotFoundError as e:
                pass

        self.click_param_type = click_param_type


prop_types = [
    PropertyType(bool, lambda s: bool(ast.literal_eval(s))),
    PropertyType(str, lambda s: s, str),
    PropertyType(int, lambda s: int(s)),
    PropertyType(float, lambda s: float(s)),
    PropertyType(bytes, lambda s: s.encode()),
    PropertyType(tuple, lambda s: tuple(json.load(s))),
    PropertyType(dict, lambda s: json.loads(s)),
    PropertyType(list, lambda s: json.loads(s)),
]

try:
    import pendulum as pdl
    prop_types += [
        PropertyType(dt.datetime, lambda s: pdl.parse(s)),
        PropertyType(dt.date, lambda s: pdl.parse(s).date())
    ]
except ModuleNotFoundError:
    pass


def of_value(value):
    for prop_type in prop_types:
        if isinstance(value, prop_type.type_):
            return prop_type
