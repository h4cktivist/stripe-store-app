import stripe

from django.conf import settings
from apps.orders.models import Order


class StripeServiceError(Exception):
    pass


class StripeService:
    @staticmethod
    def _get_keys(currency: str) -> dict:
        currency = currency.lower()

        if currency not in settings.STRIPE_KEYS:
            raise StripeServiceError(
                f'Stripe is not configured for currency "{currency}"'
            )

        return settings.STRIPE_KEYS[currency]

    @classmethod
    def create_checkout_session(cls, order: Order) -> stripe.checkout.Session:
        if order.status != Order.Status.DRAFT:
            raise StripeServiceError('Only draft orders can be paid')

        keys = cls._get_keys(order.currency)
        stripe.api_key = keys['secret']

        line_items = [
            {
                'price_data': {
                    'currency': order.currency,
                    'product_data': {
                        'name': item.item.name,
                        'description': item.item.description,
                    },
                    'unit_amount': item.item.price_in_cents,
                },
                'quantity': item.quantity,
            }
            for item in order.items.select_related('item')
        ]

        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=line_items,
            discounts=cls._build_discounts(order),
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
            metadata={
                'order_id': order.id,
            },
        )

        return session

    @staticmethod
    def _build_discounts(order: Order) -> list:
        discounts = []

        for discount in order.discounts.all():
            if discount.type == discount.Type.PERCENT:
                coupon = stripe.Coupon.create(
                    percent_off=float(discount.value),
                    duration='once',
                )
            else:
                coupon = stripe.Coupon.create(
                    amount_off=int(discount.value * 100),
                    currency=order.currency,
                    duration='once',
                )

            discounts.append({'coupon': coupon.id})

        return discounts
