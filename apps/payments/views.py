from django.conf import settings
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Item
from apps.orders.models import Order, OrderItem
from .services.stripe_service import StripeService


def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id, is_active=True)

    return render(
        request,
        'item_detail.html',
        {
            'item': item,
            'stripe_public_key': settings.STRIPE_KEYS[item.currency]['public'],
        },
    )


def buy_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, is_active=True)

    order = Order.objects.create(currency=item.currency)
    OrderItem.objects.create(order=order, item=item, quantity=1)

    session = StripeService.create_checkout_session(order)

    return JsonResponse({'id': session.id})


def success(request):
    return render(request, 'success.html')


def cancel(request):
    return render(request, 'cancel.html')
