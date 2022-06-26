import pytest

from src.entry import convert_json_schema_to_py

from .data.example_object import user_obj


@pytest.mark.parametrize(
    "schema,expected_output",
    [
        (user_obj, "fieldset"),
    ],
)
def test_simple(schema, expected_output):
    base = convert_json_schema_to_py(schema)["components"]
    assert base[0]["type"] == expected_output
    assert len(base) == 1
    assert len(base[0]["components"]) == 2
    assert base[0]["components"][0]["key"] == "name"
    assert base[0]["components"][1]["key"] == "email"
