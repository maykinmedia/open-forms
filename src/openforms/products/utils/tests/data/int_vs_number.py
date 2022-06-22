integer_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "postcode", "huisnummer", "expired"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {"huisnummer": {"title": "home number", "type": "integer"}},
}


number_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "postcode", "huisnummer", "expired"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "temp": {
            "title": "Temp today",
            "type": "number",
            "description": "Check if it's sunny",
            "examples": [23.5],
        }
    },
}
