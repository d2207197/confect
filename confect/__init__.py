
import functools as fnt

from .conf import Conf, ConfProperty
from .error import (ConfGroupExistsError, FrozenConfGroupError,
                    FrozenConfPropError, UnknownConfError)

__all__ = [
    Conf,
    FrozenConfPropError, FrozenConfGroupError,
    UnknownConfError, ConfGroupExistsError
]


@fnt.wraps(Conf.__init__)
def new_conf(*args, **kwargs):
    return Conf(*args, **kwargs)


@fnt.wraps(ConfProperty.__init__)
def property(*args, **kwargs):
    return ConfProperty(*args, **kwargs)


# fnt.update_wrapper(new_conf, Conf.__init__)
# fnt.update_wrapper(, Conf.__init__)
