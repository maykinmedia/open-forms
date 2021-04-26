from datetime import timedelta

from django.contrib.postgres.fields import JSONField
from django.db import models

from openforms.contrib.ingenico.choices import IngenicoCheckoutStatus, WebhookEventType
from openforms.forms.models import Form, FormDefinition, FormStep
from openforms.submissions.models import Submission


class IngenicoMerchantQuerySet(models.QuerySet):
    def get_active_merchant(self, merchant_id):
        return self.get(is_active=True, ingenico_merchant_id=merchant_id)


class IngenicoMerchant(models.Model):
    """
    registration and configuration for each merchant
    """

    ingenico_merchant_id = models.CharField(max_length=8, unique=True)
    label = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    objects = IngenicoMerchantQuerySet.as_manager()

    def __str__(self):
        return f"{self.label} #{self.ingenico_merchant_id}"


class IngenicoFormStep(models.Model):
    """
    the model to connect and configure to a specific form step
    """

    merchant = models.ForeignKey(
        IngenicoMerchant,
        on_delete=models.PROTECT,
    )
    # TODO decide what we want to link this to (FormDefinition? FormStep?)
    form_step = models.ForeignKey(
        FormStep,
        on_delete=models.PROTECT,
    )
    # TODO amount should be maybe be defined in form configurator
    payment_amount = models.IntegerField()

    class Meta:
        abstract = True


class IngenicoCheckout(models.Model):
    merchant = models.ForeignKey(
        IngenicoMerchant,
        on_delete=models.PROTECT,
    )
    # form_step = models.ForeignKey(
    #     IngenicoFormStep, on_delete=models.PROTECT,
    # )
    # # # form = models.ForeignKey(Form, on_delete=models.PROTECT, null=True, blank=True)
    # form_submission = models.ForeignKey(
    #     Submission, on_delete=models.PROTECT,
    # )
    # user = models.ForeignKey(
    #     get_user_model(), on_delete=models.PROTECT, null=True, blank=True,
    # )
    payment_amount = models.IntegerField()
    payment_currency = models.CharField(max_length=8)

    # TODO decide timestamps (related to status? add statuschange model?)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    ingenico_checkout_id = models.CharField(max_length=255)
    ingenico_return_mac = models.CharField(max_length=255, db_index=True)
    ingenico_merchant_reference = models.CharField(
        max_length=255, blank=True, default=""
    )

    ingenico_status = models.CharField(
        max_length=64,
        default=IngenicoCheckoutStatus.IN_PROGRESS,
        choices=IngenicoCheckoutStatus.choices,
    )

    # event_data = JSONField(default=dict, blank=True)

    @property
    def in_progress(self):
        return self.ingenico_status == IngenicoCheckoutStatus.IN_PROGRESS

    @property
    def is_finalized(self):
        return self.ingenico_status != IngenicoCheckoutStatus.IN_PROGRESS

    @property
    def expected_timeout_at(self):
        return self.created_at + timedelta(hours=2)


class IngenicoWebhookEvent(models.Model):
    received_at = models.DateTimeField(auto_now_add=True)

    ingenico_event_id = models.CharField(max_length=255, unique=True)
    ingenico_merchant_id = models.CharField(max_length=64)
    ingenico_type = models.CharField(max_length=64)

    event_data = JSONField(default=dict, blank=True)

    merchant = models.ForeignKey(
        IngenicoMerchant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    @property
    def ingenico_type_label(self):
        try:
            return WebhookEventType.labels[self.ingenico_type]
        except KeyError:
            return "<unknown>"

    def __str__(self):
        return f"{self.ingenico_type} {self.ingenico_merchant_id} '{self.ingenico_event_id}'"
