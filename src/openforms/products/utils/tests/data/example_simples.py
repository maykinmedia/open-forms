day_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "expired"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "expired": {
            "title": "End",
            "type": "string",
            "format": "date",
            "description": "Date of expire",
        }
    },
}
time_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": [],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "lunch": {
            "title": "My be lunch?",
            "type": "string",
            "format": "time",
            "description": "To lunch or not to lunch",
            "default": "11:30",
        }
    },
}
date_time_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": [],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "birthday": {
            "title": "Birthday",
            "type": "string",
            "format": "date-time",
            "description": "Are you really sure you remember it?",
            "default": "1900-00-00,11:30",
        }
    },
}
text_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "postcode", "huisnummer", "expired"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "kenteken": {
            "title": "Kenteken",
            "type": "string",
            "pattern": "^[A-Z0-9][A-Z0-9]?[A-Z0-9]?-[A-Z0-9][A-Z0-9]?[A-Z0-9]?-[A-Z0-9][A-Z0-9]?[A-Z0-9]?$",
            "description": "Kenteken van het voertuig waarvoor de aanvraag wordt gedaan.",
            "maxLength": 250,
            "examples": ["XX-11-YY"],
        }
    },
}
textarea_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "postcode", "huisnummer", "expired"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "kenteken": {
            "title": "Kenteken",
            "type": "string",
            "pattern": "^[A-Z0-9][A-Z0-9]?[A-Z0-9]?-[A-Z0-9][A-Z0-9]?[A-Z0-9]?-[A-Z0-9][A-Z0-9]?[A-Z0-9]?$",
            "description": "Kenteken van het voertuig waarvoor de aanvraag wordt gedaan.",
            "examples": ["XX-11-YY"],
        }
    },
}
number_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "postcode", "huisnummer", "expired"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {"huisnummer": {"title": "home number", "type": "number"}},
}
email_schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "required": ["kenteken", "postcode", "huisnummer", "expired", "email"],
    "title": "Het objecttype Melding Openbare Ruimte",
    "properties": {
        "email": {"title": "Your email", "type": "string", "format": "email"}
    },
}
