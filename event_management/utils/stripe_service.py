import stripe
from django.conf import settings
from decimal import Decimal

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe payments"""

    @staticmethod
    def create_payment_intent(amount, currency='usd', metadata=None):
        """
        Create a Stripe Payment Intent

        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Currency code (default: usd)
            metadata: Dictionary of metadata to attach to the payment intent

        Returns:
            Payment Intent object
        """
        try:
            # Convert amount to cents
            amount_cents = int(Decimal(str(amount)) * 100)

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def confirm_payment_intent(payment_intent_id):
        """
        Confirm a payment intent

        Args:
            payment_intent_id: The Stripe Payment Intent ID

        Returns:
            Confirmed Payment Intent object
        """
        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Retrieve a payment intent

        Args:
            payment_intent_id: The Stripe Payment Intent ID

        Returns:
            Payment Intent object
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def create_refund(charge_id, amount=None, reason=None):
        """
        Create a refund for a charge

        Args:
            charge_id: The Stripe Charge ID
            amount: Amount to refund in dollars (if None, full refund)
            reason: Reason for refund

        Returns:
            Refund object
        """
        try:
            refund_params = {'charge': charge_id}

            if amount:
                refund_params['amount'] = int(Decimal(str(amount)) * 100)

            if reason:
                refund_params['reason'] = reason

            refund = stripe.Refund.create(**refund_params)
            return refund
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def construct_webhook_event(payload, sig_header):
        """
        Construct and verify a webhook event

        Args:
            payload: Request body
            sig_header: Stripe signature header

        Returns:
            Event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise Exception("Invalid signature")
