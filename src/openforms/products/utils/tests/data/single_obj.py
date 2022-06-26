myobj = {
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
    "required": ["user"],
}

final = {
    "components": [
        {
            "legend": "Person",
            "key": "fieldSet",
            "type": "fieldset",
            "label": "Field Set",
            "input": False,
            "tableView": False,
            "components": [
                {
                    "label": "First name",
                    "tableView": True,
                    "key": "firstName",
                    "type": "textfield",
                    "input": True,
                },
                {
                    "label": "last name",
                    "tableView": True,
                    "key": "lastName",
                    "type": "textfield",
                    "input": True,
                },
                {
                    "label": "Age",
                    "mask": False,
                    "tableView": False,
                    "delimiter": False,
                    "requireDecimal": False,
                    "inputFormat": "plain",
                    "truncateMultipleSpaces": False,
                    "key": "age",
                    "type": "number",
                    "input": True,
                },
            ],
        },
    ]
}
