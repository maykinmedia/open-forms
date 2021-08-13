import factory

from openforms.forms.models.form import FormLogic


class FormLogicFactory(factory.django.DjangoModelFactory):
    json_logic_trigger = {"==": [1, 1]}
    actions = [{"action": {"type": "disable-next"}}]
    component = "test"

    class Meta:
        model = FormLogic
