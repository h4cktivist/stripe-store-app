from django.conf import settings
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Item
from apps.orders.models import Order, OrderItem
from .services.stripe_service import StripeService
from ..orders.services import get_or_create_order, add_item_to_order


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


def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id, is_active=True)
    order = get_or_create_order(request)

    if order.items.exists():
        if order.currency and order.currency != item.currency:
            return JsonResponse(
                {'error': 'Mixed currencies not allowed'},
                status=400
            )

    order.currency = item.currency
    order.save()

    add_item_to_order(order, item)

    return JsonResponse({
        'order_id': order.id,
        'items_count': order.items.count(),
    })


def cart_detail(request):
    order_id = request.session.get('order_id')

    if not order_id:
        raise Http404("Cart is empty")

    order = Order.objects.prefetch_related(
        'items__item',
        'discounts',
        'taxes',
    ).filter(
        id=order_id,
        status=Order.Status.DRAFT,
    ).first()

    if not order or not order.items.exists():
        raise Http404("Cart is empty")

    return render(
        request,
        'cart_detail.html',
        {
            'order': order,
            'stripe_public_key': settings.STRIPE_KEYS[order.currency]['public'],
        },
    )


def checkout(request):
    order = Order.objects.filter(
        id=request.session.get('order_id'),
        status=Order.Status.DRAFT,
    ).first()

    if not order:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    session = StripeService.create_checkout_session(order)

    return JsonResponse({'id': session.id})


def success(request):
    return render(request, 'success.html')


def cancel(request):
    return render(request, 'cancel.html')
