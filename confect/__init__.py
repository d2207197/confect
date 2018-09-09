
from .conf_ import Conf
from .error import (ConfGroupExistsError, FrozenConfGroupError,
                    FrozenConfPropError, UnknownConfError)

conf = Conf()

__all__ = [
    Conf, conf,
    FrozenConfPropError, FrozenConfGroupError,
    UnknownConfError, ConfGroupExistsError
]
