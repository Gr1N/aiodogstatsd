from typing import Optional

from aiodogstatsd import typedefs

__all__ = ("build", "build_tags")


def build(
    *,
    name: typedefs.MName,
    namespace: Optional[typedefs.MNamespace],
    value: typedefs.MValue,
    type_: typedefs.MType,
    tags: typedefs.MTags,
    sample_rate: typedefs.MSampleRate,
) -> bytes:
    p_name = f"{namespace}.{name}" if namespace is not None else name
    p_sample_rate = f"|@{sample_rate}" if sample_rate != 1 else ""

    p_tags = build_tags(tags)
    p_tags = f"|#{p_tags}" if p_tags else ""

    return f"{p_name}:{value}|{type_.value}{p_sample_rate}{p_tags}".encode("utf-8")


def build_tags(tags: typedefs.MTags) -> str:
    if not tags:
        return ""

    return ",".join(f"{k}:{v}" for k, v in tags.items())
