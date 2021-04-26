from djchoices import ChoiceItem, DjangoChoices


class IngenicoCheckoutStatus(DjangoChoices):
    """
    checkout status names from Ingenico
    """

    IN_PROGRESS = ChoiceItem("IN_PROGRESS")
    PAYMENT_CREATED = ChoiceItem("PAYMENT_CREATED")
    CANCELLED_BY_CONSUMER = ChoiceItem("CANCELLED_BY_CONSUMER")
    CLIENT_NOT_ELIGIBLE = ChoiceItem("CLIENT_NOT_ELIGIBLE_FOR_SELECTED_PAYMENT_PRODUCT")


class WebhookEventType(DjangoChoices):
    """
    from https://epayments.developer-ingenico.com/documentation/webhooks/event-types/
    """

    # payment

    payment__created = ChoiceItem(
        "payment.created",
        "The transaction has been created. This is the initial state once a new payment is created.",
    )
    payment__redirected = ChoiceItem(
        "payment.redirected",
        "The consumer has been redirected to a 3rd party to complete the authentication/payment.",
    )
    payment__pending_payment = ChoiceItem(
        "payment.pending_payment",
        "Instructions have been provided and we are now waiting for the money to come in.",
    )
    payment__account_verified = ChoiceItem(
        "payment.account_verified",
        "The account has been verified using a validation services like 0$ authorization.",
    )
    payment__pending_fraud_approval = ChoiceItem(
        "payment.pending_fraud_approval",
        "The transaction is awaiting approval from you to proceed with the capturing of the funds.",
    )
    payment__authorization_requested = ChoiceItem(
        "payment.authorization_requested",
        "We have requested an authorization against an asynchronous system and is awaiting its response. (This is only applicable to Union Pay and Braspag.)",
    )
    payment__pending_approval = ChoiceItem(
        "payment.pending_approval",
        "There are transactions waiting for your approval.",
    )
    payment__pending_completion = ChoiceItem(
        "payment.pending_completion",
        "There are transactions waiting for you to complete them.",
    )
    payment__pending_capture = ChoiceItem(
        "payment.pending_capture",
        "There are transactions waiting for you to capture them.",
    )
    payment__capture_requested = ChoiceItem(
        "payment.capture_requested",
        "The transaction is in the queue to be captured. (For Cards, this means that the that the transaction has been authorized.)",
    )
    payment__captured = ChoiceItem(
        "payment.captured",
        "The transaction has been captured and we have received online confirmation.",
    )
    payment__paid = ChoiceItem(
        "payment.paid",
        "We have matched the incoming funds to the transaction. This subscription will also deliver payment.paid_increment for additional matched funds after first payment.",
    )
    payment__reversed = ChoiceItem(
        "payment.reversed",
        "The transaction has been reversed.",
    )
    payment__chargeback_notification = ChoiceItem(
        "payment.chargeback_notification",
        "We have received a notification of chargeback and this status informs you that your account will be debited for a particular transaction.",
    )
    payment__chargebacked = ChoiceItem(
        "payment.chargebacked",
        "The transaction has been chargebacked.",
    )
    payment__rejected = ChoiceItem(
        "payment.rejected",
        "The transaction has been rejected.",
    )
    payment__rejected_capture = ChoiceItem(
        "payment.rejected_capture",
        "We or one of our downstream acquirers/providers have rejected the capture request.",
    )
    payment__cancelled = ChoiceItem(
        "payment.cancelled",
        "You have cancelled the transaction.",
    )
    payment__refunded = ChoiceItem(
        "payment.refunded",
        "The transaction has been refunded.",
    )

    # refund

    refund__created = ChoiceItem(
        "refund.created",
        "The refund has been created.",
    )
    refund__pending_approval = ChoiceItem(
        "refund.pending_approval",
        "There are refunds waiting for your approval.",
    )
    refund__rejected = ChoiceItem(
        "refund.rejected",
        "The refund request has been rejected.",
    )
    refund__refund_requested = ChoiceItem(
        "refund.refund_requested",
        "The transaction is in the queue to be refunded.",
    )
    refund__captured = ChoiceItem(
        "refund.captured",
        "The transaction has been captured and we have received online confirmation.",
    )
    refund__refunded = ChoiceItem(
        "refund.refunded",
        "The transaction has been refunded.",
    )
    refund__cancelled = ChoiceItem(
        "refund.cancelled",
        "You have cancelled the refund.",
    )

    # payout

    payout__created = ChoiceItem(
        "payout.created",
        "The payout has been created.",
    )
    payout__pending_approval = ChoiceItem(
        "payout.pending_approval",
        "There are payouts waiting for your approval.",
    )
    payout__rejected = ChoiceItem(
        "payout.rejected",
        "The payout has been rejected.",
    )
    payout__payout_requested = ChoiceItem(
        "payout.payout_requested",
        "The transaction is in the queue to be paid out to the consumer.",
    )
    payout__account_credited = ChoiceItem(
        "payout.account_credited",
        "We have successfully credited the consumer.",
    )
    payout__rejected_credit = ChoiceItem(
        "payout.rejected_credit",
        "The credit to the account of the consumer was rejected by the bank.",
    )
    payout__cancelled = ChoiceItem(
        "payout.cancelled",
        "You have cancelled the payout.",
    )
    payout__reversed = ChoiceItem(
        "payout.reversed",
        "The payout has been reversed.",
    )

    # token

    token__created = ChoiceItem(
        "token.created",
        "The token has been created.",
    )
    token__updated = ChoiceItem(
        "token.updated",
        "The token has been updated.",
    )
    token__expired = ChoiceItem(
        "token.expired",
        "The token references a card that has expired.",
    )
    token__expiring_soon = ChoiceItem(
        "token.expiring_soon",
        "The token references a card that will expire next month.",
    )
    token__deleted = ChoiceItem(
        "token.deleted",
        "The token has been deleted. (The event's token payload will contain only an id.)",
    )

    # dispute

    dispute__draft = ChoiceItem(
        "dispute.draft",
        "Disputes created through the API. Disputes in this state are not automatically processed and require to be submitted via the API to change the state to Created.",
    )

    dispute__created = ChoiceItem(
        "dispute.created",
        "Dispute created with all the necessary details that will be picked up for validation and further processing.",
    )
    dispute__invalid_representment = ChoiceItem(
        "dispute.invalid_representment",
        "The provided details are not sufficient to dispute the chargeback.",
    )
    dispute__send_to_bank = ChoiceItem(
        "dispute.send_to_bank",
        "All provided data in the dispute are send to the acquiring bank.",
    )
    dispute__success = ChoiceItem(
        "dispute.success",
        "Dispute has been decided in your favor.",
    )
    dispute__expired = ChoiceItem(
        "dispute.expired",
        "Dispute has exceeded the time limit for processing and can not be pursued anymore.",
    )
    dispute__cancelled = ChoiceItem(
        "dispute.cancelled",
        "Dispute has been cancelled and won't be processed any further.",
    )
