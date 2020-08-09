
class UnknownConfError(AttributeError, KeyError):
    pass


class FrozenConfPropError(TypeError):
    pass


class FrozenConfGroupError(TypeError):
    pass


class ConfGroupExistsError(ValueError):
    pass

class ParameterError(Exception):
    pass

class ParseError(Exception):
    pass
