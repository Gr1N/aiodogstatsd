import enum
from typing import Mapping, Union

__all__ = (
    "CState",
    "MName",
    "MNamespace",
    "MType",
    "MValue",
    "MSampleRate",
    "MTagKey",
    "MTagValue",
    "MTags",
)


MName = str
MNamespace = str
MValue = Union[float, int]
MSampleRate = Union[float, int]

MTagKey = str
MTagValue = Union[float, int, str]
MTags = Mapping[MTagKey, MTagValue]


@enum.unique
class MType(enum.Enum):
    COUNTER = "c"
    DISTRIBUTION = "d"
    GAUGE = "g"
    HISTOGRAM = "h"
    TIMING = "ms"


@enum.unique
class CState(enum.IntEnum):
    CONNECTED = enum.auto()
    CLOSING = enum.auto()
    DISCONNECTED = enum.auto()
