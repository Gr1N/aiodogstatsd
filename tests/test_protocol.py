import pytest

from aiodogstatsd import protocol, typedefs


@pytest.mark.parametrize(
    "in_, out",
    (
        (
            {
                "name": "name_1",
                "namespace": None,
                "value": "value_1",
                "type_": typedefs.MType.COUNTER,
                "tags": {},
                "sample_rate": 1,
            },
            b"name_1:value_1|c",
        ),
        (
            {
                "name": "name_2",
                "namespace": "namespace_2",
                "value": "value_2",
                "type_": typedefs.MType.COUNTER,
                "tags": {"tag_key_1": "tag_value_1", "tag_key_2": "tag_value_2"},
                "sample_rate": 0.5,
            },
            b"namespace_2.name_2:value_2|c|@0.5|#tag_key_1=tag_value_1,tag_key_2=tag_value_2",
        ),
    ),
)
def test_build(in_, out):
    assert out == protocol.build(**in_)
