import logging
from pprint import pprint

from openforms.contrib.ingenico.choices import WebhookEventType
from openforms.contrib.ingenico.client import IngenicoClient
from openforms.contrib.ingenico.models import (
    IngenicoCheckoutStatus,
    IngenicoFormStep,
    IngenicoWebhookEvent,
)
from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)


class IngenicoFormService:
    """
    logic between Forms and Ingenico
    """

    # TODO this is preliminary code

    def __init__(self, client: IngenicoClient = None):
        self.client = client or IngenicoClient()

    def create_submission_checkout(self, submission: Submission, return_url: str):
        step = IngenicoFormStep.objects.get(form_step=submission.form_step)
        checkout, client_info = self.client.create_hosted_checkout(
            step.merchant, return_url
        )
        # associate
        checkout.submission = submission
        checkout.save()
        return checkout, client_info

    def process_form_return(self, checkout_refs: str):
        checkout = self.client.check_hosted_checkout_refs(*checkout_refs)
        if checkout.ingenico_status == IngenicoCheckoutStatus.PAYMENT_CREATED:
            # update submission
            pass
        # what?
        return checkout


class IngenicoFormWebhooks:
    """
    webhooks handler, maps event types to methods
    """

    def __init__(self, client: IngenicoClient = None):
        self.service = IngenicoFormService(client)

    def process_event(self, event: IngenicoWebhookEvent):
        if event.ingenico_type not in WebhookEventType.values:
            logger.warning(f"webhook event with unknown type: {event}")
            return

        hook_method = event.ingenico_type.replace(".", "__")
        if hasattr(self, hook_method):
            logger.info(f"processing webhook event: {event}")
            getattr(self, hook_method)(event)
        else:
            logger.info(f"ignoring unmapped webhook event: {event}")
            logger.info(event.event_data)

    # def payment__create(self, event):
    #     pprint(event.event_data)
    #     raise NotImplemented()
