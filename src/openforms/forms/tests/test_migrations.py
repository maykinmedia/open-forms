from openforms.utils.tests.test_migrations import TestMigrations

from ..api.serializers.logic.action_serializers import LogicComponentActionSerializer
from ..models import Form, FormDefinition, FormLogic, FormStep

CONFIGURATION = {
    "components": [
        {"type": "textfield", "key": "test1"},
        {
            "type": "fieldset",
            "key": "test2",
            "components": [],
            "logic": [
                {
                    "name": "Rule 1",
                    "trigger": {
                        "type": "javascript",  # Not supported, will be skipped
                        "javascript": "result = data['test'];",
                    },
                    "actions": [
                        {
                            "name": "Rule 1 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Hidden",
                                "value": "hidden",
                                "type": "boolean",
                            },
                            "state": True,
                        }
                    ],
                },
                {
                    "name": "Rule 2",
                    "trigger": {
                        "type": "simple",
                        "simple": {
                            "show": True,
                            "when": "test1",
                            "eq": "trigger value",
                        },
                    },
                    "actions": [
                        {
                            "name": "Rule 2 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Hidden",
                                "value": "hidden",
                                "type": "boolean",
                            },
                            "state": False,
                        }
                    ],
                },
                {
                    "name": "Rule 3",
                    "trigger": {
                        "type": "json",
                        "json": {"==": [{"var": "test1"}, "test"]},
                    },
                    "actions": [
                        {
                            "name": "Rule 3 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Required",
                                "value": "validate.required",
                                "type": "boolean",
                            },
                            "state": True,
                        },
                        {
                            "name": "Rule 3 Action 2",
                            "type": "property",
                            "property": {
                                "label": "Disabled",
                                "value": "disabled",
                                "type": "boolean",
                            },
                            "state": True,
                        },
                        {
                            "name": "Rule 3 Action 3",
                            "type": "property",
                            "property": {
                                "label": "Title",
                                "value": "title",  # Not supported, will be skipped
                                "type": "string",
                            },
                            "text": "A new title",
                        },
                    ],
                },
            ],
        },
    ]
}


class ConvertFrontendAdvancedLogicTests(TestMigrations):
    migrate_from = "0002_auto_20210917_1114_squashed_0045_remove_formstep_optional"
    migrate_to = "0046_convert_advanced_logic"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        form_definition = FormDefinition.objects.create(
            name="Definition1",
            slug="definition1",
            configuration=CONFIGURATION,
        )
        form1 = Form.objects.create(name="Form1", slug="form-1")
        form2 = Form.objects.create(name="Form2", slug="form-2")
        FormStep.objects.create(form=form1, form_definition=form_definition, order=1)
        FormStep.objects.create(form=form2, form_definition=form_definition, order=2)
        self.form1 = form1
        self.form2 = form2
        self.form_definition = form_definition

    def test_migrate_logic(self):
        self.assertEqual(2, self.form1.formlogic_set.count())
        self.assertEqual(2, self.form2.formlogic_set.count())

        self.form_definition.refresh_from_db()

        self.assertEqual(
            [], self.form_definition.configuration["components"][1]["logic"]
        )


class FixBrokenConvertedLogicTests(TestMigrations):
    migrate_from = "0046_convert_advanced_logic"
    migrate_to = "0047_fix_broken_converted_rules"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        form = Form.objects.create(name="Form", slug="form")
        rule1 = FormLogic.objects.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test1"}, "trigger value"]},
            actions=[
                # Invalid rule
                {
                    "name": "Rule 1 Action 1",
                    "type": "property",
                    "state": False,
                    "property": {
                        "type": "boolean",
                        "label": "Hidden",
                        "value": "hidden",
                    },
                },
                # Valid rule
                {
                    "action": {
                        "name": "Rule 1 Action 1",
                        "type": "property",
                        "state": False,
                        "property": {
                            "type": "bool",
                            "label": "Hidden",
                            "value": "hidden",
                        },
                    },
                    "component": "test2",
                },
            ],
        )
        rule2 = FormLogic.objects.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test1"}, "test"]},
            actions=[
                # Invalid rule
                {
                    "name": "Rule 2 Action 1",
                    "type": "property",
                    "property": {
                        "value": "validate",
                        "type": "json",
                    },
                    "state": {"required": True},
                }
            ],
        )

        self.form = form
        self.rule1 = rule1
        self.rule2 = rule2

    def test_migrate_logic(self):
        self.assertEqual(2, self.form.formlogic_set.count())

        self.rule1.refresh_from_db()
        self.rule2.refresh_from_db()

        serializer1 = LogicComponentActionSerializer(data=self.rule1.actions, many=True)
        self.assertTrue(serializer1.is_valid())

        serializer2 = LogicComponentActionSerializer(data=self.rule2.actions, many=True)
        self.assertTrue(serializer2.is_valid())


class TestChangeInlineEditSetting(TestMigrations):
    migrate_from = "0047_fix_broken_converted_rules"
    migrate_to = "0048_update_formio_default_setting"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        self.form_definition = FormDefinition.objects.create(
            name="Definition with repeating group",
            slug="definition-with-repeating-group",
            configuration={
                "components": [
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "label": "Repeating Group",
                        "inlineEdit": False,
                        "components": [],
                    }
                ]
            },
        )

    def test_inline_edit_is_true(self):
        self.form_definition.refresh_from_db()

        self.assertTrue(
            self.form_definition.configuration["components"][0]["inlineEdit"]
        )
