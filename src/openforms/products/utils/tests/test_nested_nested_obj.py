import pytest

from src.entry import convert_json_schema_to_py

from .data.example_nested_user import user_obj


@pytest.mark.parametrize(
    "schema,expected_output",
    [
        (user_obj, "fieldset"),
    ],
)
def test_nested_nested_usere(schema, expected_output):
    """
    JSON schema describes object of nested user names(first_namelast_name) and email field
    """
    base = convert_json_schema_to_py(schema)["components"]
    assert base[0]["type"] == expected_output
    assert len(base) == 1
    assert len(base[0]["components"]) == 2
    assert base[0]["components"][0]["key"] == "fieldset"
    assert base[0]["components"][0]["type"] == "fieldset"
    assert len(base[0]["components"][0]["components"]) == 2
    assert base[0]["components"][0]["components"][0]["key"] == "last_name"
    assert base[0]["components"][0]["components"][0]["type"] == "textfield"
    assert base[0]["components"][0]["components"][1]["key"] == "first_name"
    assert base[0]["components"][0]["components"][1]["type"] == "textfield"

    assert base[0]["components"][1]["key"] == "email"
    assert base[0]["components"][1]["validate"]["required"] == True
    assert base[0]["components"][1]["type"] == "email"
