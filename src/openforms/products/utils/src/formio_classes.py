class Field:
    """parent class with basic attributes for a single field(form io)"""

    def __init__(self, **kwargs):
        content_dict = kwargs.get("content")
        self.key = content_dict.get("key")
        self.label = content_dict.get("title")
        self.description = content_dict.get("description")
        self.validate = {
            "required": content_dict.get("required", False),
            "pattern": content_dict.get("pattern"),
        }
        self.defaultValue = content_dict.get("default")
        self.input = True

    @property
    def dict_repr(self):
        # let op: need to be changed (temp for now)
        return self.__dict__


class FieldSetBase:
    """parent class with basic attributes for a fieldset (form io)"""

    def __init__(self, **kwargs):
        content_dict = kwargs.get("content")
        self.legend = content_dict.get("key").upper()
        self.key = "fieldset"
        self.label = "Field Set"

    @property
    def dict_repr(self):
        # let op: need to be changed (temp for now)
        return self.__dict__


class FieldContainer(FieldSetBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "fieldset"
        self.input = False
        self.components = None
        # self._content = kwargs

    def create_nested_components(self):
        """may be to drill nested structure here?"""

    pass


def __str__(self) -> str:
    return "I am a FieldSet "


class FieldSetBuilder:
    """create an object FieldContainer class and pass content to its method to create nested objects"""

    @classmethod
    def create(cls, content):
        obj = FieldContainer(**{"content": content})
        return obj


class TextField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "textfield"
        self.validate.update(
            {
                "maxLength": kwargs.get("maxLength"),
                "minLength": kwargs.get("minLength"),
            }
        )

    def __str__(self) -> str:
        return "I am an instance of a TexField"


class TextAreaField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "textarea"
        self.validate.update(
            {
                "minWords": None,
                "maxWords": None,
            }
        )

    def __str__(self) -> str:
        return "I am an instance of a TexField"


class DayField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "day"

    def __str__(self) -> str:
        return "I am an instance of a DayType"


class TimeField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "time"

    def __str__(self) -> str:
        return "I am an instance of a TimeType"


class DateTimeField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "datetime"

    def __str__(self) -> str:
        return "I am an instance of a DateTimeType"


class EmailField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "email"


class NumberField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "number"
        is_int = kwargs["content"].get("type")
        self.validate.update(
            {"max": kwargs.get("maximum"), "min": kwargs.get("minimum"), "step": "any"}
        )
        if is_int == "integer":
            self.validate.update({"integer": ""})

        """         
        formio docs(js)   
        validate: {
        min: '',
        max: '',
        step: 'any',
        integer: ''
        } 
        """


# N 1 user (should/can) choose 1 option(true/false) or many from diff oprions
class SelectBoxesField(Field):
    # note: extension of Radio component
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "selectboxes"
        self.validate.update(
            {
                "onlyAvailableItems": None,
                # "minSelectedCount": None,
                # "maxSelectedCount": None,
            }
        )

    def __str__(self) -> str:
        return "I am an instance of a Select boxES "


class RadioField(Field):
    # only one  option(true/false)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "radio"
        self.validate.update(
            {
                "onlyAvailableItems": False,
            }
        )

    def __str__(self) -> str:
        return "I am an instance of a Radio Button"


class SelectField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "select"
        self.validate.update(
            {
                "onlyAvailableItems": False,
            }
        )
