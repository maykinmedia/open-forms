from django.test import TestCase

from ..choices import IngenicoCheckoutStatus
from ..models import IngenicoMerchant
from .factories import (
    IngenicoCheckoutFactory,
    IngenicoMerchantFactory,
    IngenicoWebhookEventFactory,
)


class IngenicoMerchantTestCase(TestCase):
    def test_model(self) -> None:
        merchant = IngenicoMerchantFactory()
        x = str(merchant)
        self.assertEqual(merchant.is_active, True)

    def test_manager(self):
        merchant = IngenicoMerchantFactory(ingenico_merchant_id="1234")
        IngenicoMerchantFactory(ingenico_merchant_id="0000", is_active=False)

        actual = IngenicoMerchant.objects.get_active_merchant("1234")
        self.assertEqual(actual, merchant)

        with self.assertRaises(IngenicoMerchant.DoesNotExist):
            IngenicoMerchant.objects.get_active_merchant("0000")


class IngenicoCheckoutTestCase(TestCase):
    def test_model(self) -> None:
        checkout = IngenicoCheckoutFactory()
        x = str(checkout)
        self.assertEqual(checkout.ingenico_status, IngenicoCheckoutStatus.IN_PROGRESS)

    def test_status(self) -> None:
        checkout = IngenicoCheckoutFactory(
            ingenico_status=IngenicoCheckoutStatus.IN_PROGRESS
        )
        self.assertEqual(checkout.in_progress, True)
        self.assertEqual(checkout.is_finalized, False)

        checkout = IngenicoCheckoutFactory(
            ingenico_status=IngenicoCheckoutStatus.PAYMENT_CREATED
        )
        self.assertEqual(checkout.in_progress, False)
        self.assertEqual(checkout.is_finalized, True)

        checkout = IngenicoCheckoutFactory(
            ingenico_status=IngenicoCheckoutStatus.CANCELLED_BY_CONSUMER
        )
        self.assertEqual(checkout.in_progress, False)
        self.assertEqual(checkout.is_finalized, True)

        checkout = IngenicoCheckoutFactory(
            ingenico_status=IngenicoCheckoutStatus.CLIENT_NOT_ELIGIBLE
        )
        self.assertEqual(checkout.in_progress, False)
        self.assertEqual(checkout.is_finalized, True)


class IngenicoWebhookEventTestCase(TestCase):
    def test_model(self) -> None:
        merchant = IngenicoMerchantFactory()
        event = IngenicoWebhookEventFactory(
            merchant=merchant, ingenico_merchant_id=merchant.ingenico_merchant_id
        )
        x = str(event)
        x = event.ingenico_type_label
