from rest_framework import serializers
from rest_framework.test import APISimpleTestCase

start_default = "Start"
previous_default = "Previous"


class POC:
    start_text = "Start override"
    previous_text = ""

    def get_start(self):
        return self.start_text or start_default

    def get_previous(self):
        return self.previous_text or previous_default


class ButtonTextSerializer(serializers.Serializer):
    resolved = serializers.SerializerMethodField()
    value = serializers.CharField()

    def __init__(self, resolved_getter=None, raw_field=None, *args, **kwargs):
        kwargs.setdefault("source", "*")
        self.resolved_getter = resolved_getter
        self.raw_field = raw_field
        super().__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

        if self.resolved_getter is None:
            self.resolved_getter = f"get_{field_name}"

        if self.raw_field is None:
            self.raw_field = field_name

        value_field = self.fields["value"]
        value_field.source = self.raw_field
        value_field.bind(value_field.field_name, self)

    def get_resolved(self, obj):
        return getattr(obj, self.resolved_getter)()


class LiteralsSerializer(serializers.Serializer):
    start = ButtonTextSerializer(raw_field="start_text")
    previous = ButtonTextSerializer(raw_field="previous_text")


class POCSerializer(serializers.Serializer):
    literals = LiteralsSerializer(source="*")


class Tests(APISimpleTestCase):
    def test_output(self):
        poc = POC()

        serializer = POCSerializer(instance=poc)

        expected = {
            "literals": {
                "start": {"resolved": "Start override", "value": "Start override"},
                "previous": {
                    "resolved": "Previous",
                    "value": "",
                },
            }
        }
        self.assertEqual(serializer.data, expected)
