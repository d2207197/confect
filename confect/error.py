
class UnknownConfError(AttributeError, KeyError):
    pass


class FrozenConfPropError(TypeError):
    pass


class FrozenConfGroupError(TypeError):
    pass


class ConfGroupExistsError(ValueError):
    pass
