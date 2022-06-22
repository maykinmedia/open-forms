class SingleField:
    """parent class with basic attributes for a single field(form io)"""

    def __init__(self, **kwargs):
        content_dict = kwargs.get("content")
        self.key = content_dict.get("key")
        self.label = content_dict.get("title")
        self.description = content_dict.get("description")
        self.validate = {
            "required": content_dict.get("required"),
            "pattern": content_dict.get("pattern"),
        }
        self.defaultValue = content_dict.get("default")

    @property
    def dict_repr(self):
        return self.__dict__


class TextField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "textfield"
        self.validate.update(
            {
                "maxLength": kwargs.get("maxLength"),
                "minLength": kwargs.get("minLegth"),
            }
        )

    def __str__(self) -> str:
        return "I am an instance of a TexField"


class TextAreaField(SingleField):
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


class DayField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "day"

    def __str__(self) -> str:
        return "I am an instance of a DayType"


class TimeField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "time"

    def __str__(self) -> str:
        return "I am an instance of a TimeType"


class DateTimeField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "datetime"

    def __str__(self) -> str:
        return "I am an instance of a DateTimeType"


class EmailField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "email"


class NumberField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "number"
        is_int = kwargs["content"].get("type")
        self.validate.update(
            {"max": kwargs.get("maximum"), "min": kwargs.get("minimum"), "step": "any"}
        )
        if is_int == "integer":
            self.validate.update({"integer": ""})

        """ formio docs(js)   
        validate: {
        min: '',
        max: '',
        step: 'any',
        integer: ''
        }
        """


# N 1 user (should/can) choose 1 option(true/false) or many from diff oprions
class SelectBoxesField(SingleField):
    # note: extention of Radio component
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


class RadioField(SingleField):
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


class SelectField(SingleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "select"
        self.validate.update(
            {
                "onlyAvailableItems": False,
            }
        )


# class UrlField(SingleField):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.type = "url"

# class PhoneNumberField(SingleField):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.type = "phoneNumber"

# class AddressField(SingleField):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.type = "address"

# class PasswordField(SingleField):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.type = "password"
#         self.validate.update(
#             {"maxLength": kwargs.get("maxLength"), "minLength": kwargs.get("minLength")}        )

#     def __str__(self) -> str:
#         return "I am an instance of a Password"


if __name__ == "__main__":
    pass
