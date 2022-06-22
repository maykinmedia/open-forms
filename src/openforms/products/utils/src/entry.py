import json
from factory import FieldFactory

# from pprint import pprint

FIELD_TYPE = {"type": FieldFactory}


def get_single_item(content: dict) -> dict:
    """create a new object depending on type of a field"""
    obj = FieldFactory.create(content=content)
    return obj


def convert_json_schema_to_py(json_schema: dict) -> dict:
    """
    reads json schema in json format and return dict of fields objects
    """
    properties = json_schema.get("properties", {})
    final_result = {"components": []}
    for key in properties.keys():
        flag = key in json_schema["required"]
        content = properties[key]
        content.update({"key": key, "required": flag})
        single_field = get_single_item(content=properties[key])
        elem = json.dumps(single_field.dict_repr)
        final_result["components"].append(json.loads(elem))
    return final_result





if __name__ == "__main__":
    pass
