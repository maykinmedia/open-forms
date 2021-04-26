from django.contrib import admin

from .models import IngenicoCheckout, IngenicoMerchant, IngenicoWebhookEvent


@admin.register(IngenicoMerchant)
class IngenicoMerchantAdmin(admin.ModelAdmin):
    fields = [
        "ingenico_merchant_id",
        "label",
        "is_active",
    ]
    list_display = [
        "label",
        "ingenico_merchant_id",
        "is_active",
    ]
    search_fields = [
        "label",
        "ingenico_merchant_id",
    ]
    list_filter = [
        "is_active",
    ]
    ordering = [
        "label",
    ]


@admin.register(IngenicoCheckout)
class IngenicoCheckoutAdmin(admin.ModelAdmin):
    fields = [
        "payment_amount",
        "payment_currency",
        "created_at",
        "checked_at",
        "finalized_at",
        "ingenico_status",
        "ingenico_checkout_id",
        "ingenico_return_mac",
        "ingenico_merchant_reference",
    ]
    readonly_fields = [
        "created_at",
    ]
    list_display = [
        "ingenico_checkout_id",
        "ingenico_status",
        "payment_amount",
        "payment_currency",
        "created_at",
        "checked_at",
        "finalized_at",
    ]
    search_fields = [
        "ingenico_checkout_id",
        "ingenico_return_mac",
        "ingenico_merchant_reference",
    ]
    list_filter = [
        "ingenico_status",
    ]
    ordering = [
        "-pk",
    ]

    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(IngenicoWebhookEvent)
class IngenicoWebhookEventAdmin(admin.ModelAdmin):
    fields = [
        "received_at",
        "ingenico_event_id",
        "ingenico_merchant_id",
        "ingenico_type",
        "event_data",
        "merchant",
    ]
    list_display = [
        "ingenico_event_id",
        "ingenico_type",
        "ingenico_merchant_id",
        "merchant",
    ]
    search_fields = [
        "ingenico_event_id",
        "ingenico_merchant_id",
        "merchant__label",
    ]
    list_filter = [
        "ingenico_type",
        "merchant",
    ]
    ordering = [
        "-pk",
    ]

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
