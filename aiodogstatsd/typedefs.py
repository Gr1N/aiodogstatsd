import enum
from typing import Dict, Union

__all__ = (
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
MTags = Dict[MTagKey, MTagValue]


@enum.unique
class MType(enum.Enum):
    COUNTER = "c"
    DISTRIBUTION = "d"
    GAUGE = "g"
    HISTOGRAM = "h"
    TIMING = "ms"
