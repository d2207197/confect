import importlib
import logging
import weakref
from contextlib import contextmanager
from copy import deepcopy

from confect.error import (ConfGroupExistsError, FrozenConfGroupError,
                           FrozenConfPropError, UnknownConfError)

logger = logging.getLogger(__name__)


def _get_obj_attr(obj, attr):
    return object.__getattribute__(obj, attr)


class Conf:
    '''Configuration

    >>> conf = Conf()

    Declare new configuration properties with ``Conf.declare_group(group_name)``

    >>> with conf.declare_group('dummy') as dummy:
    ...     dummy.opt1 = 3
    ...     dummy.opt2 = 'some string'
    >>> conf.dummy.opt1
    3

    Configurations are immutable

    >>> conf.dummy.opt2 = 'other string'
    Traceback (most recent call last):
        ...
    confect.error.FrozenConfPropError: Configuration properties are frozen.
    Configuration properties can only be changed globally by loading configuration file through ``Conf.load_conf_file()`` and ``Conf.load_conf_module()``.
    And it can be changed locally in the context created by `Conf.local_env()`.

    '''  # noqa
    __slots__ = ('_is_setting_imported',
                 '_is_frozen',
                 '_conf_depot',
                 '_conf_groups',
                 '__weakref__',
                 )

    def __init__(self):
        from confect.conf_depot import ConfDepot
        self._is_setting_imported = False
        self._is_frozen = True
        self._conf_depot = ConfDepot()
        self._conf_groups = {}

    def declare_group(self, name, **default_properties):
        '''Add new configuration group and all property names with default values

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
        '''
        if name in self._conf_groups:
            raise ConfGroupExistsError(
                f'configuration group {name!r} already exists')

        with self._mutable_conf_ctx():
            group = ConfGroup(weakref.proxy(self), name, default_properties)
            self._conf_groups[name] = group
            if not default_properties:
                return group._default_setter()

    def _backup(self):
        return deepcopy(self._conf_groups)

    def _restore(self, conf_groups):
        self._conf_groups = conf_groups

    @contextmanager
    def local_env(self):
        '''Return a context manager that makes this Conf mutable temporarily.
        All configuration properties will be restored upon completion of the block.

        >>> conf = Conf()
        >>> with conf.declare_group('yummy') as yummy:
        ...     yummy.kind='seafood'
        ...     yummy.name='fish'
        >>> with conf.local_env():
        ...     conf.yummy.name = 'octopus'
        ...     print(conf.yummy.name)
        octopus
        >>> print(conf.yummy.name)
        fish

        '''  # noqa
        conf_groups_backup = self._backup()
        with self._mutable_conf_ctx():
            yield
        self._restore(conf_groups_backup)

    @contextmanager
    def _mutable_conf_ctx(self):
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
        return getattr(self, group_name)

    def __getattr__(self, group_name):
        conf_groups = _get_obj_attr(self, '_conf_groups')
        conf_depot = _get_obj_attr(self, '_conf_depot')
        if group_name not in conf_groups:
            raise UnknownConfError(
                f'Unknown configuration group {group_name!r}')

        conf_group = conf_groups[group_name]

        if group_name in conf_depot:
            conf_depot_group = conf_depot[group_name]
            conf_group._update_from_conf_depot_group(conf_depot_group)
            del conf_depot[group_name]

        return conf_group

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            raise FrozenConfGroupError(
                'Configuration groups are frozen. '
                'Call `confect.declare_group()` for '
                'registering new configuration group.'
            )

    def __dir__(self):
        return self._conf_groups.__dir__()

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

    def load_conf_file(self, path):
        '''Load python configuration file through file path.

        All configuration groups and properties should be added through ``Conf.declare_group()`` in your source code.
        Otherwise, it won't be accessable even if it is in configuration file.

        >>> conf = Conf()
        >>> conf.load_conf_file('path/to/conf.py')  # doctest: +SKIP

        Configuration file example

        .. code: python

            from confect import c
            c.yammy.kind = 'seafood'
            c.yammy.name = 'fish'
        '''  # noqa
        from pathlib import Path
        if not isinstance(path, Path):
            path = Path(path)

        with self._mutable_conf_ctx():
            with self._confect_c_ctx():
                exec(path.open('r').read())

    def load_conf_module(self, module_name):
        '''Load python configuration file through import.
        The module should be importable either through PYTHONPATH
        or was install as a package.

        All configuration groups and properties should be added through ``Conf.declare_group()`` in your source code.
        Otherwise, it won't be accessable even if it is in configuration file.

        >>> conf = Conf()
        >>> conf.load_conf_file('path/to/conf.py')  # doctest: +SKIP

        Configuration file example

        .. code: python

            from confect import c
            c.yammy.kind = 'seafood'
            c.yammy.name = 'fish'

        '''  # noqa
        with self._mutable_conf_ctx():
            with self._confect_c_ctx():
                importlib.import_module(module_name)


class ConfGroupDefaultSetter:
    __slots__ = '_conf_group'

    def __init__(self, conf_group):
        self._conf_group = conf_group

    def __getattr__(self, property_name):
        return getattr(self._conf_group, property_name)

    def __setattr__(self, property_name, value):
        if property_name in self.__slots__:
            object.__setattr__(self, property_name, value)
        else:
            self._conf_group._defaults[property_name] = value


class ConfGroup:
    __slots__ = '_conf', '_name', '_properties', '_is_mutable', '_defaults'

    def __init__(self, conf: Conf, name: str, default_properties: dict):
        self._conf = conf
        self._name = name
        self._is_mutable = False
        self._defaults = deepcopy(default_properties)
        self._properties = {}

    def __getattr__(self, property_name):
        properties = _get_obj_attr(self, '_properties')
        defaults = _get_obj_attr(self, '_defaults')

        if property_name in properties:
            return properties[property_name]
        elif property_name in defaults:
            return defaults[property_name]
        else:
            raise UnknownConfError(
                f'Unknown {property_name!r} property in '
                f'configuration group {self._name!r}')

    def __setattr__(self, property_name, value):
        if property_name in self.__slots__:
            object.__setattr__(self, property_name, value)
        elif self._is_mutable:
            self._properties[property_name] = value
        elif property_name not in self._defaults:
            raise UnknownConfError(
                f'Unknown {property_name!r} property in '
                'configuration group {self.name!r}')
        elif self._conf._is_frozen:
            raise FrozenConfPropError(
                'Configuration properties are frozen.\n'
                'Configuration properties can only be changed globally by '
                'loading configuration file through '
                '``Conf.load_conf_file()`` and ``Conf.load_conf_module()``.\n'
                'And it can be changed locally in the context '
                'created by `Conf.local_env()`.'
            )
        else:
            self._properties[property_name] = value

    def __dir__(self):
        return self._properties.__dir__()

    @contextmanager
    def _mutable_ctx(self):
        self._is_mutable = True
        yield self
        self._is_mutable = False

    @contextmanager
    def _default_setter(self):
        yield ConfGroupDefaultSetter(self)

    def _update_from_conf_depot_group(self, conf_depot_group):
        with self._mutable_ctx():
            for conf_property, value in conf_depot_group._items():
                if conf_property in self._defaults:
                    setattr(self, conf_property, value)

    def __deepcopy__(self, memo):
        cls = type(self)
        new_self = cls.__new__(cls)
        new_self._conf = self._conf  # Don't need to copy conf
        new_self._name = self._name
        new_self._is_mutable = self._is_mutable
        new_self._defaults = deepcopy(self._defaults)
        new_self._properties = deepcopy(self._properties)
        return new_self
