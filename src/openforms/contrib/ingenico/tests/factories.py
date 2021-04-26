import factory
from factory import post_generation

from openforms.contrib.ingenico.choices import WebhookEventType
from openforms.contrib.ingenico.models import (
    IngenicoCheckout,
    IngenicoFormStep,
    IngenicoMerchant,
    IngenicoWebhookEvent,
)
from openforms.forms.models import FormStep


class IngenicoMerchantFactory(factory.django.DjangoModelFactory):
    ingenico_merchant_id = factory.Sequence(lambda n: "%03d" % n)
    label = factory.Faker("company")
    is_active = True

    class Meta:
        model = IngenicoMerchant


class IngenicoFormStepFactory(factory.django.DjangoModelFactory):
    merchant: IngenicoMerchant = factory.SubFactory(IngenicoMerchantFactory)
    form_step: FormStep = factory.SubFactory(FormStep)
    payment_amount = 1000

    class Meta:
        model = IngenicoFormStep


class IngenicoCheckoutFactory(factory.django.DjangoModelFactory):
    merchant: IngenicoMerchant = factory.SubFactory(IngenicoMerchantFactory)
    payment_amount = 1000

    ingenico_checkout_id = factory.Faker("uuid4")
    ingenico_return_mac = factory.Faker("uuid4")
    ingenico_merchant_reference = ""

    class Meta:
        model = IngenicoCheckout


class IngenicoWebhookEventFactory(factory.django.DjangoModelFactory):
    ingenico_event_id = factory.Faker("uuid4")
    ingenico_merchant_id = "0001"
    ingenico_type = WebhookEventType.payment__created

    event_data = dict()

    merchant: IngenicoMerchant = factory.SubFactory(IngenicoMerchantFactory)

    class Meta:
        model = IngenicoWebhookEvent

    @post_generation
    def verify_merchant(obj, create, extracted, **kwargs):
        # TODO this is a bit funky, probably want to add another factory to manage this
        # sanity check generated
        assert (
            not obj.merchant
            or obj.merchant.ingenico_merchant_id == obj.ingenico_merchant_id
        )
        assert (
            not obj.event_data
            or obj.event_data["merchantId"] == obj.ingenico_merchant_id
        )
