import pytest
from tests.data.example_simples import (
    date_time_schema,
    day_schema,
    email_schema,
    number_schema,
    text_schema,
    textarea_schema,
    time_schema,
)

from src.entry import convert_json_schema_to_py


@pytest.mark.parametrize(
    "schema,expected_output",
    [
        (day_schema, "day"),
        (number_schema, "number"),
        (text_schema, "textfield"),
        (email_schema, "email"),
        (time_schema, "time"),
        (date_time_schema, "datetime"),
        (textarea_schema, "textarea"),
    ],
)
def test_simple(schema, expected_output):
    pass
    assert convert_json_schema_to_py(schema)["components"][0]["type"] == expected_output
