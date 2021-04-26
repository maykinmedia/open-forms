from pprint import pprint

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import RedirectView, TemplateView

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.contrib.ingenico.client import extract_checkout_refs
from openforms.contrib.ingenico.models import IngenicoMerchant
from openforms.contrib.ingenico.service import (
    IngenicoClient,
    IngenicoFormService,
    IngenicoFormWebhooks,
)


class IngenicoProtoDevView(TemplateView):
    """
    temporary development view
    """

    template_name = "ingenico/proto-dev.html"

    def get(self, request, *args, **kwargs):

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        checkout_refs = extract_checkout_refs(self.request)
        if checkout_refs:
            # TODO use the forms wrapper ..
            # service = IngenicoFormService()
            # checkout = service.process_form_return(*checkout_refs)
            # TODO .. but for now go lower level
            client = IngenicoClient()
            checkout = client.check_hosted_checkout_refs(*checkout_refs)
            if checkout:
                kwargs["payment_status"] = checkout.ingenico_status
            else:
                kwargs["payment_status"] = "unknown"

        return super().get_context_data(**kwargs)


class ReturnFromCheckoutAPIView(APIView):
    """
    page customer get redirect to to after hosted checkout

    we process the passed references, update the submission and redirect back to the form
    """

    def get(self, request, *args, form_ref, **kwargs):
        # TODO implement clean redirect
        checkout_refs = extract_checkout_refs(self.request)
        if checkout_refs:
            service = IngenicoFormService()
            checkout = service.process_form_return(*checkout_refs)
            url = service.get_url_for_checkout(checkout)
        else:
            url = "/???"
        raise NotImplementedError()
        return redirect(url)


class CreateCheckoutAPIView(APIView):
    authentication_classes = []

    # TODO serializers
    # TODO transactions
    # TODO error handling
    def post(self, request):
        # TODO this should be something like:
        # service = IngenicoFormService()
        # checkout, client_info = service.create_submission_checkout()

        client = IngenicoClient()
        # params = CheckoutDeserializer(request.data)
        params = request.data
        pprint(request.data)

        merchant = IngenicoMerchant.objects.get_active_merchant("1161")

        # TODO we probably don't want to use a client supplied return url
        checkout, client_info = client.create_hosted_checkout(
            merchant, 1000, params["return_url"]
        )
        pprint(client_info)
        return Response(client_info)


class ClientSessionAPIView(APIView):
    """
    mostly for dev/debugging, remove later
    """

    def post(self, request):
        client = IngenicoClient()
        merchant = IngenicoMerchant.objects.get_active_merchant("1161")
        checkout, client_info = client.create_client_session(merchant)
        return Response(client_info)


class WebhookAPIView(APIView):
    # TODO serializers
    # TODO transactions
    # TODO error handling
    def post(self, request):
        client = IngenicoClient()
        # store raw event
        event = client.store_webhook_event_request(request.body, request.headers)
        # handle event
        if event:
            hooks = IngenicoFormWebhooks(client)
            hooks.process_event(event)
            return HttpResponse("ok")
        else:
            return HttpResponse("duplicate")
