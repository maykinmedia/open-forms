import pytest
from src.entry import convert_json_schema_to_py
from tests.data.int_vs_number import (
    integer_schema,
    number_schema,
)


@pytest.mark.parametrize(
    "schema,expected_output",
    [
        (integer_schema, ""),
        (number_schema, None),
    ],
)
def test_compair(schema, expected_output):
    """JSON schema may contain type number and type integer;
    if type == integer corresponding object of formIo will get key "integer"=""
    in validate dict; otherwise this key will not be included.
    """
    assert (
        convert_json_schema_to_py(schema)["components"][0]["validate"].get("integer")
        == expected_output
    )
    
