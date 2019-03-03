from typing import Optional

from aiodogstatsd import types

__all__ = ("build", "build_tags")


def build(
    *,
    name: types.MName,
    namespace: Optional[types.MNamespace],
    value: types.MValue,
    type_: types.MType,
    tags: types.MTags,
    sample_rate: types.MSampleRate,
) -> bytes:
    p_name = f"{namespace}.{name}" if namespace is not None else name
    p_sample_rate = f"|@{sample_rate}" if sample_rate != 1 else ""

    p_tags = build_tags(tags)
    p_tags = f"|#{p_tags}" if p_tags else ""

    return f"{p_name}:{value}|{type_.value}{p_sample_rate}{p_tags}".encode("utf-8")


def build_tags(tags: types.MTags) -> str:
    if not tags:
        return ""

    return ",".join(f"{k}={v}" for k, v in tags.items())
