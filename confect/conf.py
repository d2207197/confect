import functools as fnt
import importlib
import logging
import os
import weakref
from contextlib import contextmanager
from copy import deepcopy
import warnings


import confect.prop_type
from confect.error import (
    ConfGroupExistsError,
    FrozenConfGroupError,
    FrozenConfPropError,
    UnknownConfError,
    ParameterError,
)

logger = logging.getLogger(__name__)


class Undefined:
    """Undefined value"""

    __instance = None
    __slots__ = ()

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)

        return cls.__instance

    def __bool__(self):
        return False

    def __repr__(self):
        return f"<{__name__}.{type(self).__qualname__}>"

    def __deepcopy__(self, memo):
        return self.__instance


Undefined = Undefined()


class ConfProperty:

    __slots__ = ("_value", "default", "prop_type", "desc")

    def __init__(self, default=Undefined, *, parser=None, desc="", prop_type=None):
        """Create configuration property with details

        >>> import confect
        >>> import datetime as dt
        >>> conf = confect.Conf()

        >>> from enum import Enum
        >>> class Color(Enum):
        ...     RED = 1
        ...     GREEN = 2
        ...     BLUE = 3

        >>> with conf.declare_group('db') as db:
        ...     db.port = 3361
        ...     db.database = 'default'
        ...     db.host = conf.prop(
        ...          default='10.3.14.15',
        ...          desc='hostname of database')
        ...     db.color = conf.prop(
        ...          default=Color.RED,
        ...          prop_type=confect.make_prop_type(
        ...              python_type=Color,
        ...              parser=lambda s: getattr(Color, s.upper())))

        Paramaters
        ----------
        default : Any
            default value
        prop_type : confect.PropertyType
            confect PropretyType for parsing the string from environment
            variable or CLI argument into Python type.
        desc : str
            description
        parser : Callable[[str], ValueType]
            Deprecated.
            parser for construct confect PropertyType automatically

        """
        self.default = default
        self._value = Undefined
        if parser is not None and prop_type is not None:
            raise ParameterError(
                "`prop_type`, `parser` can't be assigned at the same time."
            )

        if parser is not None:
            warnings.warn(
                "`parser` argument of ConfProperty is deprecated.", DeprecationWarning
            )
            prop_type = confect.prop_type.make_prop_type(type(default), parser)
        elif prop_type is not None:
            if not isinstance(prop_type, confect.prop_type.PropertyType):
                raise ValueError(
                    "`prop_type` is not instance of conefct.prop_type.PropertyType."
                )
            prop_type = prop_type
        else:
            prop_type = confect.prop_type.of_value(default)

            if prop_type is None:
                raise ValueError(f"No confect.PropertyType matched: {default!r}")

        self.prop_type = prop_type
        self.desc = desc

    @property
    def value(self):
        if self._value is not Undefined:
            return self._value

        return self.default

    @value.setter
    def value(self, value):
        self._value = value

    def click_callback(self, ctx, param, value):
        if param.default != value:
            self._value = value

    def __repr__(self):
        return (
            f"<{__name__}.{type(self).__qualname__} "
            f"default={self.default!r} value={self._value!r} "
            f"prop_type={self.prop_type}>"
            f"desc={self.desc}"
        )

    def __str__(self):
        return f"{self.desc} [default: {self.default!s}, value: {self.value!s}]"


class Conf:
    """Configuration

    >>> import confect
    >>> conf = confect.Conf()

    Declare new configuration properties with
    ``Conf.declare_group(group_name)``

    >>> with conf.declare_group('dummy') as cg:
    ...     cg.opt1 = 3
    ...     cg.opt2 = 'some string'
    >>> conf.dummy.opt1
    3

    Configurations are immutable

    >>> conf.dummy.opt2 = 'other string'
    Traceback (most recent call last):
        ...
    confect.error.FrozenConfPropError: Configuration properties are frozen.
    Configuration properties can only be changed globally by loading configuration file through ``Conf.load_file()`` and ``Conf.load_module()``.
    And it can be changed locally in the context created by `Conf.mutate_locally()`.

    """  # noqa

    __slots__ = (
        "_is_setting_imported",
        "_is_frozen",
        "_conf_depot",
        "_conf_groups",
        "__weakref__",
    )

    def __init__(self):
        """Create a new confect.Conf object

        >>> import confect
        >>> conf = confect.Conf()

        Declare new configuration properties with
        ``Conf.declare_group(group_name)``

        >>> with conf.declare_group('dummy') as cg:
        ...     cg.opt1 = 3
        ...     cg.opt2 = 'some string'

        >>> conf.dummy.opt1
        3

        """

        from confect.conf_depot import ConfDepot

        self._is_setting_imported = False
        self._is_frozen = True
        self._conf_depot = ConfDepot()
        self._conf_groups = {}

    def declare_group(self, name, **default_properties):
        """Add new configuration group and all property names with default values

        >>> conf = Conf()

        Add new group and properties through context manager

        >>> with conf.declare_group('yummy') as yummy:
        ...     yummy.kind='seafood'
        ...     yummy.name='fish'
        >>> conf.yummy.name
        'fish'

        Add new group and properties through function call

        >>> conf.declare_group('dummy',
        ...                    num_prop=3,
        ...                    str_prop='some string')
        >>> conf.dummy.num_prop
        3
        """
        if name in self._conf_groups:
            raise ConfGroupExistsError(f"configuration group {name!r} already exists")

        with self.mutate_globally():
            group = ConfGroup(self, name)
            self._conf_groups[name] = group
            default_setter_ctx = group._default_setter()
            if default_properties:
                with default_setter_ctx as default_setter:
                    default_setter._update(default_properties)
            else:
                return default_setter_ctx

    def _backup(self):
        return deepcopy(self._conf_groups)

    def _restore(self, conf_groups):
        self._conf_groups = conf_groups

    @contextmanager
    def mutate_locally(self):
        """Return a context manager that makes this Conf mutable temporarily.

        All configuration properties will be restored upon completion of the block.

        >>> conf = Conf()
        >>> with conf.declare_group('yummy') as yummy:
        ...     yummy.kind='seafood'
        ...     yummy.name='fish'
        ...
        >>> with conf.mutate_locally():
        ...     conf.yummy.name = 'octopus'
        ...     print(conf.yummy.name)
        ...
        octopus
        >>> print(conf.yummy.name)
        fish

        """  # noqa
        conf_groups_backup = self._backup()
        with self.mutate_globally():
            yield
        self._restore(conf_groups_backup)

    @contextmanager
    def mutate_globally(self):
        self._is_frozen = False
        yield
        self._is_frozen = True

    @contextmanager
    def _confect_c_ctx(self):
        import confect

        confect.c = self._conf_depot
        yield
        del confect.c

    def __contains__(self, group_name):
        return group_name in self._conf_groups

    def __getitem__(self, group_name):
        if group_name not in self._conf_groups:
            raise UnknownConfError(f"Unknown configuration group {group_name!r}")

        conf_group = self._conf_groups[group_name]

        if group_name in self._conf_depot:
            conf_depot_group = self._conf_depot[group_name]
            conf_group._update_from_conf_depot_group(conf_depot_group)
            del self._conf_depot[group_name]

        return conf_group

    def __getattr__(self, group_name):
        return self[group_name]

    def __setitem__(self, group_name, group):
        raise FrozenConfGroupError(
            "Configuration groups are frozen. "
            "Call `confect.declare_group()` for "
            "registering new configuration group."
        )

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            self[name] = value

    def __dir__(self):
        return object.__dir__(self) + list(self._conf_groups.keys())

    def __deepcopy__(self, memo):
        cls = type(self)
        new_self = cls.__new__(cls)
        new_self._is_setting_imported = self._is_setting_imported
        new_self._is_frozen = self._is_frozen
        new_self._conf_depot = deepcopy(self._conf_depot)
        new_self._conf_groups = deepcopy(self._conf_groups)

        for group in new_self._conf_groups.values():
            group._conf = weakref.proxy(new_self)

        return new_self

    def load_file(self, path):
        """Load python configuration file through file path.

        All configuration groups and properties should be added through ``Conf.declare_group()`` in your source code.
        Otherwise, it won't be accessable even if it is in configuration file.

        >>> conf = Conf()
        >>> conf.load_file('path/to/conf.py')  # doctest: +SKIP

        Configuration file example

        .. code: python

            from confect import c
            c.yammy.kind = 'seafood'
            c.yammy.name = 'fish'
        """  # noqa
        from pathlib import Path

        if not isinstance(path, Path):
            path = Path(path)

        with self.mutate_globally():
            with self._confect_c_ctx():
                exec(path.open("r").read())

    def load_module(self, module_name):
        """Load python configuration file through import.

        The module should be importable either through PYTHONPATH
        or was install as a package.

        All configuration groups and properties should be added through ``Conf.declare_group()`` in your source code.
        Otherwise, it won't be accessable even if it is in configuration file.

        >>> conf = Conf()
        >>> conf.load_model('some.module.name')  # doctest: +SKIP

        Configuration file example

        .. code: python

            from confect import c

            c.yammy.kind = 'seafood'
            c.yammy.name = 'fish'

        """  # noqa
        with self.mutate_globally():
            with self._confect_c_ctx():
                importlib.import_module(module_name)

    def load_envvars(self, prefix):
        """Load python configuration from environment variables

        This function automatically searches environment variable in
        ``<prefix>__<group>__<prop>`` format. Be aware of that all of these
        three identifier are case sensitive. If you have a configuration
        property ``conf.cache.expire_time`` and you call
        ``Conf.load_envvars('proj_X')``. It will set that ``expire_time``
        property to the parsed value of ``proj_X__cache__expire_time``
        environment variable.

        >> conf = confect.Conf()
        >> conf.load_envvars('proj_X')  # doctest: +SKIP

        Parameters
        ----------
        prefix : str
            prefix of environment variables

        """
        prefix = prefix + "__"
        with self.mutate_globally():
            for name, value in os.environ.items():
                if name.startswith(prefix):
                    _, group, prop = name.split("__")
                    value = self.parse_prop(group, prop, value)
                    self._conf_depot[group][prop] = value

    def parse_prop(self, group, prop, string):
        return self[group].parse_prop(prop, string)

    def get_prop(self, group, prop):
        return self[group].get_prop(prop)

    @fnt.wraps(ConfProperty.__init__)
    def prop(self, *args, **kwargs):
        return ConfProperty(*args, **kwargs)

    def _iter_props(self):
        for group_name, group in self._conf_groups.items():
            for prop_name, prop in group._properties.items():
                yield group_name, prop_name, prop

    def click_options(self, cmd_func):
        """Attaches all configurations to the command in
        the `--<group>-<prop>` form."""
        import click

        props = reversed(list(self._iter_props()))

        for group_name, prop_name, prop in props:
            if prop.prop_type is None:
                continue

            cmd_func = click.option(
                f"--{group_name}-{prop_name}",
                default=prop.default,
                callback=prop.click_callback,
                expose_value=False,
                type=prop.prop_type.click_param_type,
                help=prop.desc,
                show_default=True,
            )(cmd_func)

        return cmd_func

    def __repr__(self):
        return (
            f"<{__name__}.{type(self).__qualname__} "
            f"groups={list(self._conf_groups.keys())}>"
        )


class ConfGroupPropertySetter:
    __slots__ = ("_conf_group",)

    def __init__(self, conf_group):
        self._conf_group = conf_group

    def __getattr__(self, property_name):
        return self[property_name]

    def __setattr__(self, property_name, value):
        if property_name in self.__slots__:
            object.__setattr__(self, property_name, value)
        else:
            self[property_name] = value

    def __getitem__(self, property_name):
        return self._conf_group._properties.setdefault(property_name, ConfProperty())

    def __setitem__(self, property_name, default):
        if isinstance(default, ConfProperty):
            conf_prop = default
        else:
            conf_prop = ConfProperty(default)

        self._conf_group._properties[property_name] = conf_prop

    def _update(self, default_properties):
        for p, v in default_properties.items():
            self[p] = v


class ConfGroup:
    __slots__ = ("_conf", "_name", "_properties")

    def __init__(self, conf: Conf, name: str):
        self._conf = weakref.proxy(conf)
        self._name = name
        self._properties = {}

    def __getattr__(self, property_name):
        return self[property_name]

    def __setattr__(self, property_name, value):
        if property_name in self.__slots__:
            object.__setattr__(self, property_name, value)
        else:
            self[property_name] = value

    def __getitem__(self, property_name):
        if property_name not in self._properties:
            raise UnknownConfError(
                f"Unknown {property_name!r} property in "
                f"configuration group {self._name!r}"
            )

        return self._properties[property_name].value

    def __setitem__(self, property_name, value):
        if self._conf._is_frozen:
            raise FrozenConfPropError(
                "Configuration properties are frozen.\n"
                "Configuration properties can only be changed globally by "
                "loading configuration file through "
                "``Conf.load_file()`` and ``Conf.load_module()``.\n"
                "And it can be changed locally in the context "
                "created by `Conf.mutate_locally()`."
            )
        else:
            self._properties[property_name].value = value

    def __dir__(self):
        return self._properties.keys()

    @contextmanager
    def _default_setter(self):
        yield ConfGroupPropertySetter(self)

    def _update_from_conf_depot_group(self, conf_depot_group):
        for conf_property, value in conf_depot_group._items():
            if conf_property in self._properties:
                self._properties[conf_property].value = value

    def __deepcopy__(self, memo):
        cls = type(self)
        new_self = cls.__new__(cls)
        new_self._conf = self._conf  # Don't need to copy conf
        new_self._name = self._name
        new_self._properties = deepcopy(self._properties)
        return new_self

    def get_prop(self, prop):
        return self._properties[prop]

    def parse_prop(self, prop, string):
        return self.get_prop(prop).prop_type.parse(string)

    def as_dict(self):
        return {name: prob.value for name, prob in self._properties.items()}

    def __repr__(self):
        return (
            f"<{__name__}.{type(self).__qualname__} "
            f"{self._name} properties={list(self._properties.keys())}>"
        )
