from unittest import TestCase

from django.http import HttpRequest

from openforms.contrib.ingenico.client import IngenicoClient, extract_checkout_refs
from openforms.contrib.ingenico.models import IngenicoMerchant


class IngenicoClientTestCase(TestCase):
    def test_refs(self):
        request = HttpRequest()
        request.GET["hostedCheckoutId"] = "foo"
        request.GET["RETURNMAC"] = "bar"
        refs = extract_checkout_refs(request)
        self.assertEqual(
            refs,
            (
                "foo",
                "bar",
            ),
        )

    def test_client(self):
        merchant = IngenicoMerchant()
        # TODO mock request
        # client = IngenicoClient()
        # client.create_hosted_checkout(merchant, 1000, "foo://bar")
