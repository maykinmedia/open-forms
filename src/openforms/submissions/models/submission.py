from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from django.conf import settings
from django.db import models, transaction
from django.utils.formats import localize
from django.utils.functional import cached_property
from django.utils.timezone import localtime
from django.utils.translation import get_language, gettext_lazy as _

import elasticapm
from django_jsonform.models.fields import ArrayField
from furl import furl
from glom import glom

from openforms.config.models import GlobalConfiguration
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.forms.models import FormRegistrationBackend, FormStep
from openforms.logging.logevent import registration_debug
from openforms.payments.constants import PaymentStatus
from openforms.template import openforms_backend, render_from_string
from openforms.typing import JSONObject, RegistrationBackendKey
from openforms.utils.validators import AllowedRedirectValidator, SerializerValidator

from ..constants import (
    PostSubmissionEvents,
    RegistrationStatuses,
    SubmissionValueVariableSources,
)
from ..pricing import get_submission_price
from ..query import SubmissionManager
from ..serializers import CoSignDataSerializer
from .submission_step import SubmissionStep

if TYPE_CHECKING:
    from openforms.authentication.models import AuthInfo, RegistratorInfo

    from .submission_files import (
        SubmissionFileAttachment,
        SubmissionFileAttachmentQuerySet,
    )
    from .submission_value_variable import SubmissionValueVariablesState

logger = logging.getLogger(__name__)


@dataclass
class SubmissionState:
    form_steps: list[FormStep]
    submission_steps: list[SubmissionStep]

    def _get_step_offset(self):
        completed_steps = sorted(
            [step for step in self.submission_steps if step.completed],
            key=lambda step: step.modified,
        )
        offset = (
            0
            if not completed_steps
            else self.submission_steps.index(completed_steps[-1])
        )
        return offset

    def get_last_completed_step(self) -> SubmissionStep | None:
        """
        Determine the last step that was filled out.

        The last completed step is the step that:
        - is the last submitted step
        - is applicable

        It does not consider "skipped" steps.

        If there are no more steps, the result is None.
        """
        offset = self._get_step_offset()
        candidates = (
            step
            for step in self.submission_steps[offset:]
            if step.completed and step.is_applicable
        )
        return next(candidates, None)

    def get_submission_step(self, form_step_uuid: str) -> SubmissionStep | None:
        return next(
            (
                step
                for step in self.submission_steps
                if str(step.form_step.uuid) == form_step_uuid
            ),
            None,
        )

    def resolve_step(self, form_step_uuid: str) -> SubmissionStep:
        return self.get_submission_step(form_step_uuid=form_step_uuid)


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT)

    # meta information
    form_url = models.URLField(
        _("form URL"),
        max_length=1000,
        blank=False,
        default="",
        help_text=_("URL where the user initialized the submission."),
        validators=[AllowedRedirectValidator()],
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    completed_on = models.DateTimeField(_("completed on"), blank=True, null=True)
    suspended_on = models.DateTimeField(_("suspended on"), blank=True, null=True)

    co_sign_data = models.JSONField(
        _("co-sign data"),
        blank=True,
        default=dict,
        validators=[SerializerValidator(CoSignDataSerializer)],
        help_text=_("Authentication details of a co-signer."),
    )

    # payment state
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        editable=False,
        help_text=_(
            "Cost of this submission. Either derived from the related product, "
            "or evaluated from price logic rules. The price is calculated and saved "
            "on submission completion."
        ),
    )

    # interaction with registration backend
    last_register_date = models.DateTimeField(
        _("last register attempt date"),
        blank=True,
        null=True,
        help_text=_(
            "The last time the submission registration was attempted with the backend.  "
            "Note that this date will be updated even if the registration is not successful."
        ),
    )
    registration_attempts = models.PositiveIntegerField(
        _("registration backend retry counter"),
        default=0,
        help_text=_(
            "Counter to track how often we tried calling the registration backend. "
        ),
    )
    registration_result = models.JSONField(
        _("registration backend result"),
        blank=True,
        null=True,
        help_text=_(
            "Contains data returned by the registration backend while registering the submission data."
        ),
    )
    registration_status = models.CharField(
        _("registration backend status"),
        max_length=50,
        choices=RegistrationStatuses.choices,
        default=RegistrationStatuses.pending,
        help_text=_(
            "Indication whether the registration in the configured backend was successful."
        ),
    )
    pre_registration_completed = models.BooleanField(
        _("pre-registration completed"),
        default=False,
        help_text=_(
            "Indicates whether the pre-registration task completed successfully."
        ),
    )
    public_registration_reference = models.CharField(
        _("public registration reference"),
        max_length=100,
        blank=True,
        help_text=_(
            "The registration reference communicated to the end-user completing the form. "
            "This reference is intended to be unique and the reference the end-user uses "
            "to communicate with the service desk. It should be extracted from the "
            "registration result where possible, and otherwise generated to be unique. "
            "Note that this reference is displayed to the end-user and used as payment "
            "reference!"
        ),
    )
    cosign_complete = models.BooleanField(
        _("cosign complete"),
        default=False,
        help_text=_("Indicates whether the submission has been cosigned."),
    )
    cosign_request_email_sent = models.BooleanField(
        _("cosign request email sent"),
        default=False,
        help_text=_("Has the email to request a co-sign been sent?"),
    )
    cosign_confirmation_email_sent = models.BooleanField(
        _("cosign confirmation email sent"),
        default=False,
        help_text=_(
            "Has the confirmation email been sent after the submission has successfully been cosigned?"
        ),
    )

    confirmation_email_sent = models.BooleanField(
        _("confirmation email sent"),
        default=False,
        help_text=_("Indicates whether the confirmation email has been sent."),
    )

    payment_complete_confirmation_email_sent = models.BooleanField(
        _("payment complete confirmation email sent"),
        default=False,
        help_text=_("Has the confirmation emails been sent after successful payment?"),
    )

    privacy_policy_accepted = models.BooleanField(
        _("privacy policy accepted"),
        default=False,
        help_text=_("Has the user accepted the privacy policy?"),
    )
    cosign_privacy_policy_accepted = models.BooleanField(
        _("cosign privacy policy accepted"),
        default=False,
        help_text=_("Has the co-signer accepted the privacy policy?"),
    )
    statement_of_truth_accepted = models.BooleanField(
        _("statement of truth accepted"),
        default=False,
        help_text=_("Did the user declare the form to be filled out truthfully?"),
    )
    cosign_statement_of_truth_accepted = models.BooleanField(
        _("cosign statement of truth accepted"),
        default=False,
        help_text=_("Did the co-signer declare the form to be filled out truthfully?"),
    )

    _is_cleaned = models.BooleanField(
        _("is cleaned"),
        default=False,
        help_text=_(
            "Indicates whether sensitive data (if there was any) has been removed from this submission."
        ),
    )

    # TODO: Deprecated, replaced by the PostCompletionMetadata model
    on_completion_task_ids = ArrayField(
        base_field=models.CharField(
            _("on completion task ID"),
            max_length=255,
            blank=True,
        ),
        default=list,
        verbose_name=_("on completion task IDs"),
        blank=True,
        help_text=_(
            "Celery task IDs of the on_completion workflow. Use this to inspect the "
            "state of the async jobs."
        ),
    )

    needs_on_completion_retry = models.BooleanField(
        _("needs on_completion retry"),
        default=False,
        help_text=_(
            "Flag to track if the on_completion_retry chain should be invoked. "
            "This is scheduled via celery-beat."
        ),
    )

    # relation to earlier submission which is altered after processing
    previous_submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.SET_NULL, null=True, blank=True
    )

    language_code = models.CharField(
        _("language code"),
        max_length=2,
        default=get_language,
        choices=settings.LANGUAGES,
        help_text=_(
            "The code (RFC5646 format) of the language used to fill in the Form."
        ),
    )

    finalised_registration_backend_key = models.CharField(
        _("final registration backend key"),
        max_length=50,  # FormRegistrationBackend.key.max_length
        default="",
        blank=True,
        help_text=_("The key of the registration backend to use."),
    )

    objects = SubmissionManager()

    _form_login_required: bool | None = None  # can be set via annotation
    _prefilled_data = None
    _total_configuration_wrapper = None

    class Meta:
        verbose_name = _("submission")
        verbose_name_plural = _("submissions")
        constraints = [
            models.UniqueConstraint(
                fields=("public_registration_reference",),
                name="unique_public_registration_reference",
                condition=~models.Q(public_registration_reference=""),
            ),
            models.CheckConstraint(
                check=~(
                    models.Q(registration_status=RegistrationStatuses.success)
                    & models.Q(pre_registration_completed=False)
                ),
                name="registration_status_consistency_check",
            ),
        ]

    def __str__(self):
        return _("{pk} - started on {started}").format(
            pk=self.pk or _("(unsaved)"),
            started=localize(localtime(self.created_on)) or _("(no timestamp yet)"),
        )

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        if hasattr(self, "_execution_state"):
            del self._execution_state

    def save_registration_status(
        self, status: RegistrationStatuses, result: dict
    ) -> None:
        # combine the new result with existing data, where the new result overwrites
        # on key collisions. This allows storing intermediate results in the plugin
        # itself.
        if not self.registration_result and result is None:
            full_result = None
        else:
            full_result = {
                **(self.registration_result or {}),
                **result,
            }
        self.registration_status = status
        self.registration_result = full_result
        update_fields = ["registration_status", "registration_result"]

        if status == RegistrationStatuses.failed:
            self.needs_on_completion_retry = True
            update_fields += ["needs_on_completion_retry"]

        self.save(update_fields=update_fields)

    @property
    def cleaned_form_url(self) -> furl:
        """
        Return the base URL where the form of the submission is/was hosted.

        The SDK itself performs client-side redirects and this URL gets recorded,
        but appointment management/submission resuming relies on the cleaned, canonical
        URL.

        See open-formulieren/open-forms#3025 for the original ticket.

        TODO: check how this works with the hash-based router!
        """
        furl_instance = furl(self.form_url)
        # if the url path ends with 'startpagina', strip it off
        if furl_instance.path.segments[-1:] == ["startpagina"]:
            furl_instance.path.segments.remove("startpagina")
        return furl_instance.remove(
            fragment=True
        )  # Fragments are present in hash based routing

    @property
    def total_configuration_wrapper(self) -> FormioConfigurationWrapper:
        if not self._total_configuration_wrapper:
            state = self.load_execution_state()
            form_steps = state.form_steps
            if len(form_steps) == 0:
                return FormioConfigurationWrapper(configuration={})

            wrapper = FormioConfigurationWrapper(
                form_steps[0].form_definition.configuration
            )
            for form_step in form_steps[1:]:
                wrapper += form_step.form_definition.configuration_wrapper
            self._total_configuration_wrapper = wrapper
        return self._total_configuration_wrapper

    @property
    def form_login_required(self):
        # support annotated fields to save additional queries. Unfortunately,
        # we cannot pass an annotated queryset to use within a select_related field,
        # so instead in our viewset(s) we annotate the submission object.
        #
        # This saves a number of queries, since we can avoid prefetch calls for single
        # objects or form.formstep_set.all() calls on the fly.
        if self._form_login_required is not None:
            return self._form_login_required
        return self.form.login_required

    @property
    def is_authenticated(self):
        return hasattr(self, "auth_info")

    @property
    def registrator(self) -> AuthInfo | RegistratorInfo | None:
        if hasattr(self, "_registrator") and self._registrator:
            return self._registrator
        elif self.is_authenticated:
            return self.auth_info

    @property
    def has_registrator(self):
        return hasattr(self, "_registrator") and self._registrator is not None

    @property
    def is_completed(self):
        return bool(self.completed_on)

    @transaction.atomic()
    def remove_sensitive_data(self):
        from .submission_files import SubmissionFileAttachment

        if self.is_authenticated:
            self.auth_info.clear_sensitive_data()

        sensitive_variables = self.submissionvaluevariable_set.filter(
            form_variable__is_sensitive_data=True
        )
        sensitive_variables.update(
            value="", source=SubmissionValueVariableSources.sensitive_data_cleaner
        )

        SubmissionFileAttachment.objects.filter(
            submission_step__submission=self,
            submission_variable__form_variable__is_sensitive_data=True,
        ).delete()

        self._is_cleaned = True

        if self.co_sign_data:
            # We do keep the representation, as that is used in PDF and confirmation e-mail
            # generation and is usually a label derived from the source fields.
            self.co_sign_data.update(
                {
                    "identifier": "",
                    "fields": {},
                }
            )

        self.save()

    @elasticapm.capture_span(span_type="app.data.loading")
    def load_submission_value_variables_state(
        self, refresh: bool = False
    ) -> SubmissionValueVariablesState:
        if hasattr(self, "_variables_state") and not refresh:
            return self._variables_state

        # circular import
        from .submission_value_variable import SubmissionValueVariablesState

        self._variables_state = SubmissionValueVariablesState(submission=self)
        return self._variables_state

    @elasticapm.capture_span(span_type="app.data.loading")
    def load_execution_state(self, refresh: bool = False) -> SubmissionState:
        """
        Retrieve the current execution state of steps from the database.
        """
        if hasattr(self, "_execution_state") and not refresh:
            return self._execution_state

        form_steps = list(
            self.form.formstep_set.select_related("form_definition").order_by("order")
        )
        # ⚡️ no select_related/prefetch ON PURPOSE - while processing the form steps,
        # we're doing this in python as we have the objects already from the query
        # above.
        _submission_steps = self.submissionstep_set.all()
        submission_steps = {}
        for step in _submission_steps:
            # non-empty value implies that the form_step FK was (cascade) deleted
            if step.form_step_history:
                # deleted formstep FKs are loaded from history
                if step.form_step not in form_steps:
                    form_steps.append(step.form_step)
            submission_steps[step.form_step_id] = step

        # sort the steps again in case steps from history were inserted
        form_steps = sorted(form_steps, key=lambda s: s.order)

        # build the resulting list - some SubmissionStep instances will probably not exist
        # in the database yet - this is on purpose!
        steps: list[SubmissionStep] = []
        for form_step in form_steps:
            if form_step.id in submission_steps:
                step = submission_steps[form_step.id]
                # replace the python objects to avoid extra queries and/or joins in the
                # submission step query.
                step.form_step = form_step
                step.submission = self
            else:
                # there's no known DB record for this, so we create a fresh, unsaved
                # instance and return this
                step = SubmissionStep(uuid=None, submission=self, form_step=form_step)
            steps.append(step)

        state = SubmissionState(
            form_steps=form_steps,
            submission_steps=steps,
        )
        self._execution_state = state
        return state

    def clear_execution_state(self) -> None:
        if not hasattr(self, "_execution_state"):
            return

        for submission_step in self._execution_state.submission_steps:
            submission_step._can_submit = True

        del self._execution_state

    def render_confirmation_page(self) -> str:
        from openforms.variables.utils import get_variables_for_context

        if not (template := self.form.submission_confirmation_template):
            config = GlobalConfiguration.get_solo()
            template = config.submission_confirmation_template

        context_data = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": self,
            "_form": self.form,  # should be the same as self.form
            "public_reference": self.public_registration_reference,
            **get_variables_for_context(submission=self),
        }
        return render_from_string(template, context_data, backend=openforms_backend)

    def render_summary_page(self) -> list[JSONObject]:
        """Use the renderer logic to decide what to display in the summary page.

        The values of the component are returned raw, because the frontend decides how to display them.
        """
        from openforms.formio.rendering.nodes import ComponentNode

        from ..rendering import Renderer, RenderModes
        from ..rendering.nodes import SubmissionStepNode

        renderer = Renderer(submission=self, mode=RenderModes.summary, as_html=False)

        summary_data = []
        current_step = {}
        for node in renderer:
            if isinstance(node, SubmissionStepNode):
                if current_step != {}:
                    summary_data.append(current_step)
                current_step = {
                    "slug": node.step.form_step.slug,
                    "name": node.render(),
                    "data": [],
                }
                continue

            if isinstance(node, ComponentNode):
                current_field = {
                    "name": node.label,
                    "value": node.value,
                    "component": node.component,
                }
                current_step["data"].append(current_field)

        if current_step != {}:
            summary_data.append(current_step)

        return summary_data

    @property
    def steps(self) -> list[SubmissionStep]:
        # fetch the existing DB records for submitted form steps
        submission_state = self.load_execution_state()
        return submission_state.submission_steps

    def get_last_completed_step(self) -> SubmissionStep | None:
        """
        Determine which is the next step for the current submission.
        """
        submission_state = self.load_execution_state()
        return submission_state.get_last_completed_step()

    def get_merged_appointment_data(self) -> dict[str, dict[str, str | dict]]:
        component_config_key_to_appointment_key = {
            "appointments.showProducts": "productIDAndName",
            "appointments.showLocations": "locationIDAndName",
            "appointments.showTimes": "appStartTime",
            "appointments.lastName": "clientLastName",
            "appointments.birthDate": "clientDateOfBirth",
            "appointments.phoneNumber": "clientPhoneNumber",
        }

        merged_data = self.get_merged_data()
        appointment_data = {}

        for component in self.form.iter_components(recursive=True):
            # is this component any of the keys were looking for?
            for (
                component_key,
                appointment_key,
            ) in component_config_key_to_appointment_key.items():
                is_the_right_component = glom(component, component_key, default=False)
                if not is_the_right_component:
                    continue

                # it is the right component, get the value and store it
                appointment_data[appointment_key] = {
                    "label": component["label"],
                    "value": merged_data.get(component["key"]),
                }
                break

        return appointment_data

    def get_merged_data(self) -> dict:
        values_state = self.load_submission_value_variables_state()
        return values_state.get_data()

    data = property(get_merged_data)

    def get_co_signer(self) -> str:
        if not self.co_sign_data:
            return ""
        if not (co_signer := self.co_sign_data.get("representation", "")):
            logger.warning("Incomplete co-sign data for submission %s", self.uuid)
        return co_signer

    def get_attachments(self) -> SubmissionFileAttachmentQuerySet:
        from .submission_files import SubmissionFileAttachment

        return SubmissionFileAttachment.objects.for_submission(self)

    @property
    def attachments(self) -> SubmissionFileAttachmentQuerySet:
        return self.get_attachments()

    def get_merged_attachments(self) -> Mapping[str, list[SubmissionFileAttachment]]:
        if not hasattr(self, "_merged_attachments"):
            self._merged_attachments = self.get_attachments().as_form_dict()
        return self._merged_attachments

    def get_email_confirmation_recipients(self, submitted_data: dict) -> list[str]:
        from openforms.appointments.service import get_email_confirmation_recipients

        # first check if there are any recipients because it's an e-mail form, as that
        # shortcuts the formio component checking (there aren't any)
        if emails := get_email_confirmation_recipients(self):
            return emails

        recipient_emails = set()
        for key in self.form.get_keys_for_email_confirmation():
            value = submitted_data.get(key)
            if value:
                if isinstance(value, str):
                    recipient_emails.add(value)
                elif isinstance(value, list):
                    recipient_emails.update(value)

        return list(recipient_emails)

    def calculate_price(self, save=True) -> None:
        """
        Calculate and save the price of this particular submission.
        """
        logger.debug("Calculating submission %s price", self.uuid)
        if not self.payment_required:
            logger.debug(
                "Submission %s does not require payment, skipping price calculation",
                self.uuid,
            )
            return None

        self.price = get_submission_price(self)
        if save:
            self.save(update_fields=["price"])

    @property
    def payment_required(self) -> bool:
        if not self.form.payment_required:
            return False

        return bool(get_submission_price(self))

    @property
    def payment_user_has_paid(self) -> bool:
        # TODO support partial payments
        return self.payments.filter(
            status__in=(PaymentStatus.registered, PaymentStatus.completed)
        ).exists()

    @property
    def payment_registered(self) -> bool:
        # TODO support partial payments
        return self.payments.filter(status=PaymentStatus.registered).exists()

    def get_auth_mode_display(self):
        # compact anonymous display of authentication method
        if not self.is_authenticated:
            return ""

        return f"{self.auth_info.plugin} ({self.auth_info.attribute})"

    def get_prefilled_data(self):
        if self._prefilled_data is None:
            values_state = self.load_submission_value_variables_state()
            prefill_vars = values_state.get_prefill_variables()
            self._prefilled_data = {
                variable.key: variable.value for variable in prefill_vars
            }
        return self._prefilled_data

    @cached_property
    def cosigner_email(self) -> str | None:
        from openforms.formio.service import iterate_data_with_components

        for form_step in self.form.formstep_set.select_related("form_definition"):
            for component_with_data_item in iterate_data_with_components(
                form_step.form_definition.configuration, self.data
            ):
                if component_with_data_item.component["type"] == "cosign":
                    return glom(
                        self.data, component_with_data_item.data_path, default=None
                    )

    @property
    def waiting_on_cosign(self) -> bool:
        if self.cosign_complete:
            return False

        # Cosign not complete, but required or the component was filled in the form
        if self.form.cosigning_required or self.cosigner_email:
            return True

        return False

    @property
    def default_registration_backend_key(self) -> RegistrationBackendKey | None:
        backends = list(self.form.registration_backends.order_by("id"))
        match len(backends):  # sanity check
            case 1:
                return backends[0].key
            case 0:
                registration_debug(
                    self,
                    extra_data={
                        "message": _("No registration backends defined on form")
                    },
                )
                return None
            case _:
                default = backends[0]
                registration_debug(
                    self,
                    extra_data={
                        "message": _("Multiple backends defined on form"),
                        "backend": {"key": default.key, "name": default.name},
                    },
                )
                return default.key

    @property
    def registration_backend(self) -> FormRegistrationBackend | None:
        if self.finalised_registration_backend_key:
            try:
                return self.form.registration_backends.get(
                    key=self.finalised_registration_backend_key
                )
            except FormRegistrationBackend.DoesNotExist as e:
                registration_debug(
                    self,
                    error=e,
                    extra_data={
                        "message": _(
                            "Unknown registration backend set by form logic. Trying default..."
                        ),
                        "backend": {"key": self.finalised_registration_backend_key},
                    },
                )

        # not/faulty set by logic; fallback to default
        return (
            self.form.registration_backends.get(key=default_key)
            if (default_key := self.default_registration_backend_key)
            else None
        )

    @property
    def post_completion_task_ids(self) -> list[str]:
        """Get the IDs of the tasks triggered when the submission was completed

        Other tasks are triggered later once the submission is cosigned, a payment is made or a retry flow is triggered.
        But to give feedback to the user we only need the first set of triggered tasks.
        """
        result = self.postcompletionmetadata_set.filter(
            trigger_event=PostSubmissionEvents.on_completion
        ).first()
        return result.tasks_ids if result else []
