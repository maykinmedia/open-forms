user_obj = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "person",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["name", "email"],
        }
    },
}
