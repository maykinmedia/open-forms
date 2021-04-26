import logging
from typing import Tuple, Union

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from ingenico.connect.sdk.domain.definitions.address import Address
from ingenico.connect.sdk.domain.definitions.amount_of_money import AmountOfMoney
from ingenico.connect.sdk.domain.hostedcheckout.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from ingenico.connect.sdk.domain.hostedcheckout.definitions.hosted_checkout_specific_input import (
    HostedCheckoutSpecificInput,
)
from ingenico.connect.sdk.domain.payment.definitions.customer import Customer
from ingenico.connect.sdk.domain.payment.definitions.order import Order
from ingenico.connect.sdk.domain.sessions.session_request import SessionRequest
from ingenico.connect.sdk.factory import Factory
from ingenico.connect.sdk.log.python_communicator_logger import PythonCommunicatorLogger
from ingenico.connect.sdk.webhooks.in_memory_secret_key_store import (
    InMemorySecretKeyStore,
)
from ingenico.connect.sdk.webhooks.web_hooks import Webhooks

from openforms.contrib.ingenico.models import (
    IngenicoCheckout,
    IngenicoCheckoutStatus,
    IngenicoMerchant,
    IngenicoWebhookEvent,
)

logger = logging.getLogger(__name__)


class IngenicoException(Exception):
    pass


class APIException(IngenicoException):
    pass


def extract_checkout_refs(request):
    hosted_checkout_id = request.GET.get("hostedCheckoutId")
    return_hmac = request.GET.get("RETURNMAC")
    if hosted_checkout_id and return_hmac:
        return hosted_checkout_id, return_hmac
    else:
        return None


class IngenicoClient:
    """
    python interface to Ingenico functionality (no Form stuff)
    """

    def __init__(self):
        conf = settings.INGENICO_BACKEND

        self.client = Factory.create_client_from_file(
            conf["config_file"], conf["api_key_id"], conf["api_key_secret"]
        )
        self._webhook_keys = InMemorySecretKeyStore()
        self._webhook_keys.store_secret_key(
            conf["webhook_key_id"], conf["webhook_key_secret"]
        )

        # TODO determine logging parameter
        # TODO verify logging privacy
        self.logger = PythonCommunicatorLogger(logger, 800)
        self.client.enable_logging(self.logger)

    def create_hosted_checkout(
        self, merchant: IngenicoMerchant, payment_amount: int, return_url: str
    ) -> Tuple[IngenicoCheckout, dict]:
        """
        core of a hosted checkout, testable without form stuff
        """
        payment_currency = "EUR"

        # TODO move hardcoded values elsewhere
        hosted_checkout_specific_input = HostedCheckoutSpecificInput()
        hosted_checkout_specific_input.locale = "nl_NL"
        hosted_checkout_specific_input.variant = "testVariant"
        hosted_checkout_specific_input.return_cancel_state = True
        # hosted_checkout_specific_input.show_result_page = True
        hosted_checkout_specific_input.return_url = (
            return_url or "http://localhost:8000/backends/ingenico/dev/proto?return=xxx"
        )
        # TODO limit to popular payment products
        # hosted_checkout_specific_input.paymentProductFilters = PaymentProductFilters.ss

        amount_of_money = AmountOfMoney()
        amount_of_money.amount = payment_amount
        amount_of_money.currency_code = payment_currency

        # TODO figure-out what customer info we want to store
        billing_address = Address()
        billing_address.country_code = "NL"

        customer = Customer()
        customer.billing_address = billing_address
        customer.merchant_customer_id = "1234"

        order = Order()
        order.amount_of_money = amount_of_money
        order.customer = customer

        body = CreateHostedCheckoutRequest()
        body.hosted_checkout_specific_input = hosted_checkout_specific_input
        body.order = order

        # TODO add error handling
        response = (
            self.client.merchant(merchant.ingenico_merchant_id)
            .hostedcheckouts()
            .create(body)
        )
        """
        RETURNMAC 	string
        hostedCheckoutId 	string
        invalidTokens 	array
        merchantReference 	string
        partialRedirectUrl	string
        """
        # store session info
        checkout = IngenicoCheckout.objects.create(
            merchant=merchant,
            payment_amount=payment_amount,
            payment_currency=payment_currency,
            ingenico_checkout_id=response.hosted_checkout_id,
            ingenico_return_mac=response.returnmac,
            ingenico_merchant_reference=response.merchant_reference or "",
        )
        # TODO handle response.invalid_tokens
        pre_url = "https://payment."
        client_info = {
            "redirect_url": f"{pre_url}{response.partial_redirect_url}",
        }
        return checkout, client_info

    def check_hosted_checkout_refs(
        self, hosted_checkout_id: str, return_hmac: str
    ) -> IngenicoCheckout:
        try:
            checkout = IngenicoCheckout.objects.get(
                ingenico_checkout_id=hosted_checkout_id,
                ingenico_return_mac=return_hmac,
            )
        except IngenicoCheckout.DoesNotExist:
            return None
        else:
            return self.check_hosted_checkout(checkout)

    def check_hosted_checkout(self, checkout: IngenicoCheckout) -> IngenicoCheckout:
        if checkout.ingenico_status == IngenicoCheckoutStatus.IN_PROGRESS:
            checkout.checked_at = timezone.now()

            # TODO error handling
            response = (
                self.client.merchant(checkout.merchant.ingenico_merchant_id)
                .hostedcheckouts()
                .get(checkout.ingenico_checkout_id)
            )
            if response.status != IngenicoCheckoutStatus.IN_PROGRESS:
                checkout.ingenico_status = response.status
                checkout.finalized_at = timezone.now()
                if response.status == IngenicoCheckoutStatus.PAYMENT_CREATED:
                    # TODO save more payment data
                    pass

            checkout.save()

        return checkout

    def create_client_session(self, merchant: IngenicoMerchant) -> IngenicoCheckout:
        # TODO handle tokens?
        body = SessionRequest()
        body.tokens = []

        # TODO error handling
        response = (
            self.client.merchant(merchant.ingenico_merchant_id).sessions().create(body)
        )
        # TODO handle response.invalidTokens
        client_info = {
            "clientParams": {
                "assetUrl": response.asset_url,
                "clientApiUrl": response.client_api_url,
                "clientSessionId": response.client_session_id,
                "customerId": response.customer_id,
            }
        }
        return client_info

    def decode_webhook_event_request(
        self, body_str: str, request_headers: dict
    ) -> IngenicoWebhookEvent:
        helper = Webhooks.create_helper(self._webhook_keys)
        # TODO is this JSON data or parsed?
        # TODO error handling
        json_data = helper.unmarshal(body_str, request_headers)
        event = self.create_webhook_event(json_data)
        return event

    def create_webhook_event(
        self, json_data: dict
    ) -> Union[IngenicoWebhookEvent, None]:
        # quick unique check
        if IngenicoWebhookEvent.objects.filter(
            ingenico_event_id=json_data["event_id"]
        ).exists():
            return None

        try:
            merchant = IngenicoMerchant.objects.get(
                ingenico_merchant_id=json_data["merchant_id"]
            )
        except IngenicoMerchant.DoesNotExist:
            # TODO ignore events for unknown merchants? convenient for debugging
            merchant = None

        try:
            event = IngenicoWebhookEvent.objects.create(
                ingenico_event_id=json_data["event_id"],
                ingenico_type=json_data["type"],
                ingenico_merchant_id=json_data["merchant_id"],
                event_data=json_data,
                merchant=merchant,
            )
        except IntegrityError:
            # race condition
            # TODO ideally we want to specifically check for unique constraint errors
            return None
        else:
            return event
