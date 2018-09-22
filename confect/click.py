import click


def get_builtin_click_param_type(type_):
    type_to_param_type_map = dict([
        (str, click.STRING),
        (int, click.INT),
        (float, click.FLOAT),
        (bool, click.BOOL)
    ])
    return type_to_param_type_map.get(type_)


def create_click_param_type(name, parser):
    cap_name = name[0].upper() + name[1:]

    def convert(self, value, param, ctx):
        if isinstance(value, str):
            return parser(value)
        return value

    return type(f'{cap_name}ParamType',
                (click.ParamType, ),
                dict(name=name, convert=convert))()


def get_click_param_type(type_, parser, name):
    param_type = get_builtin_click_param_type(type_)
    if param_type is None:
        param_type = create_click_param_type(name, parser)

    return param_type
