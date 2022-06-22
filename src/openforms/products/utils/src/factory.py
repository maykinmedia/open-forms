from formio_classes import (
    DateTimeField,
    DayField,
    EmailField,
    TimeField,
    NumberField,
    SelectBoxesField,    
    TextField,
    TextAreaField,
    RadioField,
    SelectField
)


class StringTypeFactory:
    """create instances matching form io classes based on JSON schema type==string"""

    CLASS_TYPES = {
        "date": DayField,
        "time": TimeField,
        "date-time": DateTimeField,
        "email": EmailField,
    }

    @classmethod
    def create(cls, content):
        """make distinction for string format fields"""
        type_format = content.get("format")
        _class = cls.CLASS_TYPES.get(type_format, None)
        if type_format is not None:
            return _class(**{"content": content})
        else:

            if content.get("maxLength") is not None:
                return TextField(**{"content": content})
            else:
                return TextAreaField(**{"content": content})


class FieldFactory:
    """create instances matching form io classes based on different JSON schema types"""

    CLASS_TYPES = {
        "string": StringTypeFactory,
        "number": NumberField,
        "integer": NumberField,
        "array": SelectBoxesField,
        "boolean": RadioField,# SelectField ?
        # the rest of JSON schema "types":
        # 'null': NullType
        # "duration": DurationType,
        # "hostname": HostnameType,
        # "ipaddress": IpAddressType
        # 'object': DictType,
    }

    @classmethod
    def create(cls, content):
        _type = content.get("type")
        _class = cls.CLASS_TYPES.get(_type, None)
        if _type == "string":
            obj = StringTypeFactory.create(content=content)
        else:
            obj = _class(**{"content": content})
        return obj
