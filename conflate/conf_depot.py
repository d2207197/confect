

def _get_obj_attr(obj, attr):
    return object.__getattribute__(obj, attr)


class ConfDepot:
    __slots__ = '_depot_groups'

    def __init__(self):
        self._depot_groups = {}

    def __getitem__(self, group_name):
        return self._depot_groups[group_name]

    def __getattr__(self, group_name):
        depot_groups = _get_obj_attr(self, '_depot_groups')

        if group_name not in depot_groups:
            conf_depot_group = ConfDepotGroup()
            depot_groups[group_name] = conf_depot_group
            return conf_depot_group

        return depot_groups[group_name]

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            raise TypeError(
                'Adding property to first level of ConfDepot is forbidding.\n'  # noqa
                'In configuration file, all configuration properties should be in some configuration group.\n'  # noqa
                'Configuration group would be created automatically when needed.\n'  # noqa
                'In the following example, `yummy` is the group name and `kind` is the property name.\n'  # noqa
                '>>> c.yummy.kind = "seafood"'
            )

    def __contains__(self, group_name):
        return group_name in self._depot_groups


from collections import UserDict


class ConfDepotGroup(UserDict):

    def __getitem__(self, group_name):
        return self._depot_properties[group_name]

    def __getattr__(self, group_name):
        depot_properties = _get_obj_attr(self, '_depot_properties')

        if group_name not in depot_properties:
            raise AttributeError(
                f'ConfDepotGroup object has no property {group_name!r}'
            )

        return depot_properties[group_name]

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            self._depot_properties[name] = value
